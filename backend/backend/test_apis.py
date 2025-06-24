import requests
import json

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        print(f"\nTesting {method} {endpoint}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing {endpoint}: {str(e)}")
        return False

def main():
    print("Starting API Tests...")
    
    # Test Auth APIs
    print("\n=== Testing Auth APIs ===")
    test_endpoint("/api/auth/test")
    test_endpoint("/api/auth/login", "POST", {
        "email": "test@example.com",
        "password": "test123"
    })
    
    # Test Email APIs
    print("\n=== Testing Email APIs ===")
    test_endpoint("/api/emails/test")
    test_endpoint("/api/emails/stats")
    
    # Test Admin APIs
    print("\n=== Testing Admin APIs ===")
    test_endpoint("/api/admin/test")
    
    # Test Settings APIs
    print("\n=== Testing Settings APIs ===")
    test_endpoint("/api/settings/test")
    
    # Test Notification APIs
    print("\n=== Testing Notification APIs ===")
    test_endpoint("/api/notifications/test")
    
    # Test Reply APIs
    print("\n=== Testing Reply APIs ===")
    test_endpoint("/api/replies/test")
    
    # Test Health Check
    print("\n=== Testing Health Check ===")
    test_endpoint("/api/health")

if __name__ == "__main__":
    main() 