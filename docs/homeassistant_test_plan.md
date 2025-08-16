# Home Assistant API Test Plan for Garage Door Controller

## Overview
This test plan covers testing the ESPHome garage door controller through Home Assistant API calls. The system includes two main cover entities and four switch entities that control garage door operations.

## Device Information
- **ESPHome Device Name:** garagedoor-rpi / garagedoor-rpi2
- **Device Type:** Garage Door Controller
- **Platform:** ESPHome on Raspberry Pi

## Test Entities

### Cover Entities
1. **Garage Door (Main Gate)**
   - Entity ID: `cover.garage_door`
   - Device Class: gate
   - Operations: open, close, stop
   - Open Duration: 18s
   - Close Duration: 23s

2. **Internal Garage Door**
   - Entity ID: `cover.internal_garage_door`
   - Device Class: garage
   - Operations: open, close, stop
   - Open Duration: 15s
   - Close Duration: 15s

### Switch Entities
1. **Gate Close Switch**
   - Entity ID: `switch.gate_close_switch`
   - Function: Controls gate closing mechanism
   - GPIO Pin: 2

2. **Gate Open Switch**
   - Entity ID: `switch.gate_open_switch`
   - Function: Controls gate opening mechanism
   - GPIO Pin: 3

3. **Gate Lock Open Switch**
   - Entity ID: `switch.gate_lock_open_switch`
   - Function: Controls gate lock for opening
   - GPIO Pin: 4

4. **Internal Door Click**
   - Entity ID: `switch.internal_door_click`
   - Function: Controls internal garage door
   - GPIO Pin: 10

## Test Prerequisites

### Home Assistant Setup
1. Home Assistant must be running and accessible
2. ESPHome device must be connected and online
3. API access token must be available
4. Network connectivity between test client and Home Assistant

### Required Information
- Home Assistant URL: `http://YOUR_HA_IP:8123`
- Long-lived access token
- Device entity IDs (listed above)

## Test Cases

### TC-001: Cover Entity - Garage Door Open
**Objective:** Test opening the main garage door
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/open_cover
```
**Expected Result:**
- HTTP 200 response
- Gate lock switch activates (1s)
- Gate open switch activates
- Gate lock switch deactivates
- Door opens over 18 seconds

### TC-002: Cover Entity - Garage Door Close
**Objective:** Test closing the main garage door
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/close_cover
```
**Expected Result:**
- HTTP 200 response
- Gate close switch activates
- Door closes over 23 seconds

### TC-003: Cover Entity - Garage Door Stop
**Objective:** Test stopping the main garage door
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/stop_cover
```
**Expected Result:**
- HTTP 200 response
- All switches (gate_close, gate_open, gate_lock_open) turn off
- Door stops movement

### TC-004: Cover Entity - Internal Door Open
**Objective:** Test opening the internal garage door
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.internal_garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/open_cover
```
**Expected Result:**
- HTTP 200 response
- Internal door click switch activates for 2s
- Door opens over 15 seconds

### TC-005: Cover Entity - Internal Door Close
**Objective:** Test closing the internal garage door
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.internal_garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/close_cover
```
**Expected Result:**
- HTTP 200 response
- Internal door click switch activates for 2s
- Door closes over 15 seconds

### TC-006: Cover Entity - Internal Door Stop
**Objective:** Test stopping the internal garage door
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.internal_garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/stop_cover
```
**Expected Result:**
- HTTP 200 response
- Internal door click switch turns off
- Door stops movement

### TC-007: Switch Entity - Gate Close Switch On
**Objective:** Test turning on gate close switch directly
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.gate_close_switch"}' \
  http://YOUR_HA_IP:8123/api/services/switch/turn_on
```
**Expected Result:**
- HTTP 200 response
- GPIO pin 2 set to low (0)
- Switch state shows "on"

### TC-008: Switch Entity - Gate Close Switch Off
**Objective:** Test turning off gate close switch directly
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.gate_close_switch"}' \
  http://YOUR_HA_IP:8123/api/services/switch/turn_off
```
**Expected Result:**
- HTTP 200 response
- GPIO pin 2 set to high (1)
- Switch state shows "off"

### TC-009: Switch Entity - Gate Open Switch On
**Objective:** Test turning on gate open switch directly
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.gate_open_switch"}' \
  http://YOUR_HA_IP:8123/api/services/switch/turn_on
```
**Expected Result:**
- HTTP 200 response
- GPIO pin 3 set to low (0)
- Switch state shows "on"

### TC-010: Switch Entity - Gate Open Switch Off
**Objective:** Test turning off gate open switch directly
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.gate_open_switch"}' \
  http://YOUR_HA_IP:8123/api/services/switch/turn_off
```
**Expected Result:**
- HTTP 200 response
- GPIO pin 3 set to high (1)
- Switch state shows "off"

### TC-011: Switch Entity - Gate Lock Open Switch On
**Objective:** Test turning on gate lock open switch directly
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.gate_lock_open_switch"}' \
  http://YOUR_HA_IP:8123/api/services/switch/turn_on
```
**Expected Result:**
- HTTP 200 response
- GPIO pin 4 set to low (0)
- Switch state shows "on"

### TC-012: Switch Entity - Gate Lock Open Switch Off
**Objective:** Test turning off gate lock open switch directly
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.gate_lock_open_switch"}' \
  http://YOUR_HA_IP:8123/api/services/switch/turn_off
```
**Expected Result:**
- HTTP 200 response
- GPIO pin 4 set to high (1)
- Switch state shows "off"

### TC-013: Switch Entity - Internal Door Click On
**Objective:** Test turning on internal door click switch directly
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.internal_door_click"}' \
  http://YOUR_HA_IP:8123/api/services/switch/turn_on
```
**Expected Result:**
- HTTP 200 response
- GPIO pin 10 set to low (0)
- Switch state shows "on"

### TC-014: Switch Entity - Internal Door Click Off
**Objective:** Test turning off internal door click switch directly
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.internal_door_click"}' \
  http://YOUR_HA_IP:8123/api/services/switch/turn_off
```
**Expected Result:**
- HTTP 200 response
- GPIO pin 10 set to high (1)
- Switch state shows "off"

### TC-015: State Verification - Get All Entity States
**Objective:** Verify all entity states through API
**API Call:**
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  http://YOUR_HA_IP:8123/api/states
```
**Expected Result:**
- HTTP 200 response
- JSON response containing all entity states
- All garage door entities present and accessible

### TC-016: Specific Entity State - Garage Door
**Objective:** Get specific state of main garage door
**API Call:**
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  http://YOUR_HA_IP:8123/api/states/cover.garage_door
```
**Expected Result:**
- HTTP 200 response
- JSON response with current door state (open/closed/opening/closing)

## Integration Test Scenarios

### ITS-001: Complete Open Sequence - Main Door
**Objective:** Test complete opening sequence for main garage door
**Steps:**
1. Verify door is closed
2. Send open command
3. Verify sequence: lock on → delay → open on → lock off
4. Wait for open duration (18s)
5. Verify door state is "open"

### ITS-002: Complete Close Sequence - Main Door
**Objective:** Test complete closing sequence for main garage door
**Steps:**
1. Verify door is open
2. Send close command
3. Verify close switch activates
4. Wait for close duration (23s)
5. Verify door state is "closed"

### ITS-003: Emergency Stop Test
**Objective:** Test emergency stop during operation
**Steps:**
1. Start door opening
2. Send stop command mid-operation
3. Verify all switches turn off immediately
4. Verify door stops moving

### ITS-004: Rapid Command Test
**Objective:** Test rapid successive commands
**Steps:**
1. Send open command
2. Immediately send stop command
3. Send close command
4. Verify system handles commands appropriately

## Error Test Cases

### ETC-001: Invalid Entity ID
**Objective:** Test response to invalid entity ID
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.nonexistent_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/open_cover
```
**Expected Result:**
- HTTP 400 or appropriate error response
- Error message indicating entity not found

### ETC-002: Unauthorized Access
**Objective:** Test response without authentication token
**API Call:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/open_cover
```
**Expected Result:**
- HTTP 401 Unauthorized response

### ETC-003: Invalid Service Call
**Objective:** Test response to invalid service
**API Call:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "cover.garage_door"}' \
  http://YOUR_HA_IP:8123/api/services/cover/invalid_action
```
**Expected Result:**
- HTTP 400 or appropriate error response
- Error message indicating invalid service

## Performance Test Cases

### PTC-001: Response Time Test
**Objective:** Measure API response times
**Method:** Time each API call and verify response times are acceptable (< 1 second)

### PTC-002: Concurrent Request Test
**Objective:** Test multiple simultaneous requests
**Method:** Send multiple API calls simultaneously and verify all are handled correctly

## Test Environment Setup

### Required Tools
- curl or HTTP client
- Test execution environment
- Network access to Home Assistant
- GPIO monitoring capability (optional)

### Configuration Steps
1. Replace `YOUR_HA_IP` with actual Home Assistant IP address
2. Replace `YOUR_TOKEN` with valid long-lived access token
3. Verify entity IDs match your Home Assistant configuration
4. Ensure ESPHome device is online and responsive

## Test Execution Notes

### Safety Considerations
- Ensure garage doors are safe to operate during testing
- Have manual override available
- Test during safe hours
- Verify no obstructions before testing

### Monitoring
- Monitor Home Assistant logs during testing
- Monitor ESPHome device logs
- Watch for GPIO pin changes (if monitoring available)
- Record all API responses for analysis

### Test Data Collection
- Record response times
- Log all HTTP status codes
- Document any error messages
- Note actual vs expected behavior

## Success Criteria
- All API calls return appropriate HTTP status codes
- Entity states change as expected
- Physical hardware responds correctly
- No error conditions persist after test completion
- All safety mechanisms function properly

