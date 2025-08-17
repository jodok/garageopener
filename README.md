# Garage Opener

A Python HTTP daemon for opening a garage door via HTTP commands on a Raspberry Pi.

## Features

- HTTP server listening on port 8080
- `/open` endpoint to trigger garage opening via GPIO pin 23
- Automatic systemd service management
- Systemd journal logging

## Prerequisites

- Raspberry Pi (tested on Raspberry Pi OS)
- Python 3.6+
- User `jodok` (assumed to exist)
- Git repository cloned to desired location
- Run installation script with `sudo` from the repository directory

## Installation

1. **Clone this repository to your Raspberry Pi:**

   ```bash
   cd ~/sandbox
   git clone <repository-url> garage-opener
   cd garage-opener
   ```

2. **Make the installation script executable and run it:**

   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

The installation script will:

- Install required dependencies (`python3-rpi.gpio`)
- Use files from the current directory (git checkout)
- Add user `jodok` to the `gpio` group (uses existing system udev rules)
- Install and enable the systemd service
- Start the service automatically
- Set up systemd logging

## Usage

### HTTP Endpoints

- **GET `/open`** - Triggers garage opening
  - Returns JSON response with status and timestamp
  - Sets GPIO pin 23 LOW for 250ms, then HIGH

### Examples

```bash
# Open the garage
curl http://localhost:8080/open

# From another device on the network
curl http://192.168.1.100:8080/open
```

### Service Management

```bash
# Check service status
sudo systemctl status garage-opener.service

# Start the service
sudo systemctl start garage-opener.service

# Stop the service
sudo systemctl stop garage-opener.service

# Restart the service
sudo systemctl restart garage-opener.service

# View logs in real-time
sudo journalctl -u garage-opener.service -f

# View recent logs
sudo journalctl -u garage-opener.service -n 50


```

## Testing

Run the test script to verify everything is working:

```bash
# Install requests if not already installed
pip3 install requests

# Run the test
python3 test_service.py
```

## Configuration

### GPIO Pin

The service uses GPIO pin 23 by default. To change this, edit the `GPIO_PIN` variable in `garage_opener.py`.

### Port

The service runs on port 8080 by default. To change this, edit the `PORT` variable in `garage_opener.py`.

### Logging

Logs are written to the systemd journal and can be viewed with `journalctl`.

## Hardware Setup

1. Connect your garage door opener relay/switch to GPIO pin 23
2. Ensure proper grounding and power supply
3. Test the connection before running the service

## Security Considerations

⚠️ **Important Security Notes:**

- The service runs as user `jodok` with GPIO access via existing system udev rules
- The HTTP server listens on all interfaces (0.0.0.0)
- No authentication is implemented
- Consider implementing:
  - Firewall rules to restrict access
  - Authentication/authorization
  - HTTPS for encrypted communication

### Basic Security Improvements

1. **Restrict network access:**

   ```bash
   # Allow only local network access
   sudo ufw allow from 192.168.1.0/24 to any port 8080
   sudo ufw deny 8080
   ```

2. **Add basic authentication** (modify the Python code):

   ```python
   # Add to the request handler
   if not self.headers.get('Authorization') == 'Bearer your-secret-token':
       self.send_error(401, "Unauthorized")
       return
   ```

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status garage-opener.service

# View detailed logs
sudo journalctl -u garage-opener.service -n 50

# Check if port is already in use
sudo netstat -tlnp | grep 8080
```

### GPIO errors

```bash
# Check if RPi.GPIO is installed
python3 -c "import RPi.GPIO; print('GPIO module available')"

# Check GPIO permissions
ls -la /dev/gpiomem
```

### Network connectivity issues

```bash
# Check if service is listening
sudo netstat -tlnp | grep 8080

# Test local connectivity
curl http://localhost:8080/status

# Check firewall
sudo ufw status
```

## Uninstallation

To remove the service:

```bash
chmod +x uninstall.sh
sudo ./uninstall.sh
```

## Files

- `garage_opener.py` - Main HTTP server and GPIO control
- `garage-opener.service` - Systemd service definition
- `install.sh` - Installation script
- `uninstall.sh` - Uninstallation script
- `test_service.py` - Service testing script

## License

This project is open source. Feel free to modify and distribute.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
