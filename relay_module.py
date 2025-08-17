#!/usr/bin/env python3

import time
import signal
import sys
import os
import hashlib
import hmac
import RPi.GPIO as GPIO
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging for systemd
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Configuration
SUPPORTED_GPIO_PINS = [23, 18]  # Supported GPIO pins for relay control
HOST = "0.0.0.0"
PORT = 8080
AUTHORIZATION_SECRET = os.environ.get(
    "RELAY_SECRET", "default_secret_change_me"
)  # Set via .env file or environment variable
PULSE_DURATION = 0.25  # Duration in seconds to keep GPIO LOW


class RelayModuleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for relay control"""
        if self.path == "/relay/trigger":
            self.handle_relay_trigger()
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        """Handle GET requests for status, health checks, and documentation"""
        if self.path == "/system/health":
            self.handle_health_check()
        elif self.path == "/system/status":
            self.handle_status()
        elif self.path == "/docs" or self.path == "/":
            self.handle_documentation()
        else:
            self.send_error(404, "Not Found")

    def verify_authorization(self):
        """Verify the authorization hash in the request header"""
        auth_header = self.headers.get("Authorization")
        if not auth_header:
            return False

        try:
            # Expected format: "Bearer <hash>"
            if not auth_header.startswith("Bearer "):
                return False

            provided_hash = auth_header[7:]  # Remove "Bearer " prefix

            # Get request body for hash verification
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            # Calculate expected hash
            expected_hash = hmac.new(
                AUTHORIZATION_SECRET.encode(), body.encode(), hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(provided_hash, expected_hash)

        except Exception as e:
            logger.error(f"Authorization verification error: {e}")
            return False

    def handle_relay_trigger(self):
        """Handle relay trigger requests"""
        try:
            # Verify authorization
            if not self.verify_authorization():
                self.send_response(401)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "status": "error",
                    "message": "Unauthorized - Invalid or missing authorization hash",
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(response).encode())
                return

            # Parse request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON in request body")
                return

            # Validate GPIO pin
            gpio_pin = data.get("gpio_pin")
            if not gpio_pin or gpio_pin not in SUPPORTED_GPIO_PINS:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "status": "error",
                    "message": f"Invalid GPIO pin. Supported pins: {SUPPORTED_GPIO_PINS}",
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(response).encode())
                return

            logger.info(f"Received relay trigger command for GPIO {gpio_pin}")

            # Set GPIO mode and pin
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(gpio_pin, GPIO.OUT)

            # Set pin LOW to trigger the relay
            GPIO.output(gpio_pin, GPIO.LOW)

            # Wait for specified duration
            time.sleep(PULSE_DURATION)

            # Set pin HIGH
            GPIO.output(gpio_pin, GPIO.HIGH)

            # Clean up GPIO
            GPIO.cleanup()

            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response = {
                "status": "success",
                "message": f"Relay triggered on GPIO {gpio_pin}",
                "gpio_pin": gpio_pin,
                "pulse_duration": PULSE_DURATION,
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(response).encode())

            logger.info(f"Relay trigger executed successfully on GPIO {gpio_pin}")

        except Exception as e:
            logger.error(f"Error executing relay trigger: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def handle_health_check(self):
        """Handle health check requests"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "status": "healthy",
            "service": "raspberry-pi-relay-module",
            "timestamp": datetime.now().isoformat(),
        }
        self.wfile.write(json.dumps(response).encode())

    def handle_status(self):
        """Handle status requests"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "status": "running",
            "service": "raspberry-pi-relay-module",
            "supported_gpio_pins": SUPPORTED_GPIO_PINS,
            "pulse_duration": PULSE_DURATION,
            "timestamp": datetime.now().isoformat(),
        }
        self.wfile.write(json.dumps(response).encode())

    def handle_documentation(self):
        """Handle documentation requests"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raspberry Pi Relay Module API</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .endpoint {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .method {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            margin-right: 10px;
        }}
        .post {{ background-color: #61affe; }}
        .get {{ background-color: #49cc90; }}
        .endpoint-url {{
            font-family: monospace;
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .description {{
            color: #666;
            margin: 10px 0;
        }}
        .example {{
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            font-family: monospace;
            white-space: pre-wrap;
        }}
        .auth-note {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
        }}
        .test-section {{
            background-color: #e8f5e8;
            border: 1px solid #c3e6c3;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
        }}
        .test-button {{
            background-color: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }}
        .test-button:hover {{
            background-color: #218838;
        }}
        .response {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔌 Raspberry Pi Relay Module API</h1>
        <p>Lightweight REST API for controlling relay modules via GPIO pins</p>
        <p><strong>Version:</strong> 1.0 | <strong>Status:</strong> <span id="status">Checking...</span></p>
    </div>

    <div class="auth-note">
        <h3>🔐 Authentication</h3>
        <p>All relay operations require HMAC-SHA256 authorization. The hash is calculated from the request body using the <code>RELAY_SECRET</code> environment variable.</p>
        <p><strong>Header format:</strong> <code>Authorization: Bearer &lt;hmac-sha256-hash&gt;</code></p>
    </div>

    <div class="endpoint">
        <h2><span class="method post">POST</span> /relay/trigger</h2>
        <div class="endpoint-url">POST http://localhost:8080/relay/trigger</div>
        <div class="description">Triggers a relay on the specified GPIO pin for a short duration.</div>

        <h4>Request Body:</h4>
        <div class="example">{{
  "gpio_pin": 23
}}</div>

        <h4>Headers:</h4>
        <div class="example">Content-Type: application/json
Authorization: Bearer &lt;hmac-sha256-hash&gt;</div>

        <h4>Response:</h4>
        <div class="example">{{
  "status": "success",
  "message": "Relay triggered on GPIO 23",
  "gpio_pin": 23,
  "pulse_duration": 0.25,
  "timestamp": "2024-01-15T10:30:00.123456"
}}</div>

        <div class="test-section">
            <h4>Test Relay Trigger:</h4>
            <button class="test-button" onclick="testRelay(23)">Test GPIO 23</button>
            <button class="test-button" onclick="testRelay(18)">Test GPIO 18</button>
            <div id="relay-response" class="response"></div>
        </div>
    </div>

    <div class="endpoint">
        <h2><span class="method get">GET</span> /system/health</h2>
        <div class="endpoint-url">GET http://localhost:8080/system/health</div>
        <div class="description">Check the health status of the service.</div>

        <h4>Response:</h4>
        <div class="example">{{
  "status": "healthy",
  "service": "raspberry-pi-relay-module",
  "timestamp": "2024-01-15T10:30:00.123456"
}}</div>

        <div class="test-section">
            <button class="test-button" onclick="testHealth()">Test Health Check</button>
            <div id="health-response" class="response"></div>
        </div>
    </div>

    <div class="endpoint">
        <h2><span class="method get">GET</span> /system/status</h2>
        <div class="endpoint-url">GET http://localhost:8080/system/status</div>
        <div class="description">Get the current status and configuration of the service.</div>

        <h4>Response:</h4>
        <div class="example">{{
  "status": "running",
  "service": "raspberry-pi-relay-module",
  "supported_gpio_pins": [23, 18],
  "pulse_duration": 0.25,
  "timestamp": "2024-01-15T10:30:00.123456"
}}</div>

        <div class="test-section">
            <button class="test-button" onclick="testStatus()">Test Status</button>
            <div id="status-response" class="response"></div>
        </div>
    </div>

    <script>
        // Check service status on page load
        window.onload = function() {{
            testHealth();
        }};

        function testHealth() {{
            fetch('/system/health')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('status').style.color = data.status === 'healthy' ? '#28a745' : '#dc3545';
                    document.getElementById('health-response').textContent = JSON.stringify(data, null, 2);
                }})
                .catch(error => {{
                    document.getElementById('status').textContent = 'Error';
                    document.getElementById('status').style.color = '#dc3545';
                    document.getElementById('health-response').textContent = 'Error: ' + error.message;
                }});
        }}

        function testStatus() {{
            fetch('/system/status')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('status-response').textContent = JSON.stringify(data, null, 2);
                }})
                .catch(error => {{
                    document.getElementById('status-response').textContent = 'Error: ' + error.message;
                }});
        }}

        function testRelay(gpioPin) {{
            const data = {{ gpio_pin: gpioPin }};
            const body = JSON.stringify(data);

            // Note: This is a demo - in real usage, you'd need to generate the HMAC hash
            document.getElementById('relay-response').textContent =
                'Demo: This would trigger GPIO ' + gpioPin + '\\n' +
                'In real usage, you need to generate an HMAC-SHA256 hash of the request body\\n' +
                'using the RELAY_SECRET and include it in the Authorization header.\\n\\n' +
                'Request body: ' + body;
        }}
    </script>
</body>
</html>
        """

        self.wfile.write(html_content.encode())

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger.info(f"{self.address_string()} - {format % args}")


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, stopping server...")
    sys.exit(0)


def main():
    """Main function to start the HTTP server"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Create and start the server
        server = HTTPServer((HOST, PORT), RelayModuleHandler)
        logger.info(f"Starting Raspberry Pi relay module server on {HOST}:{PORT}")
        logger.info("Available endpoints:")
        logger.info("  POST /relay/trigger - Trigger relay on specified GPIO pin")
        logger.info("  GET  /system/health - Health check endpoint")
        logger.info("  GET  /system/status - Service status and configuration")
        logger.info("  GET  /docs          - Interactive API documentation")
        logger.info(f"Supported GPIO pins: {SUPPORTED_GPIO_PINS}")
        logger.info(f"Pulse duration: {PULSE_DURATION}s")
        logger.info("Set RELAY_SECRET in .env file for authorization")

        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        # Clean up GPIO on exit
        try:
            GPIO.cleanup()
        except:
            pass
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    main()
