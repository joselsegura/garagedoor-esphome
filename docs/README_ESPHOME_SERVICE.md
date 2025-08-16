# ESPHome Systemd Service Setup

This directory contains files to create a systemd service for running ESPHome at startup on your garage door controller system.

## Files Included

### ESPHome Service

- `esphome-garagedoor.service` - Systemd service template
- `install-esphome-service.sh` - Automated installation script

### GPIO Safeguard Service

- `gpio-safeguard.service` - GPIO protection systemd service template
- `install-gpio-safeguard-service.sh` - GPIO safeguard installation script
- `gpio_safeguard.py` - GPIO protection script

### Documentation

- `README_ESPHOME_SERVICE.md` - This documentation

## Quick Installation

1. **Transfer files to your controller system:**

   ```bash
   scp esphome-garagedoor.service install-esphome-service.sh gpio-safeguard.service install-gpio-safeguard-service.sh gpio_safeguard.py doorpi@your-controller-ip:~/
   ```

2. **Install ESPHome service:**

   ```bash
   sudo ./install-esphome-service.sh
   ```

3. **Install GPIO Safeguard service:**

   ```bash
   sudo ./install-gpio-safeguard-service.sh
   ```

3. **Customize for your system (if needed):**

   ```bash
   sudo ./install-esphome-service.sh \
     --user doorpi \
     --project-dir /home/doorpi/garagedoor_esphome \
     --venv-path /home/doorpi/esphome-venv \
     --yaml-file garagedoor.yaml
   ```

## Manual Installation

If you prefer to install manually:

### 1. Create Service User (if needed)

```bash
sudo useradd -r -m -s /bin/bash doorpi
sudo usermod -a -G dialout,gpio doorpi
```

### 2. Setup Directories

```bash
sudo mkdir -p /home/doorpi/garagedoor_esphome
sudo mkdir -p /var/log/esphome
sudo chown doorpi:doorpi /home/doorpi/garagedoor_esphome
sudo chown doorpi:doorpi /var/log/esphome
```

### 3. Install Service File

```bash
sudo cp esphome-garagedoor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable esphome-garagedoor
```

## Configuration

### Default Paths (modify in service file if needed)

- **User:** `doorpi`
- **Project Directory:** `/home/doorpi/garagedoor_esphome`
- **Virtual Environment:** `/home/doorpi/esphome-venv`
- **YAML File:** `garagedoor.yaml`

### ESPHome Installation

Ensure ESPHome is installed in the virtual environment:

```bash
sudo -u doorpi python3 -m venv /home/doorpi/esphome-venv
sudo -u doorpi /home/doorpi/esphome-venv/bin/pip install esphome
```

### YAML Configuration

Place your ESPHome configuration file:

```bash
sudo cp garagedoor.yaml /home/doorpi/garagedoor_esphome/
sudo chown doorpi:doorpi /home/doorpi/garagedoor_esphome/garagedoor.yaml
```

## Service Management

### ESPHome Service

```bash
# Start/Stop ESPHome service
sudo systemctl start esphome-garagedoor
sudo systemctl stop esphome-garagedoor
sudo systemctl restart esphome-garagedoor

# Check status
sudo systemctl status esphome-garagedoor

# View logs
sudo journalctl -u esphome-garagedoor -f

# Enable/Disable auto-start
sudo systemctl enable esphome-garagedoor
sudo systemctl disable esphome-garagedoor
```

### GPIO Safeguard Service

```bash
# Start/Stop GPIO safeguard service
sudo systemctl start gpio-safeguard
sudo systemctl stop gpio-safeguard
sudo systemctl restart gpio-safeguard

# Check status
sudo systemctl status gpio-safeguard

# View logs
sudo journalctl -u gpio-safeguard -f

# Test in dry-run mode
sudo -u doorpi python3 /home/doorpi/garagedoor_esphome/gpio_safeguard.py --dry-run

# Enable/Disable auto-start
sudo systemctl enable gpio-safeguard
sudo systemctl disable gpio-safeguard
```

### Both Services

```bash
# Start both services
sudo systemctl start esphome-garagedoor gpio-safeguard

# Check status of both
sudo systemctl status esphome-garagedoor gpio-safeguard

# View combined logs
sudo journalctl -u esphome-garagedoor -u gpio-safeguard -f
```

## Troubleshooting

### Common Issues

1. **Permission Errors:**

   ```bash
   sudo usermod -a -G dialout,gpio doorpi
   ```

2. **Virtual Environment Not Found:**

   ```bash
   sudo -u doorpi python3 -m venv /home/doorpi/esphome-venv
   sudo -u doorpi /home/doorpi/esphome-venv/bin/pip install esphome
   ```

3. **YAML File Not Found:**

   ```bash
   sudo cp your-config.yaml /home/doorpi/garagedoor_esphome/garagedoor.yaml
   sudo chown doorpi:doorpi /home/doorpi/garagedoor_esphome/garagedoor.yaml
   ```

4. **Service Won't Start:**

   ```bash
   # Check service file syntax
   sudo systemctl daemon-reload

   # Check detailed status
   sudo systemctl status esphome-garagedoor -l

   # View error logs
   sudo journalctl -u esphome-garagedoor --since "10 minutes ago"
   ```

### Testing ESPHome Manually

Before enabling the service, test ESPHome manually:

```bash
sudo -u doorpi /home/doorpi/esphome-venv/bin/esphome run /home/doorpi/garagedoor_esphome/garagedoor.yaml
```

## Security Features

The service includes several security hardening features:

- Runs as non-root user
- Private temporary directory
- Protected system directories
- Restricted home directory access
- Kernel protection enabled

## Customization

To modify the service configuration:

1. Edit `/etc/systemd/system/esphome-garagedoor.service`
2. Run `sudo systemctl daemon-reload`
3. Restart the service: `sudo systemctl restart esphome-garagedoor`

## Service File Location

After installation, the service file is located at:
`/etc/systemd/system/esphome-garagedoor.service`
