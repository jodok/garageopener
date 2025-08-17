# Raspberry Pi Relay Module

A lightweight Python HTTP daemon for controlling relay modules via HTTP commands on a Raspberry Pi. This version uses only standard Python libraries and is optimized for older Raspberry Pi models (1st generation and similar).

## Features

- **Ultra-lightweight**: Uses only standard Python libraries (no Flask)
- **HTTP server** listening on port 8080
- **REST API endpoints** for relay control
- **Support for multiple GPIO pins** (23, 28)
- **HMAC-SHA256 authorization** for security
- **Health check and status endpoints**
- **Interactive HTML documentation** (built-in, no external dependencies)
- **Automatic systemd service management**
- **Systemd journal logging**
- **Environment configuration** with `.env` file
- **Random secret generation** during installation

## Why Lightweight?

This version is specifically designed for:

- **Raspberry Pi 1st generation** (ARMv6, 700MHz)
- **Limited memory** systems (512MB RAM)
- **Slow storage** (SD cards)
- **Minimal resource usage**

### Performance Benefits

- **Dependencies**: Only python-dotenv (vs Flask + Flask-RESTX + python-dotenv)
- **Installation time**: 1-2 minutes (vs 5-10 minutes for Flask)
- **Memory usage**: ~10-20MB (vs ~50-100MB for Flask)
- **CPU usage**: Much lower overhead
- **Documentation**: Built-in HTML (no external dependencies)

## Prerequisites

- Raspberry Pi (tested on Raspberry Pi OS)
- Python 3.6+
- User `jodok` (assumed to exist)
- Git repository cloned to desired location
- Run installation script with `sudo` from the repository directory
- Internet connection for installing Python dependencies
- OpenSSL (for generating random secrets)

## Installation

1. **Clone this repository to your Raspberry Pi:**

   ```bash
   cd ~/sandbox
   git clone <repository-url> raspberry-pi-relay-module
   cd raspberry-pi-relay-module
   ```

2. **Make the installation script executable and run it:**

   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

The installation script will:

- Install system dependencies (`python3-rpi.gpio`, `python3-pip`, `python3-venv`)
- Create a Python virtual environment (`venv/`)
- Install Python dependencies (python-dotenv only) in the virtual environment
- Generate a random authorization secret
- Create a `.env` file with the secret and configuration
- Use files from the current directory (git checkout)
- Add user `jodok` to the `gpio` group (uses existing system udev rules)
- Install and enable the systemd service
- Start the service automatically
- Set up systemd logging

## API Endpoints

### POST `/relay/trigger`

Triggers a relay on the specified GPIO pin.

**Request Body:**

```json
{
  "gpio_pin": 23
}
```

**Headers:**

```
Content-Type: application/json
Authorization: Bearer <hmac-sha256-hash>
```

**Response:**

```json
{
  "status": "success",
  "message": "Relay triggered on GPIO 23",
  "gpio_pin": 23,
  "pulse_duration": 0.25,
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### GET `/system/health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "service": "raspberry-pi-relay-module",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### GET `/system/status`

Service status and configuration information.

**Response:**

```json
{
  "status": "running",
  "service": "raspberry-pi-relay-module",
  "supported_gpio_pins": [23, 28],
  "pulse_duration": 0.25,
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### GET `/docs`

Interactive HTML API documentation. Visit this endpoint in your web browser to explore the API interactively.

## Usage

### Environment Configuration

The service uses a `.env` file for configuration. During installation, a random authorization secret is generated and stored in this file.

**Important**: Keep your `.env` file secure and never commit it to version control.

#### Manual Configuration

If you need to customize the configuration:

```bash
# Copy the template
cp .env.template .env

# Edit the configuration
nano .env
```

#### Available Configuration Options

```bash
# Required: Authorization secret for API access
RELAY_SECRET=your_secure_secret_here

# Optional: Override default configuration
HOST=0.0.0.0
PORT=8080
PULSE_DURATION=0.25
```

#### Regenerating the Secret

To generate a new random secret:

```bash
# Generate new secret
openssl rand -hex 32

# Update .env file
nano .env
```

### Example API Calls

```bash
# Health check
curl http://localhost:8080/system/health

# Get status
curl http://localhost:8080/system/status

# View documentation (in browser)
# http://localhost:8080/docs

# Trigger relay on GPIO 23 (requires proper authorization)
curl -X POST http://localhost:8080/relay/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <generated-hash>" \
  -d '{"gpio_pin": 23}'
```

### Using the Test Script

The included test script automatically reads the secret from the `.env` file:

```bash
# Install requests if not already installed
pip3 install requests

# Run the test (uses .env file automatically)
python3 test_relay_api.py
```

## Authorization

The API uses HMAC-SHA256 for authorization. The hash is calculated from the request body using the secret key.

**Python example:**

```python
import hashlib
import hmac
import json

secret = "your_secure_secret_here"
data = {"gpio_pin": 23}
body = json.dumps(data)

auth_hash = hmac.new(
    secret.encode(),
    body.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {auth_hash}"
}
```

## Service Management

```bash
# Check service status
sudo systemctl status relay-module.service

# Start the service
sudo systemctl start relay-module.service

# Stop the service
sudo systemctl stop relay-module.service

# Restart the service
sudo systemctl restart relay-module.service

# View logs in real-time
sudo journalctl -u relay-module.service -f

# View recent logs
sudo journalctl -u relay-module.service -n 50
```

## Virtual Environment

The service uses a Python virtual environment to manage dependencies:

- **System packages**: `python3-rpi.gpio` is installed system-wide via apt (required for GPIO access)
- **Application packages**: Only python-dotenv is installed in the virtual environment
- **Location**: Virtual environment is created in `venv/` directory
- **Service**: Systemd service automatically uses the virtual environment's Python interpreter

### Manual Virtual Environment Management

If you need to work with the virtual environment manually:

```bash
# Activate the virtual environment
source venv/bin/activate

# Install additional packages
pip install package_name

# Run the application directly
python relay_module_light.py

# Deactivate when done
deactivate
```

## Configuration

### Supported GPIO Pins

The service supports GPIO pins 23 and 28 by default. To modify this, edit the `SUPPORTED_GPIO_PINS` list in `relay_module.py`.

### Pulse Duration

The relay is triggered by setting the GPIO pin LOW for 250ms by default. To change this, edit the `PULSE_DURATION` variable in `relay_module.py`.

### Port

The service runs on port 8080 by default. To change this, edit the `PORT` variable in `relay_module.py`.

### Authorization Secret

Set the `RELAY_SECRET` environment variable in the `.env` file for production use.

## Hardware Setup

1. Connect your relay modules to GPIO pins 23 and 28
2. Ensure proper grounding and power supply
3. Test the connections before running the service
4. The relay is triggered by setting the GPIO pin LOW for 250ms

## Security Considerations

⚠️ **Important Security Notes:**

- The service uses HMAC-SHA256 authorization for API access
- Set a strong `RELAY_SECRET` in production
- The HTTP server listens on all interfaces (0.0.0.0)
- Consider implementing:
  - Firewall rules to restrict access
  - HTTPS for encrypted communication
  - Rate limiting

### Security Best Practices

1. **Set a strong secret:**

   ```bash
   # Generate a secure random secret
   openssl rand -hex 32
   ```

2. **Restrict network access:**

   ```bash
   # Allow only local network access
   sudo ufw allow from 192.168.1.0/24 to any port 8080
   sudo ufw deny 8080
   ```

3. **Use HTTPS in production** (requires additional setup with reverse proxy)

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status relay-module-light.service

# View detailed logs
sudo journalctl -u relay-module-light.service -n 50

# Check if port is already in use
sudo netstat -tlnp | grep 8080
```

### GPIO errors

```bash
# Check if RPi.GPIO is installed system-wide
python3 -c "import RPi.GPIO; print('GPIO module available')"

# Check if virtual environment can access GPIO
./venv/bin/python -c "import RPi.GPIO; print('GPIO module available in venv')"

# Check GPIO permissions
ls -la /dev/gpiomem
```

### Authorization errors

```bash
# Check if .env file exists
ls -la .env

# Check if RELAY_SECRET is set in .env
grep RELAY_SECRET .env

# Test if the secret is being loaded correctly
./venv/bin/python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Secret:', os.environ.get('RELAY_SECRET', 'NOT_FOUND'))"
```

### Network connectivity issues

```bash
# Check if service is listening
sudo netstat -tlnp | grep 8080

# Test local connectivity
curl http://localhost:8080/system/health

# Check firewall
sudo ufw status
```

### Virtual environment issues

```bash
# Check if virtual environment exists
ls -la venv/

# Recreate virtual environment if needed
rm -rf venv/
python3 -m venv venv
./venv/bin/pip install -r requirements_light.txt

# Check if service can access virtual environment
sudo systemctl status relay-module-light.service
```

## Uninstallation

To remove the service:

```bash
chmod +x uninstall.sh
sudo ./uninstall.sh
```

## Files

- `relay_module.py` - Main lightweight HTTP server and GPIO control with built-in documentation
- `relay-module.service` - Systemd service definition
- `install.sh` - Installation script
- `uninstall.sh` - Uninstallation script
- `test_relay_api.py` - API testing script with authorization examples
- `requirements.txt` - Minimal Python dependencies for virtual environment
- `.env.template` - Template for environment configuration
- `.env` - Environment configuration (created during installation)
- `venv/` - Python virtual environment (created during installation)

## Performance Benefits

### Memory Usage

- **Current version**: ~10-20MB RAM (optimized for Raspberry Pi 1st gen)

### Installation Time

- **Current version**: 1-2 minutes (minimal dependencies)

### Dependencies

- **Current version**: 1 package (python-dotenv only)

### Documentation

- **Current version**: Built-in HTML (no external dependencies)

## License

This project is open source. Feel free to modify and distribute.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
