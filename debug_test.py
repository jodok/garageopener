#!/usr/bin/env python3

import requests
import json
import hashlib
import hmac
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8080"
SECRET = os.environ.get("RELAY_SECRET")
if not SECRET:
    print("❌ RELAY_SECRET not found in .env file or environment variables")
    print("   Please ensure .env file exists with RELAY_SECRET set")
    exit(1)


def test_empty_body():
    """Test with empty request body"""
    print("\n=== Testing Empty Body ===")
    url = f"{BASE_URL}/relay/trigger"

    try:
        response = requests.post(
            url, data="", headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def test_malformed_json():
    """Test with malformed JSON"""
    print("\n=== Testing Malformed JSON ===")
    url = f"{BASE_URL}/relay/trigger"

    try:
        response = requests.post(
            url, data='{"gpio_pin": 23', headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def test_no_content_type():
    """Test without Content-Type header"""
    print("\n=== Testing No Content-Type ===")
    url = f"{BASE_URL}/relay/trigger"

    try:
        response = requests.post(url, data='{"gpio_pin": 23}')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def test_valid_request():
    """Test with valid request"""
    print("\n=== Testing Valid Request ===")
    url = f"{BASE_URL}/relay/trigger"

    # Prepare request body
    data = {"gpio_pin": 23}
    body = json.dumps(data)

    # Generate authorization hash
    auth_hash = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_hash}",
    }

    try:
        response = requests.post(url, data=body, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    print("Raspberry Pi Relay Module Debug Test")
    print("=" * 40)

    test_empty_body()
    test_malformed_json()
    test_no_content_type()
    test_valid_request()


if __name__ == "__main__":
    main()
