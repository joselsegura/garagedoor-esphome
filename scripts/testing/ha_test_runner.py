#!/usr/bin/env python3
"""Home Assistant API Test Runner for Garage Door Controller

This script automates the testing of Home Assistant API calls for the
ESPHome garage door controller. It executes the test plan and provides
detailed results and timing information.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from typing import Optional

import requests


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ha_test_results.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class HomeAssistantTester:
    """Test runner for Home Assistant API calls"""

    def __init__(self, ha_url: str, token: str, timeout: int = 10):
        self.ha_url = ha_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self.timeout = timeout
        self.test_results = []

    def make_request(
        self, method: str, endpoint: str, data: Optional[dict] = None
    ) -> tuple[int, dict, float]:
        """Make HTTP request to Home Assistant API"""
        url = f"{self.ha_url}{endpoint}"
        start_time = time.time()

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            elif method.upper() == "POST":
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

    def test_cover_service(
        self, entity_id: str, service: str, test_id: str, description: str
    ) -> bool:
        """Test cover service call"""
        logger.info(f"Running {test_id}: {description}")

        endpoint = f"/api/services/cover/{service}"
        data = {"entity_id": entity_id}

        status_code, response_data, response_time = self.make_request("POST", endpoint, data)

        success = status_code == 200
        result = {
            "test_id": test_id,
            "description": description,
            "endpoint": endpoint,
            "entity_id": entity_id,
            "service": service,
            "status_code": status_code,
            "response_time": response_time,
            "success": success,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat(),
        }

        self.test_results.append(result)

        if success:
            logger.info(f"✅ {test_id} passed ({response_time:.3f}s)")
        else:
            logger.error(f"❌ {test_id} failed: HTTP {status_code} ({response_time:.3f}s)")
            logger.error(f"   Response: {response_data}")

        return success

    def test_switch_service(
        self, entity_id: str, service: str, test_id: str, description: str
    ) -> bool:
        """Test switch service call"""
        logger.info(f"Running {test_id}: {description}")

        endpoint = f"/api/services/switch/{service}"
        data = {"entity_id": entity_id}

        status_code, response_data, response_time = self.make_request("POST", endpoint, data)

        success = status_code == 200
        result = {
            "test_id": test_id,
            "description": description,
            "endpoint": endpoint,
            "entity_id": entity_id,
            "service": service,
            "status_code": status_code,
            "response_time": response_time,
            "success": success,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat(),
        }

        self.test_results.append(result)

        if success:
            logger.info(f"✅ {test_id} passed ({response_time:.3f}s)")
        else:
            logger.error(f"❌ {test_id} failed: HTTP {status_code} ({response_time:.3f}s)")
            logger.error(f"   Response: {response_data}")

        return success

    def test_entity_state(self, entity_id: str, test_id: str, description: str) -> bool:
        """Test getting entity state"""
        logger.info(f"Running {test_id}: {description}")

        endpoint = f"/api/states/{entity_id}"

        status_code, response_data, response_time = self.make_request("GET", endpoint)

        success = status_code == 200
        result = {
            "test_id": test_id,
            "description": description,
            "endpoint": endpoint,
            "entity_id": entity_id,
            "service": "get_state",
            "status_code": status_code,
            "response_time": response_time,
            "success": success,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat(),
        }

        self.test_results.append(result)

        if success:
            state = response_data.get("state", "unknown")
            logger.info(f"✅ {test_id} passed ({response_time:.3f}s) - State: {state}")
        else:
            logger.error(f"❌ {test_id} failed: HTTP {status_code} ({response_time:.3f}s)")
            logger.error(f"   Response: {response_data}")

        return success

    def test_all_states(self, test_id: str, description: str) -> bool:
        """Test getting all entity states"""
        logger.info(f"Running {test_id}: {description}")

        endpoint = "/api/states"

        status_code, response_data, response_time = self.make_request("GET", endpoint)

        success = status_code == 200
        entity_count = len(response_data) if isinstance(response_data, list) else 0

        result = {
            "test_id": test_id,
            "description": description,
            "endpoint": endpoint,
            "entity_id": "all",
            "service": "get_all_states",
            "status_code": status_code,
            "response_time": response_time,
            "success": success,
            "entity_count": entity_count,
            "timestamp": datetime.now().isoformat(),
        }

        self.test_results.append(result)

        if success:
            logger.info(
                f"✅ {test_id} passed ({response_time:.3f}s) - Found {entity_count} entities"
            )
        else:
            logger.error(f"❌ {test_id} failed: HTTP {status_code} ({response_time:.3f}s)")
            logger.error(f"   Response: {response_data}")

        return success

    def run_basic_cover_tests(self) -> int:
        """Run basic cover entity tests"""
        logger.info("=" * 60)
        logger.info("RUNNING COVER ENTITY TESTS")
        logger.info("=" * 60)

        failed_tests = 0

        # Main garage door tests
        if not self.test_cover_service(
            "cover.garage_door", "open_cover", "TC-001", "Open main garage door"
        ):
            failed_tests += 1
        time.sleep(2)  # Brief delay between tests

        if not self.test_cover_service(
            "cover.garage_door", "stop_cover", "TC-003", "Stop main garage door"
        ):
            failed_tests += 1
        time.sleep(2)

        if not self.test_cover_service(
            "cover.garage_door", "close_cover", "TC-002", "Close main garage door"
        ):
            failed_tests += 1
        time.sleep(2)

        # Internal garage door tests
        if not self.test_cover_service(
            "cover.internal_garage_door", "open_cover", "TC-004", "Open internal garage door"
        ):
            failed_tests += 1
        time.sleep(2)

        if not self.test_cover_service(
            "cover.internal_garage_door", "stop_cover", "TC-006", "Stop internal garage door"
        ):
            failed_tests += 1
        time.sleep(2)

        if not self.test_cover_service(
            "cover.internal_garage_door", "close_cover", "TC-005", "Close internal garage door"
        ):
            failed_tests += 1

        return failed_tests

    def run_basic_switch_tests(self) -> int:
        """Run basic switch entity tests"""
        logger.info("=" * 60)
        logger.info("RUNNING SWITCH ENTITY TESTS")
        logger.info("=" * 60)

        failed_tests = 0
        switches = [
            ("switch.gate_close_switch", "Gate close switch"),
            ("switch.gate_open_switch", "Gate open switch"),
            ("switch.gate_lock_open_switch", "Gate lock open switch"),
            ("switch.internal_door_click", "Internal door click switch"),
        ]

        test_counter = 7  # Starting from TC-007

        for entity_id, description in switches:
            # Test turn on
            if not self.test_switch_service(
                entity_id, "turn_on", f"TC-{test_counter:03d}", f"Turn on {description}"
            ):
                failed_tests += 1
            time.sleep(1)

            # Test turn off
            if not self.test_switch_service(
                entity_id, "turn_off", f"TC-{test_counter+1:03d}", f"Turn off {description}"
            ):
                failed_tests += 1
            time.sleep(1)

            test_counter += 2

        return failed_tests

    def run_state_tests(self) -> int:
        """Run entity state verification tests"""
        logger.info("=" * 60)
        logger.info("RUNNING STATE VERIFICATION TESTS")
        logger.info("=" * 60)

        failed_tests = 0

        # Test all states
        if not self.test_all_states("TC-015", "Get all entity states"):
            failed_tests += 1

        time.sleep(1)

        # Test specific entity states
        entities = [
            ("cover.garage_door", "Get main garage door state"),
            ("cover.internal_garage_door", "Get internal garage door state"),
            ("switch.gate_close_switch", "Get gate close switch state"),
            ("switch.gate_open_switch", "Get gate open switch state"),
            ("switch.gate_lock_open_switch", "Get gate lock open switch state"),
            ("switch.internal_door_click", "Get internal door click switch state"),
        ]

        for entity_id, description in entities:
            if not self.test_entity_state(
                entity_id, f"TC-016-{entity_id.split('.')[-1]}", description
            ):
                failed_tests += 1
            time.sleep(0.5)

        return failed_tests

    def run_error_tests(self) -> int:
        """Run error condition tests"""
        logger.info("=" * 60)
        logger.info("RUNNING ERROR CONDITION TESTS")
        logger.info("=" * 60)

        failed_tests = 0

        # Test invalid entity ID (should fail)
        logger.info("Running ETC-001: Test invalid entity ID")
        endpoint = "/api/services/cover/open_cover"
        data = {"entity_id": "cover.nonexistent_door"}

        status_code, response_data, response_time = self.make_request("POST", endpoint, data)

        # This should fail (we expect it to fail)
        if status_code == 200:
            logger.warning(f"⚠️  ETC-001: Expected failure but got success (HTTP {status_code})")
        else:
            logger.info(
                f"✅ ETC-001 passed: Correctly rejected invalid entity (HTTP {status_code})"
            )

        # Test invalid service (should fail)
        logger.info("Running ETC-003: Test invalid service")
        endpoint = "/api/services/cover/invalid_action"
        data = {"entity_id": "cover.garage_door"}

        status_code, response_data, response_time = self.make_request("POST", endpoint, data)

        # This should fail (we expect it to fail)
        if status_code == 200:
            logger.warning(f"⚠️  ETC-003: Expected failure but got success (HTTP {status_code})")
        else:
            logger.info(
                f"✅ ETC-003 passed: Correctly rejected invalid service (HTTP {status_code})"
            )

        return failed_tests

    def run_all_tests(self) -> int:
        """Run all test suites"""
        logger.info("🚀 Starting Home Assistant API Test Suite")
        logger.info(f"Target: {self.ha_url}")
        logger.info(f"Timeout: {self.timeout}s")
        logger.info(f"Start time: {datetime.now().isoformat()}")

        total_failed = 0

        try:
            # Run test suites
            total_failed += self.run_state_tests()
            total_failed += self.run_basic_switch_tests()
            total_failed += self.run_basic_cover_tests()
            total_failed += self.run_error_tests()

        except KeyboardInterrupt:
            logger.info("\n⏹️  Test execution interrupted by user")
            return -1
        except Exception as e:
            logger.error(f"❌ Test execution failed with error: {e}")
            return -1

        return total_failed

    def generate_report(self) -> str:
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        if total_tests > 0:
            avg_response_time = (
                sum(result["response_time"] for result in self.test_results) / total_tests
            )
        else:
            avg_response_time = 0

        report = f"""
{'='*80}
HOME ASSISTANT API TEST REPORT
{'='*80}

Test Summary:
  Total Tests:     {total_tests}
  Passed:          {passed_tests}
  Failed:          {failed_tests}
  Success Rate:    {(passed_tests/total_tests)*100 if total_tests > 0 else 0:.1f}%
  Avg Response:    {avg_response_time:.3f}s

Test Results:
"""

        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            report += f"  {result['test_id']}: {status} ({result['response_time']:.3f}s) - {result['description']}\n"

        if failed_tests > 0:
            report += "\nFailed Tests Details:\n"
            for result in self.test_results:
                if not result["success"]:
                    report += f"  {result['test_id']}: HTTP {result['status_code']} - {result.get('response_data', {})}\n"

        report += f"\nTest completed at: {datetime.now().isoformat()}\n"
        report += "=" * 80

        return report

    def save_detailed_results(self, filename: str = "ha_test_detailed_results.json"):
        """Save detailed test results to JSON file"""
        with open(filename, "w") as f:
            json.dump(
                {
                    "test_run_info": {
                        "ha_url": self.ha_url,
                        "total_tests": len(self.test_results),
                        "passed_tests": sum(1 for result in self.test_results if result["success"]),
                        "failed_tests": sum(
                            1 for result in self.test_results if not result["success"]
                        ),
                        "execution_time": datetime.now().isoformat(),
                    },
                    "test_results": self.test_results,
                },
                f,
                indent=2,
            )
        logger.info(f"📄 Detailed results saved to {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Home Assistant API Test Runner for Garage Door Controller"
    )
    parser.add_argument(
        "--url", required=True, help="Home Assistant URL (e.g., http://192.168.1.100:8123)"
    )
    parser.add_argument("--token", required=True, help="Home Assistant long-lived access token")
    parser.add_argument(
        "--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument("--quick", action="store_true", help="Run only basic functionality tests")
    parser.add_argument("--covers-only", action="store_true", help="Run only cover entity tests")
    parser.add_argument("--switches-only", action="store_true", help="Run only switch entity tests")
    parser.add_argument(
        "--states-only", action="store_true", help="Run only state verification tests"
    )

    args = parser.parse_args()

    # Create tester instance
    tester = HomeAssistantTester(args.url, args.token, args.timeout)

    try:
        failed_tests = 0

        if args.quick:
            logger.info("🏃 Running quick test suite")
            failed_tests += tester.run_state_tests()
        elif args.covers_only:
            failed_tests += tester.run_basic_cover_tests()
        elif args.switches_only:
            failed_tests += tester.run_basic_switch_tests()
        elif args.states_only:
            failed_tests += tester.run_state_tests()
        else:
            failed_tests = tester.run_all_tests()

        # Generate and display report
        report = tester.generate_report()
        print(report)

        # Save detailed results
        tester.save_detailed_results()

        # Exit with appropriate code
        if failed_tests == -1:
            sys.exit(2)  # Interrupted or error
        elif failed_tests > 0:
            sys.exit(1)  # Some tests failed
        else:
            logger.info("🎉 All tests passed!")
            sys.exit(0)  # All tests passed

    except Exception as e:
        logger.error(f"❌ Test runner failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
