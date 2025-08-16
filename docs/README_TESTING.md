# Home Assistant API Testing for Garage Door Controller

This directory contains a comprehensive test suite for testing your ESPHome garage door controller through the Home Assistant API.

## Files Overview

- `homeassistant_test_plan.md` - Detailed test plan with all test cases
- `ha_test_runner.py` - Automated Python test script
- `test_config.example.json` - Example configuration file
- `README_TESTING.md` - This file (setup and usage instructions)

## Quick Start

### 1. Prerequisites

- Home Assistant running and accessible
- ESPHome device online and connected to Home Assistant
- Python 3.6+ with `requests` library
- Long-lived access token from Home Assistant

### 2. Setup

1. **Install dependencies:**

```bash
pip install requests
```

2. **Get your Home Assistant access token:**
   - Go to your Home Assistant web interface
   - Click on your profile (bottom left)
   - Scroll down to "Long-Lived Access Tokens"
   - Click "Create Token"
   - Copy the token (you won't see it again!)

3. **Prepare the test script:**

```bash
chmod +x ha_test_runner.py
```

### 3. Basic Usage

**Run all tests:**

```bash
python3 ha_test_runner.py --url http://YOUR_HA_IP:8123 --token YOUR_TOKEN
```

**Run only state verification tests (safe):**

```bash
python3 ha_test_runner.py --url http://YOUR_HA_IP:8123 --token YOUR_TOKEN --states-only
```

**Run quick test suite:**

```bash
python3 ha_test_runner.py --url http://YOUR_HA_IP:8123 --token YOUR_TOKEN --quick
```

### 4. Test Options

- `--covers-only` - Test only cover entities (garage doors)
- `--switches-only` - Test only switch entities
- `--states-only` - Test only state reading (no device movement)
- `--quick` - Run minimal test suite
- `--timeout 30` - Set request timeout (default: 10 seconds)

## Safety Notes

⚠️ **IMPORTANT SAFETY CONSIDERATIONS**

1. **Physical Safety:**
   - Ensure garage doors are safe to operate
   - Check for obstructions before testing
   - Have manual override available
   - Test during safe hours when no one is around

2. **System Safety:**
   - Start with `--states-only` to verify connectivity
   - Test individual components before full sequences
   - Monitor Home Assistant logs during testing
   - Have ESPHome device logs accessible

3. **Test Environment:**
   - Use a test environment when possible
   - Verify entity IDs match your configuration
   - Ensure stable network connectivity

## Understanding Test Results

### Success Indicators

- ✅ Test passed with HTTP 200 response
- Response time under 1 second (typically)
- Physical device responds as expected

### Failure Indicators

- ❌ Test failed with error HTTP status
- Timeout or network errors
- Unexpected device behavior

### Log Files

- `ha_test_results.log` - Detailed test execution log
- `ha_test_detailed_results.json` - Complete test results in JSON format

## Test Categories

### 1. State Verification Tests (Safe)

These tests only read entity states and don't cause device movement:

```bash
python3 ha_test_runner.py --url http://YOUR_HA_IP:8123 --token YOUR_TOKEN --states-only
```

### 2. Switch Control Tests

Test individual switch entities:

```bash
python3 ha_test_runner.py --url http://YOUR_HA_IP:8123 --token YOUR_TOKEN --switches-only
```

### 3. Cover Control Tests (Physical Movement)

Test garage door operations (⚠️ causes actual movement):

```bash
python3 ha_test_runner.py --url http://YOUR_HA_IP:8123 --token YOUR_TOKEN --covers-only
```

## Troubleshooting

### Common Issues

1. **HTTP 401 Unauthorized**
   - Check your access token
   - Verify token hasn't expired
   - Ensure token has proper permissions

2. **HTTP 404 Not Found**
   - Verify Home Assistant URL is correct
   - Check if API is enabled in Home Assistant
   - Ensure ESPHome device is connected

3. **Entity Not Found Errors**
   - Verify entity IDs in Home Assistant
   - Check ESPHome device configuration
   - Ensure device is online and responsive

4. **Timeout Errors**
   - Increase timeout with `--timeout 30`
   - Check network connectivity
   - Verify Home Assistant is responsive

### Debugging Steps

1. **Test connectivity:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://YOUR_HA_IP:8123/api/
```

2. **List all entities:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://YOUR_HA_IP:8123/api/states | grep garage
```

3. **Check specific entity:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://YOUR_HA_IP:8123/api/states/cover.garage_door
```

## Manual Testing

If you prefer manual testing, use the test plan in `homeassistant_test_plan.md`. Each test case includes the exact curl commands to run.

### Example Manual Test

```bash
# Test getting garage door state
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  http://YOUR_HA_IP:8123/api/states/cover.garage_door

# Test opening garage door (⚠️ causes movement)
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/open_cover
```

## Integration with CI/CD

The test script returns appropriate exit codes for automation:

- `0` - All tests passed
- `1` - Some tests failed
- `2` - Test execution error or interrupted

Example usage in scripts:

```bash
#!/bin/bash
python3 ha_test_runner.py --url $HA_URL --token $HA_TOKEN --quick
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

## Customizing Tests

To modify or extend the tests:

1. **Edit test cases in `ha_test_runner.py`**
2. **Add new entity IDs for your configuration**
3. **Adjust timing delays if needed**
4. **Create custom test suites for specific scenarios**

## Support

For issues with:

- **ESPHome configuration:** Check ESPHome documentation
- **Home Assistant setup:** Check Home Assistant documentation
- **Test script bugs:** Review test logs and modify script as needed

## Entity Reference

Based on your ESPHome configuration:

### Cover Entities

- `cover.garage_door` - Main garage gate (18s open, 23s close)
- `cover.internal_garage_door` - Internal door (15s open/close)

### Switch Entities

- `switch.gate_close_switch` - GPIO pin 2
- `switch.gate_open_switch` - GPIO pin 3
- `switch.gate_lock_open_switch` - GPIO pin 4
- `switch.internal_door_click` - GPIO pin 10

All switches use inverted logic (on = GPIO low, off = GPIO high).
