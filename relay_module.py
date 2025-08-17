#!/usr/bin/env python3

import time
import signal
import sys
import os
import hashlib
import hmac
from http.server import HTTPServer, BaseHTTPRequestHandler
import RPi.GPIO as GPIO
import json
import logging
from datetime import datetime

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
SUPPORTED_GPIO_PINS = [23, 28]  # Supported GPIO pins for relay control
HOST = "0.0.0.0"
PORT = 8080
AUTHORIZATION_SECRET = os.environ.get(
    "RELAY_SECRET", "default_secret_change_me"
)  # Set via environment variable
PULSE_DURATION = 0.25  # Duration in seconds to keep GPIO LOW


class RelayModuleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for relay control"""
        if self.path == "/relay/trigger":
            self.handle_relay_trigger()
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        """Handle GET requests for status and health checks"""
        if self.path == "/health":
            self.handle_health_check()
        elif self.path == "/status":
            self.handle_status()
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
        logger.info("  GET  /health        - Health check endpoint")
        logger.info("  GET  /status        - Service status and configuration")
        logger.info(f"Supported GPIO pins: {SUPPORTED_GPIO_PINS}")
        logger.info(f"Pulse duration: {PULSE_DURATION}s")
        logger.info("Set RELAY_SECRET environment variable for authorization")

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
