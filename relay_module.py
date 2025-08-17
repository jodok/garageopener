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
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields, Namespace
from functools import wraps

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

# Initialize Flask app
app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="Raspberry Pi Relay Module API",
    description="A REST API for controlling relay modules connected to Raspberry Pi GPIO pins",
    doc="/docs",
    authorizations={
        "apikey": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "HMAC-SHA256 hash of request body using RELAY_SECRET",
        }
    },
    security="apikey",
)

# Create namespaces
relay_ns = Namespace("relay", description="Relay control operations")
system_ns = Namespace("system", description="System status and health operations")

api.add_namespace(relay_ns)
api.add_namespace(system_ns)

# Define models for Swagger documentation
relay_trigger_model = api.model(
    "RelayTrigger",
    {
        "gpio_pin": fields.Integer(
            required=True,
            description="GPIO pin number to trigger",
            example=23,
            enum=SUPPORTED_GPIO_PINS,
        )
    },
)

success_response_model = api.model(
    "SuccessResponse",
    {
        "status": fields.String(description="Response status", example="success"),
        "message": fields.String(description="Response message"),
        "gpio_pin": fields.Integer(description="GPIO pin that was triggered"),
        "pulse_duration": fields.Float(description="Duration of the pulse in seconds"),
        "timestamp": fields.String(description="ISO timestamp of the operation"),
    },
)

error_response_model = api.model(
    "ErrorResponse",
    {
        "status": fields.String(description="Response status", example="error"),
        "message": fields.String(description="Error message"),
        "timestamp": fields.String(description="ISO timestamp of the error"),
    },
)

health_response_model = api.model(
    "HealthResponse",
    {
        "status": fields.String(description="Health status", example="healthy"),
        "service": fields.String(description="Service name"),
        "timestamp": fields.String(description="ISO timestamp"),
    },
)

status_response_model = api.model(
    "StatusResponse",
    {
        "status": fields.String(description="Service status", example="running"),
        "service": fields.String(description="Service name"),
        "supported_gpio_pins": fields.List(
            fields.Integer, description="List of supported GPIO pins"
        ),
        "pulse_duration": fields.Float(description="Default pulse duration in seconds"),
        "timestamp": fields.String(description="ISO timestamp"),
    },
)


def verify_authorization(f):
    """Decorator to verify authorization hash"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {
                "status": "error",
                "message": "Unauthorized - Missing authorization header",
                "timestamp": datetime.now().isoformat(),
            }, 401

        try:
            # Expected format: "Bearer <hash>"
            if not auth_header.startswith("Bearer "):
                return {
                    "status": "error",
                    "message": "Unauthorized - Invalid authorization format",
                    "timestamp": datetime.now().isoformat(),
                }, 401

            provided_hash = auth_header[7:]  # Remove "Bearer " prefix

            # Get request body for hash verification
            body = request.get_data(as_text=True)

            # Calculate expected hash
            expected_hash = hmac.new(
                AUTHORIZATION_SECRET.encode(), body.encode(), hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(provided_hash, expected_hash):
                return {
                    "status": "error",
                    "message": "Unauthorized - Invalid authorization hash",
                    "timestamp": datetime.now().isoformat(),
                }, 401

            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"Authorization verification error: {e}")
            return {
                "status": "error",
                "message": "Unauthorized - Authorization verification failed",
                "timestamp": datetime.now().isoformat(),
            }, 401

    return decorated_function


@relay_ns.route("/trigger")
class RelayTrigger(Resource):
    @relay_ns.doc(
        "trigger_relay",
        security="apikey",
        responses={
            200: ("Relay triggered successfully", success_response_model),
            400: ("Bad request", error_response_model),
            401: ("Unauthorized", error_response_model),
            500: ("Internal server error", error_response_model),
        },
    )
    @relay_ns.expect(relay_trigger_model)
    @verify_authorization
    def post(self):
        """Trigger a relay on the specified GPIO pin"""
        try:
            data = request.get_json()

            if not data:
                return {
                    "status": "error",
                    "message": "Request body is required",
                    "timestamp": datetime.now().isoformat(),
                }, 400

            # Validate GPIO pin
            gpio_pin = data.get("gpio_pin")
            if not gpio_pin or gpio_pin not in SUPPORTED_GPIO_PINS:
                return {
                    "status": "error",
                    "message": f"Invalid GPIO pin. Supported pins: {SUPPORTED_GPIO_PINS}",
                    "timestamp": datetime.now().isoformat(),
                }, 400

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

            response = {
                "status": "success",
                "message": f"Relay triggered on GPIO {gpio_pin}",
                "gpio_pin": gpio_pin,
                "pulse_duration": PULSE_DURATION,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Relay trigger executed successfully on GPIO {gpio_pin}")
            return response, 200

        except Exception as e:
            logger.error(f"Error executing relay trigger: {e}")
            return {
                "status": "error",
                "message": f"Internal Server Error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }, 500


@system_ns.route("/health")
class HealthCheck(Resource):
    @system_ns.doc(
        "health_check", responses={200: ("Service is healthy", health_response_model)}
    )
    def get(self):
        """Check the health status of the service"""
        response = {
            "status": "healthy",
            "service": "raspberry-pi-relay-module",
            "timestamp": datetime.now().isoformat(),
        }
        return response, 200


@system_ns.route("/status")
class Status(Resource):
    @system_ns.doc(
        "get_status",
        responses={200: ("Service status retrieved", status_response_model)},
    )
    def get(self):
        """Get the current status and configuration of the service"""
        response = {
            "status": "running",
            "service": "raspberry-pi-relay-module",
            "supported_gpio_pins": SUPPORTED_GPIO_PINS,
            "pulse_duration": PULSE_DURATION,
            "timestamp": datetime.now().isoformat(),
        }
        return response, 200


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, stopping server...")
    sys.exit(0)


def main():
    """Main function to start the Flask server"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info(f"Starting Raspberry Pi relay module server on {HOST}:{PORT}")
        logger.info("Available endpoints:")
        logger.info("  POST /relay/trigger - Trigger relay on specified GPIO pin")
        logger.info("  GET  /system/health - Health check endpoint")
        logger.info("  GET  /system/status - Service status and configuration")
        logger.info("  GET  /docs          - Swagger API documentation")
        logger.info(f"Supported GPIO pins: {SUPPORTED_GPIO_PINS}")
        logger.info(f"Pulse duration: {PULSE_DURATION}s")
        logger.info("Set RELAY_SECRET environment variable for authorization")

        app.run(host=HOST, port=PORT, debug=False)

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
