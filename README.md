# ESPHome Garage Door Controller

A comprehensive garage door control system built with ESPHome, featuring GPIO monitoring, safety protection, and automated testing.

## Quick Start

1. **ESPHome Configuration**: The main configuration is in `garagedoor.yaml`
2. **Deployment**: See `deployment/README.md` for system installation
3. **Testing**: Use scripts in `scripts/testing/` for validation
4. **Monitoring**: GPIO protection runs via `scripts/monitoring/gpio_safeguard.py`

## Repository Structure

```
├── garagedoor.yaml              # Main ESPHome configuration
├── config/                      # ESPHome configurations
├── scripts/                     # Python utilities
│   ├── monitoring/             # GPIO monitoring & protection
│   ├── testing/                # Testing & validation tools
│   └── utils/                  # General utilities
├── deployment/                  # System deployment files
├── docs/                       # Documentation
├── tests/                      # Test configurations & data
└── logs/                       # Runtime logs
```

## Features

- **ESPHome Integration**: Native Home Assistant integration
- **GPIO Safety**: Automatic protection against dangerous GPIO states
- **Monitoring**: Real-time GPIO state logging
- **Testing**: Comprehensive API and hardware testing tools
- **Auto-deployment**: Systemd services for production deployment

## Documentation

- [Service Setup Guide](docs/README_ESPHOME_SERVICE.md)
- [Testing Documentation](docs/README_TESTING.md)
- [Deployment Guide](deployment/README.md)

## Safety Features

- GPIO4: Maximum 2 seconds at 0
- GPIO3: Maximum 20 seconds at 0
- GPIO10: Maximum 4 seconds at 0
- GPIO2: Maximum 25 seconds at 0
- Automatic correction of safety violations
