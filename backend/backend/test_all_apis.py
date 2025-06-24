import requests
import json
import sys

BASE_URL = "http://localhost:5000"

HEADERS = {"Content-Type": "application/json"}
JWT_TOKEN = None

def get_jwt_token():
    url = f"{BASE_URL}/api/auth/login"
    data = {"email": "admin@emailautomation.com", "password": "admin123"}
    print(f"Logging in to get JWT token: {url}")
    response = requests.post(url, json=data, headers=HEADERS)
    print(f"Login status: {response.status_code}")
    print(f"Login response: {response.text}")
    if response.status_code == 200:
        token = response.json().get("access_token")
        return token
    return None

def test_endpoint(method, endpoint, data=None, expected_status=200, headers=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*50}")
    print(f"Testing {method} {endpoint}")
    print(f"URL: {url}")
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")
    if headers:
        print(f"Headers: {headers}")
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return False
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:400]}...")
        return response.status_code == expected_status
    except Exception as e:
        print(f"Error testing {endpoint}: {str(e)}")
        return False

def main():
    print("Starting ADVANCED API Tests...")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Python version: {sys.version}")
    print(f"Requests version: {requests.__version__}")

    global JWT_TOKEN
    JWT_TOKEN = get_jwt_token()
    if not JWT_TOKEN:
        print("Failed to get JWT token. Exiting tests.")
        return
    auth_headers = {"Content-Type": "application/json", "Authorization": f"Bearer {JWT_TOKEN}"}

    # 1. List all email accounts
    test_endpoint("GET", "/api/settings/email-accounts", headers=auth_headers)

    # 2. Add a new email account (mock data)
    test_endpoint("POST", "/api/settings/email-accounts", data={
        "email": "apitest@example.com",
        "password": "testpass",
        "imap_server": "imap.example.com",
        "imap_port": 993,
        "account_type": "hostinger"
    }, headers=auth_headers)

    # 3. Update email account status (deactivate)
    test_endpoint("PUT", "/api/settings/email-accounts/apitest@example.com/update", data={
        "is_active": False
    }, headers=auth_headers)

    # 4. Update email account status (activate)
    test_endpoint("PUT", "/api/settings/email-accounts/apitest@example.com/update", data={
        "is_active": True
    }, headers=auth_headers)

    # 5. Test connection to a specific email account
    test_endpoint("POST", "/api/settings/email-accounts/apitest@example.com/test", headers=auth_headers)

    # 6. Test connection to all email accounts
    test_endpoint("POST", "/api/settings/email-accounts/test-all", headers=auth_headers)

    # 7. Delete the test email account
    test_endpoint("DELETE", "/api/settings/email-accounts/apitest@example.com", headers=auth_headers)

    # 8. Get reply accounts (active only)
    test_endpoint("GET", "/api/replies/accounts", headers=auth_headers)

    # 9. Admin: Update user status (mock user_id)
    test_endpoint("PUT", "/api/admin/users/1/status", data={"is_active": False}, headers=auth_headers)
    test_endpoint("PUT", "/api/admin/users/1/status", data={"is_active": True}, headers=auth_headers)

    # 10. Admin: Get system status
    test_endpoint("GET", "/api/admin/system/status", headers=auth_headers)

    print("\nADVANCED API Tests Completed!")
    print("=" * 50)

if __name__ == "__main__":
    main() 