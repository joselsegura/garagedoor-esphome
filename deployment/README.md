# Deployment Guide

This directory contains everything needed to deploy the garage door controller system.

## Files

- `systemd/` - Systemd service files
- `scripts/` - Installation scripts

## Quick Installation

1. Copy files to target system
2. Run installation scripts:

   ```bash
   sudo ./scripts/install-esphome-service.sh
   sudo ./scripts/install-gpio-safeguard-service.sh
   ```

## Service Management

```bash
# Start services
sudo systemctl start esphome-garagedoor gpio-safeguard

# Check status
sudo systemctl status esphome-garagedoor gpio-safeguard

# View logs
sudo journalctl -u esphome-garagedoor -u gpio-safeguard -f
```

See [Service Setup Guide](../docs/README_ESPHOME_SERVICE.md) for detailed instructions.
