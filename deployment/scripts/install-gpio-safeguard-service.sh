#!/bin/bash
set -e

# GPIO Safeguard Systemd Service Installation Script
# This script installs and configures the GPIO Safeguard protection service

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values (modify these for your system)
SERVICE_USER="doorpi"
SERVICE_GROUP="doorpi"
PROJECT_DIR="/home/doorpi/garagedoor_esphome"
SCRIPT_NAME="gpio_safeguard.py"
SERVICE_NAME="gpio-safeguard"
STATUS_INTERVAL="60"

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}GPIO Safeguard Service Installation${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_system_requirements() {
    print_step "Checking system requirements..."

    # Check if systemd is available
    if ! command -v systemctl &> /dev/null; then
        print_error "systemctl not found. This system doesn't appear to use systemd."
        exit 1
    fi

    # Check if Python3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "python3 not found. Please install Python 3."
        exit 1
    fi

    print_info "✓ systemd is available"
    print_info "✓ Python3 is available"
}

check_gpio_access() {
    print_step "Checking GPIO access..."

    # Check if GPIO devices exist
    if [[ -e /dev/gpiomem ]] || [[ -d /sys/class/gpio ]]; then
        print_info "✓ GPIO devices found"
    else
        print_warning "GPIO devices not found. Service may not work without proper GPIO access."
    fi

    # Check if raspi-gpio is available
    if command -v raspi-gpio &> /dev/null; then
        print_info "✓ raspi-gpio command available"
    else
        print_warning "raspi-gpio command not found. Install with: sudo apt install raspi-gpio"
    fi
}

create_user_if_needed() {
    print_step "Checking service user..."

    if ! id "$SERVICE_USER" &>/dev/null; then
        print_info "Creating service user: $SERVICE_USER"
        useradd -r -m -s /bin/bash "$SERVICE_USER"
        usermod -a -G dialout,gpio "$SERVICE_USER" 2>/dev/null || true
        print_info "✓ User $SERVICE_USER created and added to gpio group"
    else
        print_info "✓ User $SERVICE_USER already exists"
        # Ensure user is in gpio group
        usermod -a -G gpio "$SERVICE_USER" 2>/dev/null || print_warning "Could not add user to gpio group"
    fi
}

setup_directories() {
    print_step "Setting up directories..."

    # Create project directory
    mkdir -p "$PROJECT_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR"
    print_info "✓ Project directory: $PROJECT_DIR"

    # Create logs directory
    mkdir -p "/var/log/gpio-safeguard"
    chown "$SERVICE_USER:$SERVICE_GROUP" "/var/log/gpio-safeguard"
    print_info "✓ Log directory: /var/log/gpio-safeguard"
}

install_service_file() {
    print_step "Installing systemd service file..."

    # Create the service file
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=GPIO Safeguard Protection System
Documentation=GPIO monitoring and protection service for garage door controller
After=network.target
Wants=network.target
PartOf=esphome-garagedoor.service
Conflicts=shutdown.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/$SCRIPT_NAME --status-interval $STATUS_INTERVAL
Restart=always
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Environment
Environment=PYTHONUNBUFFERED=1

# Security settings
NoNewPrivileges=false
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR
ReadWritePaths=/var/log/gpio-safeguard
ReadWritePaths=/dev/gpiomem
ReadWritePaths=/sys/class/gpio
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Resource limits
MemoryMax=128M
CPUQuota=50%

# Capabilities for GPIO access
CapabilityBoundingSet=CAP_SYS_RAWIO
AmbientCapabilities=CAP_SYS_RAWIO

[Install]
WantedBy=multi-user.target
Also=esphome-garagedoor.service
EOF

    print_info "✓ Service file created: /etc/systemd/system/${SERVICE_NAME}.service"
}

configure_service() {
    print_step "Configuring systemd service..."

    # Reload systemd
    systemctl daemon-reload
    print_info "✓ systemd daemon reloaded"

    # Enable service
    systemctl enable "$SERVICE_NAME"
    print_info "✓ Service enabled for automatic startup"
}

test_gpio_safeguard() {
    print_step "Testing GPIO safeguard script..."

    if [[ -f "$PROJECT_DIR/$SCRIPT_NAME" ]]; then
        print_info "✓ GPIO safeguard script found"

        # Test dry-run mode
        if sudo -u "$SERVICE_USER" python3 "$PROJECT_DIR/$SCRIPT_NAME" --dry-run --help &>/dev/null; then
            print_info "✓ Script appears to be working"
        else
            print_warning "Script test failed. Check dependencies and permissions."
        fi
    else
        print_warning "GPIO safeguard script not found at $PROJECT_DIR/$SCRIPT_NAME"
        print_info "Make sure to copy gpio_safeguard.py to the project directory"
    fi
}

show_instructions() {
    print_header
    echo -e "${GREEN}GPIO Safeguard Service installation completed!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Copy gpio_safeguard.py to: $PROJECT_DIR/$SCRIPT_NAME"
    echo "2. Ensure raspi-gpio is installed: sudo apt install raspi-gpio"
    echo "3. Test the service:"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo "   sudo systemctl status $SERVICE_NAME"
    echo ""
    echo -e "${BLUE}Service management commands:${NC}"
    echo "• Start service:    sudo systemctl start $SERVICE_NAME"
    echo "• Stop service:     sudo systemctl stop $SERVICE_NAME"
    echo "• Restart service:  sudo systemctl restart $SERVICE_NAME"
    echo "• Check status:     sudo systemctl status $SERVICE_NAME"
    echo "• View logs:        sudo journalctl -u $SERVICE_NAME -f"
    echo "• Dry-run test:     sudo -u $SERVICE_USER python3 $PROJECT_DIR/$SCRIPT_NAME --dry-run"
    echo ""
    echo -e "${BLUE}Configuration:${NC}"
    echo "• Service file:     /etc/systemd/system/${SERVICE_NAME}.service"
    echo "• Project directory: $PROJECT_DIR"
    echo "• Log directory:    /var/log/gpio-safeguard"
    echo "• Status interval:  $STATUS_INTERVAL seconds"
    echo ""
    echo -e "${YELLOW}Safety features enabled:${NC}"
    echo "• GPIO4: max 2 seconds at 0"
    echo "• GPIO3: max 20 seconds at 0"
    echo "• GPIO10: max 4 seconds at 0"
    echo "• GPIO2: max 25 seconds at 0"
    echo ""
    echo -e "${YELLOW}Security features:${NC}"
    echo "• Runs as non-root user ($SERVICE_USER)"
    echo "• Memory limited to 128MB"
    echo "• CPU limited to 50%"
    echo "• GPIO access capabilities only"
}

# Command line argument parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            SERVICE_USER="$2"
            SERVICE_GROUP="$2"
            shift 2
            ;;
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --script-name)
            SCRIPT_NAME="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --status-interval)
            STATUS_INTERVAL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --user USER               Service user (default: doorpi)"
            echo "  --project-dir DIR         Project directory (default: /home/doorpi/garagedoor_esphome)"
            echo "  --script-name SCRIPT      Script filename (default: gpio_safeguard.py)"
            echo "  --service-name NAME       Service name (default: gpio-safeguard)"
            echo "  --status-interval SEC     Status report interval (default: 60)"
            echo "  -h, --help               Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main installation process
main() {
    print_header
    print_info "Configuration:"
    print_info "  Service user: $SERVICE_USER"
    print_info "  Project directory: $PROJECT_DIR"
    print_info "  Script name: $SCRIPT_NAME"
    print_info "  Service name: $SERVICE_NAME"
    print_info "  Status interval: $STATUS_INTERVAL seconds"
    echo ""

    check_root
    check_system_requirements
    check_gpio_access
    create_user_if_needed
    setup_directories
    install_service_file
    configure_service
    test_gpio_safeguard
    show_instructions
}

# Run main function
main
