#!/usr/bin/env python3

import time
import signal
import sys
import os
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
GPIO_PIN = 23
HOST = "0.0.0.0"
PORT = 8080


class GarageOpenerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/open":
            self.handle_open_command()
        else:
            self.send_error(404, "Not Found")

    def handle_open_command(self):
        """Handle the /open command to trigger garage opening"""
        try:
            logger.info("Received garage open command")

            # Set GPIO mode and pin
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(GPIO_PIN, GPIO.OUT)

            # Set pin LOW to trigger the garage opener
            GPIO.output(GPIO_PIN, GPIO.LOW)

            # Wait for 250ms
            time.sleep(0.25)

            # Set pin HIGH
            GPIO.output(GPIO_PIN, GPIO.HIGH)

            # Clean up GPIO
            GPIO.cleanup()

            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response = {
                "status": "success",
                "message": "Garage opening command sent",
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(response).encode())

            logger.info("Garage open command executed successfully")

        except Exception as e:
            logger.error(f"Error executing garage open command: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

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
        server = HTTPServer((HOST, PORT), GarageOpenerHandler)
        logger.info(f"Starting garage opener server on {HOST}:{PORT}")
        logger.info("Available endpoints:")
        logger.info("  GET /open   - Trigger garage opening")

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
