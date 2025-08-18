#!/usr/bin/env python3

import logging
import subprocess
import time
from datetime import datetime


# GPIO pins to monitor
PINS = [2, 3, 4, 10]

# Log file path
LOG_FILE = "/home/doorpi/gpio_monitor.log"


class MillisecondFormatter(logging.Formatter):
    """Custom formatter to include milliseconds in timestamp."""

    def formatTime(self, record, datefmt=None):  # noqa: ARG002, N802
        """Override formatTime to include milliseconds."""
        ct = datetime.fromtimestamp(record.created)
        return ct.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Remove last 3 digits to get milliseconds


def setup_logger():
    logger = logging.getLogger("GPIO_Monitor")
    logger.setLevel(logging.INFO)

    # Log format with millisecond precision
    formatter = MillisecondFormatter("%(asctime)s | %(message)s")

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def read_gpio(pin):
    """Uses 'raspi-gpio get <pin>' to read the pin status.

    Returns 0 or 1 depending on the detected logic level.
    """
    try:
        output = subprocess.check_output(["/usr/bin/raspi-gpio", "get", str(pin)], text=True)  # noqa: S603
        # Example output: "GPIO 2: level=1 fsel=1 func=OUTPUT pull=DOWN"
        if "level=1" in output:
            return 1
        if "level=0" in output:
            return 0

        return None

    except subprocess.CalledProcessError:
        return None

    else:
        return None




def main():
    logger = setup_logger()
    logger.info("===== STARTING GPIO MONITORING =====")

    previous_states = {}

    try:
        while True:
            current_states = {}
            changed = False

            for pin in PINS:
                value = read_gpio(pin)
                current_states[pin] = value

                if previous_states.get(pin) != value:
                    changed = True

            if changed:
                states_str = " | ".join(
                    f"GPIO{pin}={current_states[pin] if current_states[pin] is not None else 'ERR'}"
                    for pin in PINS
                )
                logger.info(states_str)
                previous_states = current_states

            time.sleep(0.5)  # half a second between reads

    except KeyboardInterrupt:
        logger.info("===== GPIO MONITORING STOPPED =====")


if __name__ == "__main__":
    main()
