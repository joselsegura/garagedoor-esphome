#!/bin/bash
set -e

# ESPHome Systemd Service Installation Script
# This script installs and configures the ESPHome service for garage door control

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
VENV_PATH="/home/doorpi/esphome-venv"
YAML_FILE="garagedoor.yaml"
SERVICE_NAME="esphome-garagedoor"

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}ESPHome Garage Door Service Installation${NC}"
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

    print_info "✓ systemd is available"
}

create_user_if_needed() {
    print_step "Checking service user..."

    if ! id "$SERVICE_USER" &>/dev/null; then
        print_info "Creating service user: $SERVICE_USER"
        useradd -r -m -s /bin/bash "$SERVICE_USER"
        usermod -a -G dialout,gpio "$SERVICE_USER" 2>/dev/null || true
        print_info "✓ User $SERVICE_USER created"
    else
        print_info "✓ User $SERVICE_USER already exists"
    fi
}

setup_directories() {
    print_step "Setting up directories..."

    # Create project directory
    mkdir -p "$PROJECT_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR"
    print_info "✓ Project directory: $PROJECT_DIR"

    # Create logs directory
    mkdir -p "/var/log/esphome"
    chown "$SERVICE_USER:$SERVICE_GROUP" "/var/log/esphome"
    print_info "✓ Log directory: /var/log/esphome"
}

install_service_file() {
    print_step "Installing systemd service file..."

    # Create the service file
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=ESPHome Garage Door Controller
Documentation=https://esphome.io/
After=network-online.target
Wants=network-online.target
Restart=on-failure

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$VENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$VENV_PATH/bin/esphome run $YAML_FILE
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR
ReadWritePaths=/var/log/esphome
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
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

show_instructions() {
    print_header
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Copy your ESPHome YAML file to: $PROJECT_DIR/$YAML_FILE"
    echo "2. Install ESPHome in virtual environment: $VENV_PATH"
    echo "3. Test the service manually:"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo "   sudo systemctl status $SERVICE_NAME"
    echo ""
    echo -e "${BLUE}Service management commands:${NC}"
    echo "• Start service:    sudo systemctl start $SERVICE_NAME"
    echo "• Stop service:     sudo systemctl stop $SERVICE_NAME"
    echo "• Restart service:  sudo systemctl restart $SERVICE_NAME"
    echo "• Check status:     sudo systemctl status $SERVICE_NAME"
    echo "• View logs:        sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo -e "${BLUE}Configuration files:${NC}"
    echo "• Service file:     /etc/systemd/system/${SERVICE_NAME}.service"
    echo "• Project directory: $PROJECT_DIR"
    echo "• Virtual env:      $VENV_PATH"
    echo ""
    echo -e "${YELLOW}Remember to:${NC}"
    echo "• Ensure ESPHome is installed in the virtual environment"
    echo "• Place your YAML configuration file in the project directory"
    echo "• Check that the service user has GPIO access permissions"
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
        --venv-path)
            VENV_PATH="$2"
            shift 2
            ;;
        --yaml-file)
            YAML_FILE="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --user USER           Service user (default: doorpi)"
            echo "  --project-dir DIR     Project directory (default: /home/doorpi/garagedoor_esphome)"
            echo "  --venv-path PATH      Virtual environment path (default: /home/doorpi/esphome-venv)"
            echo "  --yaml-file FILE      ESPHome YAML file (default: garagedoor.yaml)"
            echo "  --service-name NAME   Service name (default: esphome-garagedoor)"
            echo "  -h, --help           Show this help message"
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
    print_info "  Virtual environment: $VENV_PATH"
    print_info "  YAML file: $YAML_FILE"
    print_info "  Service name: $SERVICE_NAME"
    echo ""

    check_root
    check_system_requirements
    create_user_if_needed
    setup_directories
    install_service_file
    configure_service
    show_instructions
}

# Run main function
main
