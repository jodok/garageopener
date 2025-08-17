#!/usr/bin/env python3

import requests
import time
import sys


def test_garage_service():
    """Test the garage opener service endpoints"""

    base_url = "http://localhost:8080"

    print("=== Garage Opener Service Test ===")

    # Test 1: Check if service is running
    print("\n1. Testing service availability...")
    try:
        response = requests.get(f"{base_url}/open", timeout=5)
        if response.status_code == 200:
            print("✅ Service is running and responding")
            data = response.json()
            print(f"   Response: {data.get('message', 'No message')}")
        else:
            print(f"❌ Service returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to service. Is it running?")
        print("   Try: sudo systemctl status garage-opener.service")
        return False
    except Exception as e:
        print(f"❌ Error testing service: {e}")
        return False

    # Test 2: Test invalid endpoint
    print("\n2. Testing invalid endpoint...")
    try:
        response = requests.get(f"{base_url}/invalid", timeout=5)
        if response.status_code == 404:
            print("✅ Invalid endpoint correctly returns 404")
        else:
            print(
                f"❌ Invalid endpoint returned unexpected status: {response.status_code}"
            )
    except Exception as e:
        print(f"❌ Error testing invalid endpoint: {e}")

    print("\n=== Test Complete ===")
    print("If all tests passed, your garage opener service is working correctly!")
    return True


if __name__ == "__main__":
    success = test_garage_service()
    sys.exit(0 if success else 1)
