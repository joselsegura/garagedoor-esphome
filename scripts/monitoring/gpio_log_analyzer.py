#!/usr/bin/env python3
"""
GPIO Log File Analyzer

This tool analyzes GPIO log files to check consistency between consecutive
log entries. Each log line starts with a timestamp followed by '|' and 
contains GPIO status information.

Log format:
- First line: Header (e.g., "===== STARTING GPIO MONITORING =====")
- Last line: Footer (e.g., "===== GPIO MONITORING STOPPED =====")
- Data lines: timestamp | GPIO2=1 | GPIO3=1 | GPIO4=1 | GPIO10=1
- Timestamp format: YYYY-MM-DD HH:MM:SS.fff (with millisecond precision)

The tool validates consistency rules between consecutive GPIO states.
"""

import re
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gpio_log_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GPIOLogEntry:
    """Represents a single GPIO log entry"""
    
    def __init__(self, line_number: int, timestamp_str: str, gpio_states: Dict[str, int]):
        self.line_number = line_number
        self.timestamp_str = timestamp_str
        self.gpio_states = gpio_states
        self.timestamp = None
        
        # Try to parse timestamp
        try:
            # Common timestamp formats (prioritizing the new millisecond format from gpio_monitor.py)
            timestamp_formats = [
                '%Y-%m-%d %H:%M:%S.%f',    # New format with microseconds/milliseconds (YYYY-MM-DD HH:MM:SS.fff)
                '%Y-%m-%d %H:%M:%S',       # Standard format without milliseconds
                '%H:%M:%S.%f',             # Time only with microseconds/milliseconds
                '%H:%M:%S',                # Time only without milliseconds
                '%Y/%m/%d %H:%M:%S.%f',    # Alternative date separator with milliseconds
                '%Y/%m/%d %H:%M:%S',       # Alternative date separator
                '%d/%m/%Y %H:%M:%S.%f',    # European date format with milliseconds
                '%d/%m/%Y %H:%M:%S'        # European date format
            ]
            
            for fmt in timestamp_formats:
                try:
                    self.timestamp = datetime.strptime(timestamp_str.strip(), fmt)
                    # Log successful parsing for millisecond formats (debug level)
                    if '.%f' in fmt:
                        logger.debug(f"Successfully parsed timestamp with precision: {timestamp_str.strip()}")
                    break
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not parse timestamp '{timestamp_str}' on line {line_number}: {e}")
    
    def __str__(self):
        gpio_str = " | ".join([f"GPIO{pin}={state}" for pin, state in sorted(self.gpio_states.items())])
        return f"Line {self.line_number}: {self.timestamp_str} | {gpio_str}"

class GPIOLogAnalyzer:
    """Analyzes GPIO log files for consistency"""
    
    def __init__(self):
        self.log_entries: List[GPIOLogEntry] = []
        self.header_line = None
        self.footer_line = None
        self.inconsistencies = []
        self.gpio_pins = set()
        self.validation_rules = []
        
    def add_validation_rule(self, rule_func, description: str):
        """Add a validation rule function"""
        self.validation_rules.append({
            'function': rule_func,
            'description': description
        })
    
    def parse_log_file(self, filename: str) -> bool:
        """Parse the GPIO log file"""
        logger.info(f"📁 Parsing log file: {filename}")
        
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
        except FileNotFoundError:
            logger.error(f"❌ File not found: {filename}")
            return False
        except Exception as e:
            logger.error(f"❌ Error reading file {filename}: {e}")
            return False
        
        if not lines:
            logger.error("❌ Log file is empty")
            return False
        
        # Parse header (first line)
        first_line = lines[0].strip()
        if "=====" in first_line and "STARTING" in first_line.upper():
            self.header_line = first_line
            logger.info(f"✅ Found header: {first_line}")
        else:
            logger.warning(f"⚠️  First line doesn't match expected header format: {first_line}")
            self.header_line = first_line
        
        # Parse footer (last line)
        if len(lines) > 1:
            last_line = lines[-1].strip()
            if "=====" in last_line and ("STOPPED" in last_line.upper() or "ENDING" in last_line.upper()):
                self.footer_line = last_line
                logger.info(f"✅ Found footer: {last_line}")
            else:
                logger.warning(f"⚠️  Last line doesn't match expected footer format: {last_line}")
                self.footer_line = last_line
        
        # Parse data lines (everything between header and footer)
        data_lines = lines[1:-1] if len(lines) > 2 else []
        
        logger.info(f"📊 Processing {len(data_lines)} data lines...")
        
        for line_num, line in enumerate(data_lines, start=2):  # Start from line 2
            line = line.strip()
            if not line:
                continue
                
            entry = self._parse_log_line(line_num, line)
            if entry:
                self.log_entries.append(entry)
                self.gpio_pins.update(entry.gpio_states.keys())
        
        logger.info(f"✅ Parsed {len(self.log_entries)} GPIO log entries")
        logger.info(f"📌 Detected GPIO pins: {sorted(self.gpio_pins)}")
        
        return len(self.log_entries) > 0
    
    def validate_initial_state(self) -> bool:
        """Validate that all GPIO values are 1 in the initial state"""
        if not self.log_entries:
            logger.warning("⚠️  No log entries to validate initial state")
            return True
        
        first_entry = self.log_entries[0]
        logger.info(f"🔍 Validating initial state (line {first_entry.line_number})...")
        
        invalid_pins = []
        for pin, state in first_entry.gpio_states.items():
            if state != 1:
                invalid_pins.append(f"GPIO{pin}={state}")
        
        if invalid_pins:
            issue = {
                'type': 'invalid_initial_state',
                'line_numbers': (first_entry.line_number,),
                'description': f"Initial state violation: All GPIO values should be 1",
                'details': {
                    'invalid_pins': invalid_pins,
                    'expected': "All GPIO values = 1",
                    'actual': dict(first_entry.gpio_states)
                }
            }
            self.inconsistencies.append(issue)
            logger.error(f"❌ Initial state violation on line {first_entry.line_number}")
            logger.error(f"    Invalid pins: {', '.join(invalid_pins)}")
            return False
        else:
            logger.info(f"✅ Initial state is valid - all GPIO values are 1")
            return True
    
    def validate_gpio4_transitions(self) -> bool:
        """Validate GPIO4 transitions: should go 1->0->1 with 1-2 second timing"""
        if len(self.log_entries) < 3:
            logger.warning("⚠️  Need at least 3 entries to validate GPIO4 transitions")
            return True
        
        logger.info("🔍 Validating GPIO4 transition patterns...")
        
        gpio4_transitions = []
        transition_issues = []
        
        # Find all GPIO4 state changes
        for i, entry in enumerate(self.log_entries):
            if '4' in entry.gpio_states:
                gpio4_state = entry.gpio_states['4']
                gpio4_transitions.append((i, entry.line_number, gpio4_state, entry.timestamp, entry.timestamp_str))
        
        if not gpio4_transitions:
            logger.warning("⚠️  No GPIO4 states found in log entries")
            return True
        
        # Analyze transition patterns
        for i in range(len(gpio4_transitions) - 2):
            curr_idx, curr_line, curr_state, curr_time, curr_time_str = gpio4_transitions[i]
            next_idx, next_line, next_state, next_time, next_time_str = gpio4_transitions[i + 1]
            third_idx, third_line, third_state, third_time, third_time_str = gpio4_transitions[i + 2]
            
            # Check for 1->0->1 pattern
            if curr_state == 1 and next_state == 0 and third_state == 1:
                # Check timing if timestamps are available
                if curr_time and next_time and third_time:
                    time_to_0 = (next_time - curr_time).total_seconds()
                    time_to_1 = (third_time - next_time).total_seconds()
                    total_time = (third_time - curr_time).total_seconds()
                    
                    logger.info(f"✅ Found GPIO4 transition 1->0->1 (lines {curr_line}->{next_line}->{third_line})")
                    logger.info(f"    Timing: {time_to_0:.3f}s to 0, {time_to_1:.3f}s back to 1, total: {total_time:.3f}s")
                    
                    # Validate timing: GPIO4 should be 0 for 1-2 seconds
                    if time_to_1 < 1.0 or time_to_1 > 2.0:
                        issue = {
                            'type': 'gpio4_timing_violation',
                            'line_numbers': (curr_line, next_line, third_line),
                            'description': f"GPIO4 timing violation: should be 0 for 1-2 seconds",
                            'details': {
                                'pattern': '1->0->1',
                                'time_at_0': f"{time_to_1:.3f}s",
                                'expected_range': '1.0-2.0 seconds',
                                'valid_timing': False
                            }
                        }
                        transition_issues.append(issue)
                        logger.warning(f"⚠️  GPIO4 timing violation (lines {curr_line}->{next_line}->{third_line}): {time_to_1:.3f}s at 0")
                else:
                    logger.info(f"✅ Found GPIO4 transition 1->0->1 (lines {curr_line}->{next_line}->{third_line}) - timing not validated (no timestamps)")
            
            # Check for invalid patterns
            elif curr_state == 0 and next_state == 0:
                # GPIO4 staying at 0 for too long might be an issue
                if curr_time and next_time:
                    time_diff = (next_time - curr_time).total_seconds()
                    if time_diff > 2.0:
                        issue = {
                            'type': 'gpio4_stuck_at_0',
                            'line_numbers': (curr_line, next_line),
                            'description': f"GPIO4 stuck at 0 for too long",
                            'details': {
                                'duration': f"{time_diff:.3f}s",
                                'expected_max': '2.0 seconds'
                            }
                        }
                        transition_issues.append(issue)
                        logger.warning(f"⚠️  GPIO4 stuck at 0 for {time_diff:.3f}s (lines {curr_line}->{next_line})")
        
        # Add all issues to the main inconsistencies list
        self.inconsistencies.extend(transition_issues)
        
        if not transition_issues:
            logger.info("✅ All GPIO4 transitions are valid")
            return True
        else:
            logger.warning(f"⚠️  Found {len(transition_issues)} GPIO4 transition issues")
            return False
    
    def validate_gpio3_transitions(self) -> bool:
        """Validate GPIO3 transitions: should go 1->0->1 with 15-20 second timing, after GPIO4 returns to 1"""
        if len(self.log_entries) < 5:
            logger.warning("⚠️  Need at least 5 entries to validate GPIO3 transitions")
            return True
        
        logger.info("🔍 Validating GPIO3 transition patterns...")
        
        transition_issues = []
        
        # Find GPIO4 1->0->1 transitions first, then check for GPIO3 transitions
        for i in range(len(self.log_entries) - 4):
            # Look for GPIO4 pattern: 1->0->1
            entries = self.log_entries[i:i+5]  # Look at 5 consecutive entries
            
            if (len(entries) >= 3 and 
                '4' in entries[0].gpio_states and '4' in entries[1].gpio_states and '4' in entries[2].gpio_states and
                '3' in entries[0].gpio_states and '3' in entries[1].gpio_states and '3' in entries[2].gpio_states):
                
                gpio4_states = [entries[j].gpio_states['4'] for j in range(3)]
                gpio3_states = [entries[j].gpio_states['3'] for j in range(min(5, len(entries)))]
                
                # Check if we have GPIO4 pattern 1->0->1
                if gpio4_states == [1, 0, 1]:
                    logger.info(f"📍 Found GPIO4 transition 1->0->1 at lines {entries[0].line_number}-{entries[2].line_number}")
                    
                    # Now look for GPIO3 transition after GPIO4 returns to 1
                    # GPIO3 should go 0 approximately 2 seconds after GPIO4 returns to 1
                    gpio4_return_entry = entries[2]  # When GPIO4 returns to 1
                    
                    # Look for GPIO3 going to 0 in subsequent entries
                    gpio3_goes_0_entry = None
                    gpio3_returns_1_entry = None
                    
                    for j in range(2, min(len(entries), len(self.log_entries) - i)):
                        if j < len(entries) and '3' in entries[j].gpio_states:
                            if entries[j].gpio_states['3'] == 0 and gpio3_goes_0_entry is None:
                                gpio3_goes_0_entry = entries[j]
                            elif (entries[j].gpio_states['3'] == 1 and gpio3_goes_0_entry is not None and 
                                  gpio3_returns_1_entry is None):
                                gpio3_returns_1_entry = entries[j]
                                break
                    
                    # Validate GPIO3 transition if found
                    if gpio3_goes_0_entry and gpio3_returns_1_entry:
                        logger.info(f"✅ Found GPIO3 transition 1->0->1 (lines {gpio3_goes_0_entry.line_number}->{gpio3_returns_1_entry.line_number})")
                        
                        # Check timing if timestamps are available
                        if (gpio4_return_entry.timestamp and gpio3_goes_0_entry.timestamp and 
                            gpio3_returns_1_entry.timestamp):
                            
                            # Time from GPIO4 return to GPIO3 going 0 (should be ~2 seconds)
                            delay_to_gpio3_0 = (gpio3_goes_0_entry.timestamp - gpio4_return_entry.timestamp).total_seconds()
                            
                            # Time GPIO3 stays at 0 (should be 15-20 seconds)
                            gpio3_duration_at_0 = (gpio3_returns_1_entry.timestamp - gpio3_goes_0_entry.timestamp).total_seconds()
                            
                            logger.info(f"    Timing: {delay_to_gpio3_0:.3f}s delay after GPIO4, {gpio3_duration_at_0:.3f}s at 0")
                            
                            # Validate delay (should be around 2 seconds, allow some tolerance)
                            if delay_to_gpio3_0 < 1.0 or delay_to_gpio3_0 > 4.0:
                                issue = {
                                    'type': 'gpio3_delay_violation',
                                    'line_numbers': (gpio4_return_entry.line_number, gpio3_goes_0_entry.line_number),
                                    'description': f"GPIO3 delay violation: should go 0 approximately 2s after GPIO4 returns to 1",
                                    'details': {
                                        'actual_delay': f"{delay_to_gpio3_0:.3f}s",
                                        'expected_delay': '~2.0 seconds (1-4s tolerance)',
                                        'valid_timing': False
                                    }
                                }
                                transition_issues.append(issue)
                                logger.warning(f"⚠️  GPIO3 delay violation: {delay_to_gpio3_0:.3f}s delay (expected ~2s)")
                            
                            # Validate duration at 0 (should be 15-20 seconds)
                            if gpio3_duration_at_0 < 15.0 or gpio3_duration_at_0 > 20.0:
                                issue = {
                                    'type': 'gpio3_timing_violation',
                                    'line_numbers': (gpio3_goes_0_entry.line_number, gpio3_returns_1_entry.line_number),
                                    'description': f"GPIO3 timing violation: should be 0 for 15-20 seconds",
                                    'details': {
                                        'time_at_0': f"{gpio3_duration_at_0:.3f}s",
                                        'expected_range': '15.0-20.0 seconds',
                                        'valid_timing': False
                                    }
                                }
                                transition_issues.append(issue)
                                logger.warning(f"⚠️  GPIO3 timing violation: {gpio3_duration_at_0:.3f}s at 0 (expected 15-20s)")
                            else:
                                logger.info(f"✅ GPIO3 timing valid: {gpio3_duration_at_0:.3f}s at 0")
                        else:
                            logger.info(f"✅ Found GPIO3 transition pattern - timing not validated (no timestamps)")
                    else:
                        # GPIO4 returned to 1 but no corresponding GPIO3 transition found
                        issue = {
                            'type': 'missing_gpio3_transition',
                            'line_numbers': (gpio4_return_entry.line_number,),
                            'description': f"Missing GPIO3 transition: GPIO4 returned to 1 but GPIO3 didn't follow expected pattern",
                            'details': {
                                'gpio4_return_line': gpio4_return_entry.line_number,
                                'expected': 'GPIO3 should go 1->0->1 after GPIO4 returns to 1'
                            }
                        }
                        transition_issues.append(issue)
                        logger.warning(f"⚠️  Missing GPIO3 transition after GPIO4 return at line {gpio4_return_entry.line_number}")
        
        # Add all issues to the main inconsistencies list
        self.inconsistencies.extend(transition_issues)
        
        if not transition_issues:
            logger.info("✅ All GPIO3 transitions are valid")
            return True
        else:
            logger.warning(f"⚠️  Found {len(transition_issues)} GPIO3 transition issues")
            return False
    
    def validate_gpio10_transitions(self) -> bool:
        """Validate GPIO10 transitions: should return to 1 within 4 seconds maximum when it goes to 0"""
        if len(self.log_entries) < 2:
            logger.warning("⚠️  Need at least 2 entries to validate GPIO10 transitions")
            return True
        
        logger.info("🔍 Validating GPIO10 transition patterns...")
        
        gpio10_transitions = []
        transition_issues = []
        
        # Find all GPIO10 state changes
        for i, entry in enumerate(self.log_entries):
            if '10' in entry.gpio_states:
                gpio10_state = entry.gpio_states['10']
                gpio10_transitions.append((i, entry.line_number, gpio10_state, entry.timestamp, entry.timestamp_str))
        
        if not gpio10_transitions:
            logger.warning("⚠️  No GPIO10 states found in log entries")
            return True
        
        # Analyze GPIO10 transitions for 1->0->1 patterns
        for i in range(len(gpio10_transitions) - 1):
            curr_idx, curr_line, curr_state, curr_time, curr_time_str = gpio10_transitions[i]
            next_idx, next_line, next_state, next_time, next_time_str = gpio10_transitions[i + 1]
            
            # Check for transition to 0
            if curr_state == 1 and next_state == 0:
                logger.info(f"📍 Found GPIO10 transition 1->0 at lines {curr_line}->{next_line}")
                
                # Look for return to 1
                return_to_1_found = False
                for j in range(i + 2, len(gpio10_transitions)):
                    ret_idx, ret_line, ret_state, ret_time, ret_time_str = gpio10_transitions[j]
                    
                    if ret_state == 1:
                        # Found return to 1
                        return_to_1_found = True
                        logger.info(f"✅ Found GPIO10 return to 1 at line {ret_line}")
                        
                        # Check timing if timestamps are available
                        if next_time and ret_time:
                            duration_at_0 = (ret_time - next_time).total_seconds()
                            logger.info(f"    Timing: GPIO10 was at 0 for {duration_at_0:.3f}s")
                            
                            # Validate timing: GPIO10 should return to 1 within 4 seconds maximum
                            if duration_at_0 > 4.0:
                                issue = {
                                    'type': 'gpio10_timing_violation',
                                    'line_numbers': (next_line, ret_line),
                                    'description': f"GPIO10 timing violation: took too long to return to 1",
                                    'details': {
                                        'time_at_0': f"{duration_at_0:.3f}s",
                                        'expected_max': '4.0 seconds',
                                        'valid_timing': False
                                    }
                                }
                                transition_issues.append(issue)
                                logger.warning(f"⚠️  GPIO10 timing violation: {duration_at_0:.3f}s at 0 (max 4.0s)")
                            else:
                                logger.info(f"✅ GPIO10 timing valid: {duration_at_0:.3f}s at 0 (within 4.0s limit)")
                        else:
                            logger.info(f"✅ Found GPIO10 return to 1 - timing not validated (no timestamps)")
                        break
                    elif ret_state == 0:
                        # Still at 0, continue looking
                        continue
                
                # If we didn't find a return to 1, that might be an issue
                if not return_to_1_found:
                    # Check if this is the last transition or if there are more entries to check
                    if i + 2 >= len(gpio10_transitions):
                        logger.warning(f"⚠️  GPIO10 went to 0 at line {next_line} but no return to 1 found in remaining log")
                        issue = {
                            'type': 'gpio10_no_return',
                            'line_numbers': (next_line,),
                            'description': f"GPIO10 went to 0 but never returned to 1",
                            'details': {
                                'transition_line': next_line,
                                'expected': 'GPIO10 should return to 1 within 4 seconds maximum'
                            }
                        }
                        transition_issues.append(issue)
        
        # Also check for GPIO10 staying at 0 too long between any consecutive 0 states
        for i in range(len(gpio10_transitions) - 1):
            curr_idx, curr_line, curr_state, curr_time, curr_time_str = gpio10_transitions[i]
            next_idx, next_line, next_state, next_time, next_time_str = gpio10_transitions[i + 1]
            
            # If both states are 0 and we have timestamps, check duration
            if curr_state == 0 and next_state == 0 and curr_time and next_time:
                duration_between = (next_time - curr_time).total_seconds()
                
                # If there's more than 4 seconds between consecutive 0 states, that's a violation
                if duration_between > 4.0:
                    issue = {
                        'type': 'gpio10_stuck_at_0',
                        'line_numbers': (curr_line, next_line),
                        'description': f"GPIO10 stuck at 0 for too long",
                        'details': {
                            'duration': f"{duration_between:.3f}s",
                            'expected_max': '4.0 seconds'
                        }
                    }
                    transition_issues.append(issue)
                    logger.warning(f"⚠️  GPIO10 stuck at 0 for {duration_between:.3f}s (lines {curr_line}->{next_line})")
        
        # Add all issues to the main inconsistencies list
        self.inconsistencies.extend(transition_issues)
        
        if not transition_issues:
            logger.info("✅ All GPIO10 transitions are valid")
            return True
        else:
            logger.warning(f"⚠️  Found {len(transition_issues)} GPIO10 transition issues")
            return False
    
    def validate_gpio2_transitions(self) -> bool:
        """Validate GPIO2 transitions: should return to 1 within 25 seconds maximum when it goes to 0"""
        if len(self.log_entries) < 2:
            logger.warning("⚠️  Need at least 2 entries to validate GPIO2 transitions")
            return True
        
        logger.info("🔍 Validating GPIO2 transition patterns...")
        
        gpio2_transitions = []
        transition_issues = []
        
        # Find all GPIO2 state changes
        for i, entry in enumerate(self.log_entries):
            if '2' in entry.gpio_states:
                gpio2_state = entry.gpio_states['2']
                gpio2_transitions.append((i, entry.line_number, gpio2_state, entry.timestamp, entry.timestamp_str))
        
        if not gpio2_transitions:
            logger.warning("⚠️  No GPIO2 states found in log entries")
            return True
        
        # Analyze GPIO2 transitions for 1->0->1 patterns
        for i in range(len(gpio2_transitions) - 1):
            curr_idx, curr_line, curr_state, curr_time, curr_time_str = gpio2_transitions[i]
            next_idx, next_line, next_state, next_time, next_time_str = gpio2_transitions[i + 1]
            
            # Check for transition to 0
            if curr_state == 1 and next_state == 0:
                logger.info(f"📍 Found GPIO2 transition 1->0 at lines {curr_line}->{next_line}")
                
                # Look for return to 1
                return_to_1_found = False
                for j in range(i + 2, len(gpio2_transitions)):
                    ret_idx, ret_line, ret_state, ret_time, ret_time_str = gpio2_transitions[j]
                    
                    if ret_state == 1:
                        # Found return to 1
                        return_to_1_found = True
                        logger.info(f"✅ Found GPIO2 return to 1 at line {ret_line}")
                        
                        # Check timing if timestamps are available
                        if next_time and ret_time:
                            duration_at_0 = (ret_time - next_time).total_seconds()
                            logger.info(f"    Timing: GPIO2 was at 0 for {duration_at_0:.3f}s")
                            
                            # Validate timing: GPIO2 should return to 1 within 25 seconds
                            if duration_at_0 > 25.0:
                                issue = {
                                    'type': 'gpio2_timing_violation',
                                    'line_numbers': (next_line, ret_line),
                                    'description': f"GPIO2 timing violation: took too long to return to 1",
                                    'details': {
                                        'time_at_0': f"{duration_at_0:.3f}s",
                                        'expected_max': '25.0 seconds',
                                        'valid_timing': False
                                    }
                                }
                                transition_issues.append(issue)
                                logger.warning(f"⚠️  GPIO2 timing violation: {duration_at_0:.3f}s at 0 (max 25.0s)")
                            else:
                                logger.info(f"✅ GPIO2 timing valid: {duration_at_0:.3f}s at 0 (within 25.0s limit)")
                        else:
                            logger.info(f"✅ Found GPIO2 return to 1 - timing not validated (no timestamps)")
                        break
                    elif ret_state == 0:
                        # Still at 0, continue looking
                        continue
                
                # If we didn't find a return to 1, that might be an issue
                if not return_to_1_found:
                    # Check if this is the last transition or if there are more entries to check
                    if i + 2 >= len(gpio2_transitions):
                        logger.warning(f"⚠️  GPIO2 went to 0 at line {next_line} but no return to 1 found in remaining log")
                        issue = {
                            'type': 'gpio2_no_return',
                            'line_numbers': (next_line,),
                            'description': f"GPIO2 went to 0 but never returned to 1",
                            'details': {
                                'transition_line': next_line,
                                'expected': 'GPIO2 should return to 1 within 25 seconds'
                            }
                        }
                        transition_issues.append(issue)
        
        # Also check for GPIO2 staying at 0 too long between any consecutive 0 states
        for i in range(len(gpio2_transitions) - 1):
            curr_idx, curr_line, curr_state, curr_time, curr_time_str = gpio2_transitions[i]
            next_idx, next_line, next_state, next_time, next_time_str = gpio2_transitions[i + 1]
            
            # If both states are 0 and we have timestamps, check duration
            if curr_state == 0 and next_state == 0 and curr_time and next_time:
                duration_between = (next_time - curr_time).total_seconds()
                
                # If there's more than 25 seconds between consecutive 0 states, that's a violation
                if duration_between > 25.0:
                    issue = {
                        'type': 'gpio2_stuck_at_0',
                        'line_numbers': (curr_line, next_line),
                        'description': f"GPIO2 stuck at 0 for too long",
                        'details': {
                            'duration': f"{duration_between:.3f}s",
                            'expected_max': '25.0 seconds'
                        }
                    }
                    transition_issues.append(issue)
                    logger.warning(f"⚠️  GPIO2 stuck at 0 for {duration_between:.3f}s (lines {curr_line}->{next_line})")
        
        # Add all issues to the main inconsistencies list
        self.inconsistencies.extend(transition_issues)
        
        if not transition_issues:
            logger.info("✅ All GPIO2 transitions are valid")
            return True
        else:
            logger.warning(f"⚠️  Found {len(transition_issues)} GPIO2 transition issues")
            return False
    
    def _parse_log_line(self, line_number: int, line: str) -> Optional[GPIOLogEntry]:
        """Parse a single log line"""
        # Expected format: YYYY-MM-DD HH:MM:SS.fff | GPIO2=1 | GPIO3=1 | GPIO4=1 | GPIO10=1
        
        if '|' not in line:
            logger.warning(f"⚠️  Line {line_number}: No '|' separator found")
            return None
        
        parts = line.split('|')
        if len(parts) < 2:
            logger.warning(f"⚠️  Line {line_number}: Invalid format - not enough parts")
            return None
        
        timestamp_str = parts[0].strip()
        gpio_parts = parts[1:]
        
        # Parse GPIO states
        gpio_states = {}
        gpio_pattern = re.compile(r'GPIO(\d+)=(\d+)')
        
        for part in gpio_parts:
            part = part.strip()
            match = gpio_pattern.match(part)
            if match:
                pin = match.group(1)
                state = int(match.group(2))
                gpio_states[pin] = state
            else:
                if part:  # Only warn if part is not empty
                    logger.warning(f"⚠️  Line {line_number}: Could not parse GPIO part: '{part}'")
        
        if not gpio_states:
            logger.warning(f"⚠️  Line {line_number}: No GPIO states found")
            return None
        
        return GPIOLogEntry(line_number, timestamp_str, gpio_states)
    
    def check_consistency(self) -> bool:
        """Check consistency between consecutive log entries and validate initial state"""
        logger.info("🔍 Checking GPIO log consistency...")
        
        # First, validate initial state
        initial_state_valid = self.validate_initial_state()
        
        # Then, validate GPIO4 transitions
        gpio4_transitions_valid = self.validate_gpio4_transitions()
        
        # Validate GPIO3 transitions
        gpio3_transitions_valid = self.validate_gpio3_transitions()
        
        # Validate GPIO10 transitions
        gpio10_transitions_valid = self.validate_gpio10_transitions()
        
        # Validate GPIO2 transitions
        gpio2_transitions_valid = self.validate_gpio2_transitions()
        
        if len(self.log_entries) < 2:
            logger.warning("⚠️  Need at least 2 entries to check consecutive consistency")
            return (initial_state_valid and gpio4_transitions_valid and gpio3_transitions_valid and 
                   gpio10_transitions_valid and gpio2_transitions_valid)
        
        logger.info("🔍 Checking consistency between consecutive entries...")
        inconsistency_count = 0
        
        for i in range(1, len(self.log_entries)):
            prev_entry = self.log_entries[i-1]
            curr_entry = self.log_entries[i]
            
            # Check if all GPIO pins are present in both entries
            prev_pins = set(prev_entry.gpio_states.keys())
            curr_pins = set(curr_entry.gpio_states.keys())
            
            if prev_pins != curr_pins:
                missing_in_curr = prev_pins - curr_pins
                missing_in_prev = curr_pins - prev_pins
                
                issue = {
                    'type': 'missing_gpio_pins',
                    'line_numbers': (prev_entry.line_number, curr_entry.line_number),
                    'description': f"GPIO pin mismatch between lines {prev_entry.line_number} and {curr_entry.line_number}",
                    'details': {
                        'missing_in_current': list(missing_in_curr),
                        'missing_in_previous': list(missing_in_prev)
                    }
                }
                self.inconsistencies.append(issue)
                inconsistency_count += 1
                logger.warning(f"⚠️  {issue['description']}")
                if missing_in_curr:
                    logger.warning(f"    Missing in current: GPIO{', GPIO'.join(missing_in_curr)}")
                if missing_in_prev:
                    logger.warning(f"    Missing in previous: GPIO{', GPIO'.join(missing_in_prev)}")
            
            # Apply custom validation rules
            for rule in self.validation_rules:
                try:
                    rule_result = rule['function'](prev_entry, curr_entry)
                    if not rule_result.get('valid', True):
                        issue = {
                            'type': 'rule_violation',
                            'line_numbers': (prev_entry.line_number, curr_entry.line_number),
                            'description': f"Rule violation: {rule['description']}",
                            'details': rule_result
                        }
                        self.inconsistencies.append(issue)
                        inconsistency_count += 1
                        logger.warning(f"⚠️  {issue['description']} (lines {prev_entry.line_number}-{curr_entry.line_number})")
                except Exception as e:
                    logger.error(f"❌ Error applying rule '{rule['description']}': {e}")
        
        consecutive_consistent = inconsistency_count == 0
        if consecutive_consistent:
            logger.info("✅ All consecutive entries are consistent")
        else:
            logger.warning(f"⚠️  Found {inconsistency_count} consecutive inconsistencies")
        
        # Return True only if all validations pass
        overall_valid = (initial_state_valid and gpio4_transitions_valid and gpio3_transitions_valid and 
                        gpio10_transitions_valid and gpio2_transitions_valid and consecutive_consistent)
        if overall_valid:
            logger.info("✅ GPIO log analysis passed all validation checks")
        else:
            logger.warning("⚠️  GPIO log analysis found validation issues")
        
        return overall_valid
    
    def generate_report(self) -> str:
        """Generate analysis report"""
        report = []
        report.append("=" * 80)
        report.append("GPIO LOG FILE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  Total log entries: {len(self.log_entries)}")
        report.append(f"  GPIO pins detected: {sorted(self.gpio_pins)}")
        report.append(f"  Inconsistencies found: {len(self.inconsistencies)}")
        report.append(f"  Header: {self.header_line}")
        report.append(f"  Footer: {self.footer_line}")
        report.append("")
        
        # Validation rules applied
        report.append("VALIDATION RULES APPLIED:")
        report.append("  1. Initial state: All GPIO values should be 1")
        report.append("  2. GPIO4 transitions: Should go 1->0->1 with 1-2 second timing")
        report.append("  3. GPIO3 transitions: Should go 1->0->1 with 15-20 second timing, after GPIO4 returns to 1")
        report.append("  4. GPIO10 transitions: Should return to 1 within 4 seconds maximum when it goes to 0")
        report.append("  5. GPIO2 transitions: Should return to 1 within 25 seconds maximum when it goes to 0")
        report.append("  6. GPIO pin consistency: All pins should be present in each entry")
        report.append("  Note: Timing validation uses millisecond precision when available")
        if self.validation_rules:
            for i, rule in enumerate(self.validation_rules, start=7):
                report.append(f"  {i}. Custom rule: {rule['description']}")
        report.append("")
        
        # Time range
        if self.log_entries:
            first_entry = self.log_entries[0]
            last_entry = self.log_entries[-1]
            report.append("TIME RANGE:")
            report.append(f"  First entry: Line {first_entry.line_number} - {first_entry.timestamp_str}")
            report.append(f"  Last entry:  Line {last_entry.line_number} - {last_entry.timestamp_str}")
            report.append("")
        
        # Inconsistencies
        if self.inconsistencies:
            report.append("INCONSISTENCIES FOUND:")
            for i, issue in enumerate(self.inconsistencies, 1):
                report.append(f"  {i}. {issue['description']}")
                if 'details' in issue:
                    for key, value in issue['details'].items():
                        if key not in ['valid']:
                            report.append(f"     {key}: {value}")
                report.append("")
        else:
            report.append("✅ NO INCONSISTENCIES FOUND")
            report.append("")
        
        # GPIO state summary
        if self.log_entries:
            report.append("GPIO STATE SUMMARY:")
            for pin in sorted(self.gpio_pins):
                states = [entry.gpio_states.get(pin, -1) for entry in self.log_entries]
                unique_states = set(states)
                report.append(f"  GPIO{pin}: States used: {sorted(unique_states)}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "gpio_analysis_report.txt"):
        """Save analysis report to file"""
        report = self.generate_report()
        try:
            with open(filename, 'w') as f:
                f.write(report)
            logger.info(f"📄 Analysis report saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")

def main():
    parser = argparse.ArgumentParser(description='GPIO Log File Analyzer - Check consistency in GPIO state logs')
    parser.add_argument('logfile', help='Path to the GPIO log file to analyze')
    parser.add_argument('--output', '-o', help='Output file for analysis report (default: gpio_analysis_report.txt)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create analyzer
    analyzer = GPIOLogAnalyzer()
    
    try:
        # Parse log file
        if not analyzer.parse_log_file(args.logfile):
            logger.error("❌ Failed to parse log file")
            sys.exit(1)
        
        # Check consistency
        analyzer.check_consistency()
        
        # Generate and display report
        report = analyzer.generate_report()
        print(report)
        
        # Save report
        output_file = args.output or "gpio_analysis_report.txt"
        analyzer.save_report(output_file)
        
        # Exit with appropriate code
        if analyzer.inconsistencies:
            logger.info(f"⚠️  Analysis completed with {len(analyzer.inconsistencies)} inconsistencies found")
            sys.exit(1)
        else:
            logger.info("✅ Analysis completed successfully - no inconsistencies found")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
