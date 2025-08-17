#!/bin/bash

# Raspberry Pi Relay Module Lightweight Uninstall Script

set -e

echo "=== Raspberry Pi Relay Module Lightweight Uninstall Script ==="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Stop and disable the service
echo "Stopping and disabling service..."
systemctl stop relay-module.service 2>/dev/null || true
systemctl disable relay-module.service 2>/dev/null || true

# Remove systemd service file
echo "Removing systemd service file..."
rm -f /etc/systemd/system/relay-module.service
systemctl daemon-reload

# Note: Installation directory is git checkout, not removed
echo "Note: Installation directory is a git checkout and will not be removed"
echo "Note: Virtual environment in venv/ directory is not removed"
echo "Note: .env file is not removed"

# Note: Logs are handled by systemd journal
echo "Note: Logs are stored in systemd journal"

# Note: udev rules are system-wide and not removed
echo "Note: System udev rules for GPIO access are preserved"

echo "✅ Uninstallation complete!"
echo ""
echo "Note: The python3-rpi.gpio package was not removed."
echo "If you want to remove it, run: sudo apt remove python3-rpi.gpio"
echo ""
echo "Note: The jodok user is still in the gpio group."
echo "If you want to remove it, run: sudo gpasswd -d jodok gpio"
