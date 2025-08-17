#!/bin/bash

# Raspberry Pi Relay Module Installation Script
# This script installs the relay module service on a Raspberry Pi

set -e

echo "=== Raspberry Pi Relay Module Installation Script ==="

# Check if running as root (via sudo)
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run with sudo"
   exit 1
fi

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    echo "The GPIO functionality may not work correctly"
fi

# Set installation directory (current directory)
INSTALL_DIR="$(pwd)"
echo "Using installation directory: $INSTALL_DIR"

# Install systemd service
echo "Installing systemd service..."
cp "$INSTALL_DIR/relay-module.service" /etc/systemd/system/
systemctl daemon-reload

# Install system dependencies
echo "Installing system dependencies..."
apt update
apt install -y python3-rpi.gpio python3-pip python3-venv

# Create and activate virtual environment
echo "Setting up virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Set up GPIO permissions
echo "Setting up GPIO permissions..."
# Add jodok user to gpio group (group should already exist)
usermod -a -G gpio jodok
echo "✅ Added jodok user to gpio group"
echo "   Note: Your system already has proper udev rules for GPIO access"

# Note: Using systemd logging - no log file needed
echo "Using systemd logging..."

# Enable and start the service
echo "Enabling and starting service..."
systemctl enable relay-module.service
systemctl start relay-module.service

# Check service status
echo "Checking service status..."
if systemctl is-active --quiet relay-module.service; then
    echo "✅ Service is running successfully!"
else
    echo "❌ Service failed to start. Check logs with: journalctl -u relay-module.service"
    exit 1
fi

echo ""
echo "=== Installation Complete ==="
echo "Service is now running on http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "Note: The service is running as user 'jodok'"
echo "You may need to log out and back in for GPIO group permissions to take effect"
echo ""
echo "Note: This assumes you're running the script from the git checkout directory"
echo ""
echo "Available endpoints:"
echo "  POST /relay/trigger - Trigger relay on specified GPIO pin"
echo "  GET  /system/health - Health check endpoint"
echo "  GET  /system/status - Service status and configuration"
echo "  GET  /docs          - Swagger API documentation"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status relay-module.service  # Check service status"
echo "  sudo systemctl stop relay-module.service    # Stop the service"
echo "  sudo systemctl start relay-module.service   # Start the service"
echo "  sudo systemctl restart relay-module.service # Restart the service"
echo "  sudo journalctl -u relay-module.service -f  # Follow logs in real-time"
echo "  sudo journalctl -u relay-module.service -n 50  # Show last 50 log entries"
echo ""
echo "Test the service:"
echo "  curl http://localhost:8080/system/health"
echo "  curl http://localhost:8080/system/status"
echo "  python3 test_relay_api.py  # Run the test script"
echo "  # Visit http://localhost:8080/docs for interactive API documentation"
