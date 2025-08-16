#!/usr/bin/env python3
"""GPIO Safeguard System

This program monitors GPIO pins and actively enforces safety rules to prevent
dangerous states that could damage equipment or cause malfunctions.

Based on gpio_monitor.py but with active protection capabilities.

Safety Rules:
- GPIO4: If set to 0, must return to 1 within 2 seconds maximum
- GPIO3: If set to 0, must return to 1 within 20 seconds maximum
- GPIO10: If set to 0, must return to 1 within 4 seconds maximum
- GPIO2: If set to 0, must return to 1 within 25 seconds maximum
- All GPIOs: Should start and default to 1 (safe state)
"""

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from typing import Optional


# GPIO pins to monitor and protect
MONITORED_PINS = [2, 3, 4, 10]

# Safety timing rules (in seconds)
SAFETY_RULES = {
    2: 25.0,  # GPIO2: max 25 seconds at 0
    3: 20.0,  # GPIO3: max 20 seconds at 0
    4: 2.0,  # GPIO4: max 2 seconds at 0
    10: 4.0,  # GPIO10: max 4 seconds at 0
}

# Log file path
LOG_FILE = "/home/doorpi/gpio_safeguard.log"


class MillisecondFormatter(logging.Formatter):
    """Custom formatter to include milliseconds in timestamp"""

    def formatTime(self, record, datefmt=None):
        """Override formatTime to include milliseconds"""
        ct = datetime.fromtimestamp(record.created)
        return ct.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Remove last 3 digits to get milliseconds


class GPIOSafeguard:
    """GPIO monitoring and protection system"""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.logger = self.setup_logger()
        self.gpio_states = {}
        self.gpio_timers = {}  # Track when GPIOs went to 0
        self.violations_count = 0
        self.corrections_made = 0

    def setup_logger(self):
        """Setup logging with millisecond precision"""
        logger = logging.getLogger("GPIO_Safeguard")
        logger.setLevel(logging.INFO)

        # Clear any existing handlers
        logger.handlers = []

        # Log format with millisecond precision
        formatter = MillisecondFormatter("%(asctime)s | %(levelname)s | %(message)s")

        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def read_gpio(self, pin: int) -> Optional[int]:
        """Read GPIO pin state using raspi-gpio command.
        Returns 0, 1, or None if error.
        """
        try:
            output = subprocess.check_output(
                ["raspi-gpio", "get", str(pin)], text=True, stderr=subprocess.DEVNULL
            )
            # Example output: "GPIO 2: level=1 fsel=1 func=OUTPUT pull=DOWN"
            if "level=1" in output:
                return 1
            elif "level=0" in output:
                return 0
            else:
                return None
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to read GPIO{pin}: {e}")
            return None

    def set_gpio(self, pin: int, value: int, max_retries: int = 3) -> bool:
        """Set GPIO pin to specified value (0 or 1) with verification and retries.
        Verifies the change by reading back the pin state.
        Returns True if successful and verified, False otherwise.
        """
        if self.dry_run:
            self.logger.info(f"🔧 DRY-RUN: Would set GPIO{pin} to {value}")
            return True

        for attempt in range(max_retries):
            try:
                # Use raspi-gpio to set the pin
                if value == 1:
                    cmd = ["raspi-gpio", "set", str(pin), "op", "dh"]  # drive high
                else:
                    cmd = ["raspi-gpio", "set", str(pin), "op", "dl"]  # drive low

                subprocess.check_call(cmd, stderr=subprocess.DEVNULL)

                # Verify the change by reading back the pin state
                time.sleep(0.01)  # Brief delay to ensure the change has taken effect
                actual_value = self.read_gpio(pin)

                if actual_value == value:
                    if attempt > 0:
                        self.logger.info(
                            f"🔧 CORRECTED: Set GPIO{pin} to {value} (verified on attempt {attempt + 1})"
                        )
                    else:
                        self.logger.info(f"🔧 CORRECTED: Set GPIO{pin} to {value} (verified)")
                    return True
                elif actual_value is None:
                    self.logger.warning(
                        f"⚠️  Set GPIO{pin} to {value} but could not verify (read failed) - attempt {attempt + 1}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(0.05)  # Wait a bit longer before retry
                        continue
                    return False  # Treat read failure as set failure for safety
                else:
                    self.logger.warning(
                        f"⚠️  Set GPIO{pin} to {value} but read back {actual_value} - attempt {attempt + 1}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(0.05)  # Wait a bit before retry
                        continue
                    else:
                        self.logger.error(
                            f"❌ Set GPIO{pin} to {value} but read back {actual_value} after {max_retries} attempts - GPIO change failed!"
                        )
                        return False

            except subprocess.CalledProcessError as e:
                self.logger.warning(
                    f"⚠️  Failed to set GPIO{pin} to {value} (attempt {attempt + 1}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(0.05)  # Wait before retry
                    continue
                else:
                    self.logger.error(
                        f"❌ Failed to set GPIO{pin} to {value} after {max_retries} attempts"
                    )
                    return False

        return False

    def initialize_gpios(self):
        """Initialize all monitored GPIOs to safe state (1)"""
        self.logger.info("🔄 Initializing GPIOs to safe state...")

        for pin in MONITORED_PINS:
            current_state = self.read_gpio(pin)
            if current_state is None:
                self.logger.error(f"❌ Cannot read GPIO{pin} during initialization")
                continue

            if current_state != 1:
                self.logger.warning(
                    f"⚠️  GPIO{pin} is not in safe state (currently {current_state})"
                )
                if self.set_gpio(pin, 1):
                    self.logger.info(f"✅ GPIO{pin} initialized to safe state (1)")
                else:
                    self.logger.error(f"❌ Failed to initialize GPIO{pin}")
            else:
                self.logger.info(f"✅ GPIO{pin} already in safe state (1)")

            self.gpio_states[pin] = 1  # Assume safe state after initialization
            self.gpio_timers[pin] = None

    def check_safety_violations(self):
        """Check for safety rule violations and take corrective action"""
        current_time = datetime.now()
        violations_detected = False

        for pin in MONITORED_PINS:
            current_state = self.read_gpio(pin)

            if current_state is None:
                continue

            previous_state = self.gpio_states.get(pin)

            # Track state changes
            if previous_state != current_state:
                self.logger.info(f"📊 GPIO{pin}: {previous_state} -> {current_state}")
                self.gpio_states[pin] = current_state

                if current_state == 0:
                    # GPIO went to 0, start timer
                    self.gpio_timers[pin] = current_time
                    self.logger.info(
                        f"⏱️  GPIO{pin} timer started (max {SAFETY_RULES[pin]}s allowed)"
                    )
                elif current_state == 1:
                    # GPIO returned to 1, clear timer
                    if self.gpio_timers[pin] is not None:
                        duration = (current_time - self.gpio_timers[pin]).total_seconds()
                        self.logger.info(
                            f"✅ GPIO{pin} returned to safe state after {duration:.3f}s"
                        )
                    self.gpio_timers[pin] = None

            # Check for safety violations (GPIO at 0 for too long)
            if current_state == 0 and self.gpio_timers[pin] is not None:
                elapsed = (current_time - self.gpio_timers[pin]).total_seconds()
                max_allowed = SAFETY_RULES[pin]

                if elapsed > max_allowed:
                    violations_detected = True
                    self.violations_count += 1

                    self.logger.warning(
                        f"🚨 SAFETY VIOLATION: GPIO{pin} at 0 for {elapsed:.3f}s "
                        f"(max {max_allowed}s) - FORCING TO SAFE STATE"
                    )

                    # Force GPIO back to safe state
                    if self.set_gpio(pin, 1):
                        self.corrections_made += 1
                        self.gpio_states[pin] = 1
                        self.gpio_timers[pin] = None
                        self.logger.warning(
                            f"🛡️  SAFETY: GPIO{pin} forced to safe state (1) - correction verified"
                        )
                    else:
                        self.logger.error(
                            f"❌ CRITICAL: Failed to correct GPIO{pin}! Verification failed - manual intervention may be required!"
                        )
                        # Continue monitoring even if correction failed - maybe it will recover
                        # But don't reset the timer so we keep trying on subsequent checks

        return violations_detected

    def get_status_summary(self) -> str:
        """Get current status summary"""
        status_parts = []
        for pin in MONITORED_PINS:
            state = self.gpio_states.get(pin, "UNKNOWN")
            if state == 0 and self.gpio_timers[pin] is not None:
                elapsed = (datetime.now() - self.gpio_timers[pin]).total_seconds()
                max_allowed = SAFETY_RULES[pin]
                status_parts.append(f"GPIO{pin}={state}({elapsed:.1f}s/{max_allowed}s)")
            else:
                status_parts.append(f"GPIO{pin}={state}")
        return " | ".join(status_parts)

    def run_safeguard(self, status_interval=30):
        """Run the GPIO safeguard system"""
        mode_str = "DRY-RUN MODE" if self.dry_run else "ACTIVE MODE"
        self.logger.info(f"🚀 STARTING GPIO SAFEGUARD SYSTEM - {mode_str}")
        self.logger.info(f"📋 Monitoring pins: {MONITORED_PINS}")
        self.logger.info(f"⚡ Safety rules: {SAFETY_RULES}")
        self.logger.info("=" * 80)

        # Initialize GPIOs to safe state
        if not self.dry_run:
            self.initialize_gpios()
        else:
            # In dry-run mode, just read current states
            for pin in MONITORED_PINS:
                state = self.read_gpio(pin)
                self.gpio_states[pin] = state
                self.gpio_timers[pin] = None
                self.logger.info(f"📊 GPIO{pin} current state: {state}")

        last_status_time = datetime.now()

        try:
            while True:
                # Check for violations and take corrective action
                violations = self.check_safety_violations()

                # Periodic status report
                current_time = datetime.now()
                if (current_time - last_status_time).total_seconds() >= status_interval:
                    status = self.get_status_summary()
                    self.logger.info(
                        f"📊 Status: {status} | Violations: {self.violations_count} | Corrections: {self.corrections_made}"
                    )
                    last_status_time = current_time

                # Sleep between checks (adjust for responsiveness vs CPU usage)
                time.sleep(0.1)  # Check every 100ms for fast response

        except KeyboardInterrupt:
            self.logger.info("\n⏹️  Safeguard system stopped by user")
            self.logger.info("📊 Final statistics:")
            self.logger.info(f"   Total violations detected: {self.violations_count}")
            self.logger.info(f"   Total corrections made: {self.corrections_made}")
            self.logger.info("===== GPIO SAFEGUARD STOPPED =====")


def main():
    parser = argparse.ArgumentParser(description="GPIO Safeguard System - Active GPIO protection")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in simulation mode (no actual GPIO changes)"
    )
    parser.add_argument(
        "--status-interval",
        type=int,
        default=30,
        help="Status report interval in seconds (default: 30)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Create safeguard system
    safeguard = GPIOSafeguard(dry_run=args.dry_run)

    if args.verbose:
        safeguard.logger.setLevel(logging.DEBUG)

    # Verify we can read GPIOs before starting
    gpio_accessible = True
    for pin in MONITORED_PINS:
        if safeguard.read_gpio(pin) is None:
            safeguard.logger.error(f"❌ Cannot access GPIO{pin}")
            gpio_accessible = False

    if not gpio_accessible:
        safeguard.logger.error("❌ GPIO access failed. Check permissions and hardware.")
        sys.exit(1)

    # Run the safeguard system
    try:
        safeguard.run_safeguard(status_interval=args.status_interval)
    except Exception as e:
        safeguard.logger.error(f"❌ Safeguard system failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
