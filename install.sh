#!/bin/bash

# Garage Opener Installation Script
# This script installs the garage opener service on a Raspberry Pi

set -e

echo "=== Garage Opener Installation Script ==="

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
cp "$INSTALL_DIR/garage-opener.service" /etc/systemd/system/
systemctl daemon-reload

# Install dependencies
echo "Installing dependencies..."
apt update
apt install -y python3-rpi.gpio

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
systemctl enable garage-opener.service
systemctl start garage-opener.service

# Check service status
echo "Checking service status..."
if systemctl is-active --quiet garage-opener.service; then
    echo "✅ Service is running successfully!"
else
    echo "❌ Service failed to start. Check logs with: journalctl -u garage-opener.service"
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
echo "  GET /open   - Trigger garage opening"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status garage-opener.service  # Check service status"
echo "  sudo systemctl stop garage-opener.service    # Stop the service"
echo "  sudo systemctl start garage-opener.service   # Start the service"
echo "  sudo systemctl restart garage-opener.service # Restart the service"
echo "  sudo journalctl -u garage-opener.service -f  # Follow logs in real-time"
echo "  sudo journalctl -u garage-opener.service -n 50  # Show last 50 log entries"
echo ""
echo "Test the service:"
echo "  curl http://localhost:8080/open"
