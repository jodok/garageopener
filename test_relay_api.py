#!/usr/bin/env python3

import requests
import json
import hashlib
import hmac
import os

# Configuration
BASE_URL = "http://localhost:8080"
SECRET = os.environ.get("RELAY_SECRET", "your_secure_secret_here")


def generate_auth_hash(body):
    """Generate HMAC-SHA256 hash for authorization"""
    return hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()


def trigger_relay(gpio_pin):
    """Trigger relay on specified GPIO pin"""
    url = f"{BASE_URL}/relay/trigger"

    # Prepare request body
    data = {"gpio_pin": gpio_pin}
    body = json.dumps(data)

    # Generate authorization hash
    auth_hash = generate_auth_hash(body)

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_hash}",
    }

    try:
        response = requests.post(url, data=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def check_health():
    """Check service health"""
    url = f"{BASE_URL}/system/health"
    try:
        response = requests.get(url)
        print(f"Health Check - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check error: {e}")
        return False


def get_status():
    """Get service status"""
    url = f"{BASE_URL}/system/status"
    try:
        response = requests.get(url)
        print(f"Status Check - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Status check error: {e}")
        return False


def main():
    print("Raspberry Pi Relay Module API Test")
    print("=" * 40)

    # Check health
    print("\n1. Health Check:")
    check_health()

    # Get status
    print("\n2. Service Status:")
    get_status()

    # Test relay triggers
    print("\n3. Testing Relay Triggers:")

    # Test GPIO 23
    print(f"\nTriggering GPIO 23:")
    trigger_relay(23)

    # Test GPIO 28
    print(f"\nTriggering GPIO 28:")
    trigger_relay(28)

    # Test invalid GPIO
    print(f"\nTesting invalid GPIO 99:")
    trigger_relay(99)


if __name__ == "__main__":
    main()
