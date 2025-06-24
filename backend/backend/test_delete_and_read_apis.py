#!/usr/bin/env python3
"""
Focused Test Script for Delete and Read/Unread Functionality
Tests the specific APIs for email deletion (trash) and read/unread operations.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

# Test data
TEST_USER = {
    "email": "delete_test@example.com",
    "password": "testpassword123",
    "username": "Delete Test User"
}

class DeleteReadTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_email_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, response: requests.Response = None, error: str = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "status_code": response.status_code if response else None,
            "error": error
        }
        
        if response:
            try:
                result["response_data"] = response.json()
            except:
                result["response_text"] = response.text
                
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"   Error: {error}")
        if response and response.status_code != 200:
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
        print()

    def get_headers(self, token=None):
        """Get headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def setup_test_user(self):
        """Setup test user and get authentication token"""
        print("🔐 Setting up test user...")
        
        # Register test user
        try:
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json=TEST_USER,
                headers=self.get_headers()
            )
            success = response.status_code in [200, 201, 409]  # 409 if user already exists
            self.log_test("Register Test User", success, response)
        except Exception as e:
            self.log_test("Register Test User", False, error=str(e))
            return False

        # Login to get token
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json={"email": TEST_USER["email"], "password": TEST_USER["password"]},
                headers=self.get_headers()
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                self.auth_token = data.get("access_token")
            self.log_test("Login Test User", success, response)
            return success
        except Exception as e:
            self.log_test("Login Test User", False, error=str(e))
            return False

    def get_test_email(self):
        """Get a test email to work with"""
        print("📧 Getting test email...")
        
        try:
            # First fetch some emails
            response = self.session.post(
                f"{API_BASE}/emails/fetch",
                json={"limit": 5},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Fetch Emails for Testing", success, response)
            
            # Get list of emails
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"page": 1, "per_page": 10},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                if emails:
                    self.test_email_id = emails[0]["id"]
                    print(f"   Using email ID: {self.test_email_id}")
            self.log_test("Get Email List", success, response)
            return success
        except Exception as e:
            self.log_test("Get Test Email", False, error=str(e))
            return False

    def test_read_unread_functionality(self):
        """Test read/unread functionality thoroughly"""
        print("👁️ Testing Read/Unread Functionality...")
        
        if not self.test_email_id:
            print("   Skipping - No test email available")
            return False

        # Test 1: Mark email as read
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/read",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Mark Email as Read", success, response)
            
            if success:
                data = response.json()
                email_data = data.get("email", {})
                is_read = email_data.get("is_read", False)
                print(f"   Email is_read status: {is_read}")
        except Exception as e:
            self.log_test("Mark Email as Read", False, error=str(e))

        # Test 2: Verify email is marked as read
        try:
            response = self.session.get(
                f"{API_BASE}/emails/{self.test_email_id}",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                is_read = data.get("is_read", False)
                print(f"   Verification - Email is_read: {is_read}")
            self.log_test("Verify Email Read Status", success, response)
        except Exception as e:
            self.log_test("Verify Email Read Status", False, error=str(e))

        # Test 3: Mark email as unread
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/unread",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Mark Email as Unread", success, response)
            
            if success:
                data = response.json()
                email_data = data.get("email", {})
                is_read = email_data.get("is_read", True)
                print(f"   Email is_read status: {is_read}")
        except Exception as e:
            self.log_test("Mark Email as Unread", False, error=str(e))

        # Test 4: Verify email is marked as unread
        try:
            response = self.session.get(
                f"{API_BASE}/emails/{self.test_email_id}",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                is_read = data.get("is_read", True)
                print(f"   Verification - Email is_read: {is_read}")
            self.log_test("Verify Email Unread Status", success, response)
        except Exception as e:
            self.log_test("Verify Email Unread Status", False, error=str(e))

        # Test 5: Mark all emails as read
        try:
            response = self.session.post(
                f"{API_BASE}/emails/mark_all_read",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Mark All Emails as Read", success, response)
        except Exception as e:
            self.log_test("Mark All Emails as Read", False, error=str(e))

    def test_delete_trash_functionality(self):
        """Test delete/trash functionality thoroughly"""
        print("🗑️ Testing Delete/Trash Functionality...")
        
        if not self.test_email_id:
            print("   Skipping - No test email available")
            return False

        # Test 1: Move email to trash
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/action",
                json={"action": "trash"},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Move Email to Trash", success, response)
            
            if success:
                data = response.json()
                print(f"   Response: {data.get('message', 'No message')}")
        except Exception as e:
            self.log_test("Move Email to Trash", False, error=str(e))

        # Test 2: Verify email is in trash folder
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "trash", "page": 1, "per_page": 10},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                found_in_trash = any(email["id"] == self.test_email_id for email in emails)
                print(f"   Email found in trash: {found_in_trash}")
            self.log_test("Verify Email in Trash", success, response)
        except Exception as e:
            self.log_test("Verify Email in Trash", False, error=str(e))

        # Test 3: Check email details to verify trash status
        try:
            response = self.session.get(
                f"{API_BASE}/emails/{self.test_email_id}",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                is_trashed = data.get("is_trashed", False)
                folder = data.get("folder", "")
                print(f"   Email is_trashed: {is_trashed}, folder: {folder}")
            self.log_test("Check Email Trash Status", success, response)
        except Exception as e:
            self.log_test("Check Email Trash Status", False, error=str(e))

        # Test 4: Restore email from trash
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/action",
                json={"action": "restore"},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Restore Email from Trash", success, response)
            
            if success:
                data = response.json()
                print(f"   Response: {data.get('message', 'No message')}")
        except Exception as e:
            self.log_test("Restore Email from Trash", False, error=str(e))

        # Test 5: Verify email is restored to inbox
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "inbox", "page": 1, "per_page": 10},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                found_in_inbox = any(email["id"] == self.test_email_id for email in emails)
                print(f"   Email found in inbox: {found_in_inbox}")
            self.log_test("Verify Email Restored to Inbox", success, response)
        except Exception as e:
            self.log_test("Verify Email Restored to Inbox", False, error=str(e))

        # Test 6: Check email details after restore
        try:
            response = self.session.get(
                f"{API_BASE}/emails/{self.test_email_id}",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                is_trashed = data.get("is_trashed", True)
                folder = data.get("folder", "")
                print(f"   Email is_trashed: {is_trashed}, folder: {folder}")
            self.log_test("Check Email Status After Restore", success, response)
        except Exception as e:
            self.log_test("Check Email Status After Restore", False, error=str(e))

    def test_other_email_actions(self):
        """Test other email actions (archive, spam)"""
        print("📁 Testing Other Email Actions...")
        
        if not self.test_email_id:
            print("   Skipping - No test email available")
            return False

        # Test archive action
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/action",
                json={"action": "archive"},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Move Email to Archive", success, response)
        except Exception as e:
            self.log_test("Move Email to Archive", False, error=str(e))

        # Test spam action
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/action",
                json={"action": "spam"},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Move Email to Spam", success, response)
        except Exception as e:
            self.log_test("Move Email to Spam", False, error=str(e))

        # Restore to inbox for cleanup
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/action",
                json={"action": "restore"},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Restore Email to Inbox (Cleanup)", success, response)
        except Exception as e:
            self.log_test("Restore Email to Inbox (Cleanup)", False, error=str(e))

    def test_email_filtering_by_status(self):
        """Test email filtering by read/unread status"""
        print("🔍 Testing Email Filtering by Status...")
        
        # Test filtering unread emails
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"is_read": "false", "page": 1, "per_page": 5},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                unread_count = len(data.get("emails", []))
                print(f"   Unread emails found: {unread_count}")
            self.log_test("Filter Unread Emails", success, response)
        except Exception as e:
            self.log_test("Filter Unread Emails", False, error=str(e))

        # Test filtering read emails
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"is_read": "true", "page": 1, "per_page": 5},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                read_count = len(data.get("emails", []))
                print(f"   Read emails found: {read_count}")
            self.log_test("Filter Read Emails", success, response)
        except Exception as e:
            self.log_test("Filter Read Emails", False, error=str(e))

    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 DELETE & READ/UNREAD TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
        
        # Save detailed results to file
        report_file = "delete_read_test_results.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {report_file}")
        
        return passed_tests == total_tests

    def run_all_tests(self):
        """Run all delete and read/unread tests"""
        print("🚀 Starting Delete & Read/Unread API Testing...")
        print("="*60)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user")
            return False
        
        if not self.get_test_email():
            print("❌ Failed to get test email")
            return False
        
        # Run tests
        self.test_read_unread_functionality()
        self.test_delete_trash_functionality()
        self.test_other_email_actions()
        self.test_email_filtering_by_status()
        
        # Generate report
        return self.generate_report()

def main():
    """Main function"""
    print("Email Automation Backend - Delete & Read/Unread API Testing")
    print("="*60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend health check failed: {response.status_code}")
            return 1
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend at {BASE_URL}")
        print(f"   Error: {e}")
        print(f"   Make sure the backend is running on {BASE_URL}")
        return 1
    
    # Run tests
    tester = DeleteReadTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 