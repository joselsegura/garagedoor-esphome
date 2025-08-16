#!/usr/bin/env python3
"""
Garage Door Cycling Tool

This tool opens both garage doors, waits for them to be fully opened,
then closes them. It repeats this cycle with random wait periods between
iterations (15-30 seconds).

Based on ha_test_runner.py for Home Assistant API communication.
"""

import requests
import json
import time
import sys
import argparse
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('door_cycler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DoorCycler:
    """Tool for cycling garage doors through open/close cycles"""
    
    def __init__(self, ha_url: str, token: str, timeout: int = 10):
        self.ha_url = ha_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.timeout = timeout
        self.cycle_count = 0
        self.door_entities = {
            'main': 'cover.garage_door',
            'internal': 'cover.internal_garage_door'
        }
        
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Tuple[int, Dict, float]:
        """Make HTTP request to Home Assistant API"""
        url = f"{self.ha_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            end_time = time.time()
            response_time = end_time - start_time
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"text": response.text}
                
            return response.status_code, response_data, response_time
            
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            response_time = end_time - start_time
            return 0, {"error": str(e)}, response_time
    
    def get_door_state(self, entity_id: str) -> str:
        """Get current state of a door entity"""
        endpoint = f"/api/states/{entity_id}"
        status_code, response_data, response_time = self.make_request('GET', endpoint)
        
        if status_code == 200:
            state = response_data.get('state', 'unknown')
            logger.debug(f"Door {entity_id} state: {state} ({response_time:.3f}s)")
            return state
        else:
            logger.error(f"Failed to get state for {entity_id}: HTTP {status_code}")
            return 'unknown'
    
    def send_door_command(self, entity_id: str, service: str) -> bool:
        """Send a command to a door entity"""
        endpoint = f"/api/services/cover/{service}"
        data = {"entity_id": entity_id}
        
        status_code, response_data, response_time = self.make_request('POST', endpoint, data)
        
        success = status_code == 200
        door_name = entity_id.split('.')[-1].replace('_', ' ').title()
        
        if success:
            logger.info(f"✅ {door_name}: {service} command sent ({response_time:.3f}s)")
        else:
            logger.error(f"❌ {door_name}: Failed to send {service} command - HTTP {status_code}")
            logger.error(f"   Response: {response_data}")
            
        return success
    
    def wait_for_door_state(self, entity_id: str, target_state: str, max_wait: int = 60) -> bool:
        """Wait for a door to reach the target state"""
        door_name = entity_id.split('.')[-1].replace('_', ' ').title()
        logger.info(f"⏳ Waiting for {door_name} to reach '{target_state}' state...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            current_state = self.get_door_state(entity_id)
            
            if current_state == target_state:
                elapsed = time.time() - start_time
                logger.info(f"✅ {door_name} reached '{target_state}' state ({elapsed:.1f}s)")
                return True
            elif current_state in ['unavailable', 'unknown']:
                logger.warning(f"⚠️  {door_name} state is {current_state}")
            
            time.sleep(2)  # Check every 2 seconds
        
        elapsed = time.time() - start_time
        logger.error(f"❌ {door_name} did not reach '{target_state}' state within {max_wait}s (elapsed: {elapsed:.1f}s)")
        return False
    
    def wait_for_both_doors_state(self, target_state: str, max_wait: int = 60) -> bool:
        """Wait for both doors to reach the target state"""
        logger.info(f"⏳ Waiting for both doors to reach '{target_state}' state...")
        
        main_success = self.wait_for_door_state(self.door_entities['main'], target_state, max_wait)
        internal_success = self.wait_for_door_state(self.door_entities['internal'], target_state, max_wait)
        
        if main_success and internal_success:
            logger.info(f"✅ Both doors reached '{target_state}' state")
            return True
        else:
            logger.error(f"❌ One or both doors failed to reach '{target_state}' state")
            return False
    
    def open_both_doors(self) -> bool:
        """Open both garage doors"""
        logger.info("🚪 Opening both garage doors...")
        
        # Send open commands to both doors
        main_success = self.send_door_command(self.door_entities['main'], 'open_cover')
        internal_success = self.send_door_command(self.door_entities['internal'], 'open_cover')
        
        if not (main_success and internal_success):
            logger.error("❌ Failed to send open commands to one or both doors")
            return False
        
        # Wait for both doors to be fully open
        return self.wait_for_both_doors_state('open')
    
    def close_both_doors(self) -> bool:
        """Close both garage doors"""
        logger.info("🚪 Closing both garage doors...")
        
        # Send close commands to both doors
        main_success = self.send_door_command(self.door_entities['main'], 'close_cover')
        internal_success = self.send_door_command(self.door_entities['internal'], 'close_cover')
        
        if not (main_success and internal_success):
            logger.error("❌ Failed to send close commands to one or both doors")
            return False
        
        # Wait for both doors to be fully closed
        return self.wait_for_both_doors_state('closed')
    
    def perform_cycle(self) -> bool:
        """Perform one complete open/close cycle"""
        self.cycle_count += 1
        logger.info(f"🔄 Starting cycle #{self.cycle_count}")
        logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Open both doors
        if not self.open_both_doors():
            logger.error("❌ Failed to open doors, aborting cycle")
            return False
        
        logger.info("✅ Doors opened successfully")
        time.sleep(2)  # Brief pause between open and close
        
        # Close both doors
        if not self.close_both_doors():
            logger.error("❌ Failed to close doors, cycle incomplete")
            return False
        
        logger.info(f"✅ Cycle #{self.cycle_count} completed successfully")
        return True
    
    def run_continuous_cycling(self, max_cycles: Optional[int] = None):
        """Run continuous door cycling with random intervals"""
        logger.info("🚀 Starting garage door cycling tool")
        logger.info(f"Target: {self.ha_url}")
        logger.info(f"Main door: {self.door_entities['main']}")
        logger.info(f"Internal door: {self.door_entities['internal']}")
        logger.info(f"Random wait interval: 15-30 seconds")
        if max_cycles:
            logger.info(f"Maximum cycles: {max_cycles}")
        else:
            logger.info("Maximum cycles: Unlimited (Ctrl+C to stop)")
        logger.info("=" * 60)
        
        try:
            while True:
                # Check if we've reached the maximum cycles
                if max_cycles and self.cycle_count >= max_cycles:
                    logger.info(f"🏁 Reached maximum cycles ({max_cycles}), stopping")
                    break
                
                # Perform one cycle
                cycle_success = self.perform_cycle()
                
                if not cycle_success:
                    logger.error("❌ Cycle failed, stopping continuous operation")
                    break
                
                # Random wait between cycles (15-30 seconds)
                wait_time = random.randint(15, 30)
                logger.info(f"⏰ Waiting {wait_time} seconds before next cycle...")
                
                # Sleep with periodic status updates
                for remaining in range(wait_time, 0, -5):
                    if remaining <= 5:
                        logger.info(f"   Starting next cycle in {remaining} seconds...")
                        time.sleep(remaining)
                        break
                    else:
                        time.sleep(5)
                        if remaining % 10 == 0:  # Status update every 10 seconds
                            logger.info(f"   Next cycle in {remaining} seconds...")
                
        except KeyboardInterrupt:
            logger.info("\n⏹️  Cycling stopped by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        
        logger.info(f"📊 Total cycles completed: {self.cycle_count}")
        logger.info("🏁 Door cycling tool finished")
    
    def test_connectivity(self) -> bool:
        """Test connectivity to Home Assistant and door entities"""
        logger.info("🔍 Testing connectivity to Home Assistant...")
        
        # Test basic connectivity
        endpoint = "/api/states"
        status_code, response_data, response_time = self.make_request('GET', endpoint)
        
        if status_code != 200:
            logger.error(f"❌ Failed to connect to Home Assistant: HTTP {status_code}")
            return False
        
        logger.info(f"✅ Connected to Home Assistant ({response_time:.3f}s)")
        
        # Test door entity availability
        for door_name, entity_id in self.door_entities.items():
            state = self.get_door_state(entity_id)
            if state == 'unknown':
                logger.error(f"❌ {door_name.title()} door entity ({entity_id}) not available")
                return False
            else:
                logger.info(f"✅ {door_name.title()} door ({entity_id}) state: {state}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Garage Door Cycling Tool - Opens and closes both garage doors continuously')
    parser.add_argument('--url', required=True, help='Home Assistant URL (e.g., http://192.168.1.100:8123)')
    parser.add_argument('--token', required=True, help='Home Assistant long-lived access token')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('--max-cycles', type=int, help='Maximum number of cycles to run (default: unlimited)')
    parser.add_argument('--test-only', action='store_true', help='Test connectivity only, do not run cycles')
    
    args = parser.parse_args()
    
    # Create door cycler instance
    cycler = DoorCycler(args.url, args.token, args.timeout)
    
    try:
        # Test connectivity first
        if not cycler.test_connectivity():
            logger.error("❌ Connectivity test failed, exiting")
            sys.exit(1)
        
        if args.test_only:
            logger.info("✅ Connectivity test passed, exiting (test-only mode)")
            sys.exit(0)
        
        # Run continuous cycling
        cycler.run_continuous_cycling(args.max_cycles)
        
    except Exception as e:
        logger.error(f"❌ Tool failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
