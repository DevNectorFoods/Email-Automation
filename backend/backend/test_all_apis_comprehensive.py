#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Email Automation Backend
Tests all APIs including delete functionality, read/unread operations, and more.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

# Test data
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123",
    "username": "Test User"
}

TEST_ADMIN = {
    "email": "admin@example.com", 
    "password": "adminpass123",
    "username": "Admin User"
}

TEST_EMAIL_ACCOUNT = {
    "email": "apitest@example.com",
    "password": "testpass123",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com", 
    "smtp_port": 587
}

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.admin_token = None
        self.test_results = []
        self.email_ids = []
        
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

    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            success = response.status_code == 200
            self.log_test("Health Check", success, response)
            return success
        except Exception as e:
            self.log_test("Health Check", False, error=str(e))
            return False

    def test_auth_apis(self):
        """Test authentication APIs"""
        print("🔐 Testing Authentication APIs...")
        
        # Test registration
        try:
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json=TEST_USER,
                headers=self.get_headers()
            )
            success = response.status_code in [200, 201, 409]  # 409 if user already exists
            self.log_test("User Registration", success, response)
        except Exception as e:
            self.log_test("User Registration", False, error=str(e))

        # Test admin registration
        try:
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json={**TEST_ADMIN, "role": "admin"},
                headers=self.get_headers()
            )
            success = response.status_code in [200, 201, 409]
            self.log_test("Admin Registration", success, response)
        except Exception as e:
            self.log_test("Admin Registration", False, error=str(e))

        # Test login
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
            self.log_test("User Login", success, response)
        except Exception as e:
            self.log_test("User Login", False, error=str(e))

        # Test admin login
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json={"email": TEST_ADMIN["email"], "password": TEST_ADMIN["password"]},
                headers=self.get_headers()
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                self.admin_token = data.get("access_token")
            self.log_test("Admin Login", success, response)
        except Exception as e:
            self.log_test("Admin Login", False, error=str(e))

        # Test get current user
        if self.auth_token:
            try:
                response = self.session.get(
                    f"{API_BASE}/auth/profile",
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Get Current User", success, response)
            except Exception as e:
                self.log_test("Get Current User", False, error=str(e))

    def test_email_account_apis(self):
        """Test email account management APIs"""
        print("📧 Testing Email Account APIs...")
        
        if not self.admin_token:
            print("   Skipping - No admin token available")
            return

        # Test add email account
        try:
            response = self.session.post(
                f"{API_BASE}/settings/email-accounts",
                json=TEST_EMAIL_ACCOUNT,
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code in [200, 201, 409]  # 409 if account already exists
            self.log_test("Add Email Account", success, response)
        except Exception as e:
            self.log_test("Add Email Account", False, error=str(e))

        # Test get email accounts
        try:
            response = self.session.get(
                f"{API_BASE}/emails/accounts",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get Email Accounts", success, response)
        except Exception as e:
            self.log_test("Get Email Accounts", False, error=str(e))

        # Test test account connectivity
        try:
            response = self.session.post(
                f"{API_BASE}/emails/accounts/test",
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            self.log_test("Test Account Connectivity", success, response)
        except Exception as e:
            self.log_test("Test Account Connectivity", False, error=str(e))

    def test_email_fetch_and_listing(self):
        """Test email fetching and listing APIs"""
        print("📥 Testing Email Fetch & Listing APIs...")
        
        if not self.auth_token:
            print("   Skipping - No auth token available")
            return

        # Test fetch emails
        try:
            response = self.session.post(
                f"{API_BASE}/emails/fetch",
                json={"limit": 10},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Fetch Emails", success, response)
        except Exception as e:
            self.log_test("Fetch Emails", False, error=str(e))

        # Test list emails
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"page": 1, "per_page": 10},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                self.email_ids = [email["id"] for email in emails[:3]]  # Store first 3 email IDs for testing
            self.log_test("List Emails", success, response)
        except Exception as e:
            self.log_test("List Emails", False, error=str(e))

        # Test get email stats
        try:
            response = self.session.get(
                f"{API_BASE}/emails/stats",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get Email Stats", success, response)
        except Exception as e:
            self.log_test("Get Email Stats", False, error=str(e))

    def test_read_unread_apis(self):
        """Test read/unread functionality"""
        print("👁️ Testing Read/Unread APIs...")
        
        if not self.auth_token or not self.email_ids:
            print("   Skipping - No auth token or email IDs available")
            return

        email_id = self.email_ids[0] if self.email_ids else None
        
        if email_id:
            # Test mark email as read
            try:
                response = self.session.post(
                    f"{API_BASE}/emails/{email_id}/read",
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Mark Email as Read", success, response)
            except Exception as e:
                self.log_test("Mark Email as Read", False, error=str(e))

            # Test mark email as unread
            try:
                response = self.session.post(
                    f"{API_BASE}/emails/{email_id}/unread",
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Mark Email as Unread", success, response)
            except Exception as e:
                self.log_test("Mark Email as Unread", False, error=str(e))

            # Test mark all emails as read
            try:
                response = self.session.post(
                    f"{API_BASE}/emails/mark_all_read",
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Mark All Emails as Read", success, response)
            except Exception as e:
                self.log_test("Mark All Emails as Read", False, error=str(e))

    def test_email_actions(self):
        """Test email actions including delete/trash functionality"""
        print("🗑️ Testing Email Actions (Delete/Trash)...")
        
        if not self.auth_token or not self.email_ids:
            print("   Skipping - No auth token or email IDs available")
            return

        email_id = self.email_ids[0] if self.email_ids else None
        
        if email_id:
            # Test move email to trash
            try:
                response = self.session.post(
                    f"{API_BASE}/emails/{email_id}/action",
                    json={"action": "trash"},
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Move Email to Trash", success, response)
            except Exception as e:
                self.log_test("Move Email to Trash", False, error=str(e))

            # Test restore email from trash
            try:
                response = self.session.post(
                    f"{API_BASE}/emails/{email_id}/action",
                    json={"action": "restore"},
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Restore Email from Trash", success, response)
            except Exception as e:
                self.log_test("Restore Email from Trash", False, error=str(e))

            # Test move email to archive
            try:
                response = self.session.post(
                    f"{API_BASE}/emails/{email_id}/action",
                    json={"action": "archive"},
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Move Email to Archive", success, response)
            except Exception as e:
                self.log_test("Move Email to Archive", False, error=str(e))

            # Test move email to spam
            try:
                response = self.session.post(
                    f"{API_BASE}/emails/{email_id}/action",
                    json={"action": "spam"},
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Move Email to Spam", success, response)
            except Exception as e:
                self.log_test("Move Email to Spam", False, error=str(e))

    def test_email_filtering(self):
        """Test email filtering and folder access"""
        print("🔍 Testing Email Filtering & Folders...")
        
        if not self.auth_token:
            print("   Skipping - No auth token available")
            return

        # Test list emails with different filters
        filters = [
            {"folder": "inbox"},
            {"folder": "trash"},
            {"folder": "archive"},
            {"folder": "spam"},
            {"is_read": "false"},
            {"is_read": "true"}
        ]

        for filter_params in filters:
            try:
                response = self.session.get(
                    f"{API_BASE}/emails/",
                    params={**filter_params, "page": 1, "per_page": 5},
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code in [200, 403]  # 403 for restricted folders
                filter_name = " & ".join([f"{k}={v}" for k, v in filter_params.items()])
                self.log_test(f"Filter Emails: {filter_name}", success, response)
            except Exception as e:
                filter_name = " & ".join([f"{k}={v}" for k, v in filter_params.items()])
                self.log_test(f"Filter Emails: {filter_name}", False, error=str(e))

    def test_categorization_apis(self):
        """Test email categorization APIs"""
        print("🏷️ Testing Categorization APIs...")
        
        if not self.auth_token:
            print("   Skipping - No auth token available")
            return

        # Test get categories
        try:
            response = self.session.get(
                f"{API_BASE}/emails/categories",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get Categories", success, response)
        except Exception as e:
            self.log_test("Get Categories", False, error=str(e))

        # Test get main categories
        try:
            response = self.session.get(
                f"{API_BASE}/emails/categories/main",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get Main Categories", success, response)
        except Exception as e:
            self.log_test("Get Main Categories", False, error=str(e))

        # Test get uncategorized emails
        try:
            response = self.session.get(
                f"{API_BASE}/emails/categorize/uncategorized",
                params={"limit": 5},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get Uncategorized Emails", success, response)
        except Exception as e:
            self.log_test("Get Uncategorized Emails", False, error=str(e))

        # Test batch categorization
        if self.email_ids:
            try:
                response = self.session.post(
                    f"{API_BASE}/emails/categorize/batch",
                    json={"email_ids": self.email_ids[:2], "limit": 2},
                    headers=self.get_headers(self.auth_token)
                )
                success = response.status_code == 200
                self.log_test("Batch Categorization", success, response)
            except Exception as e:
                self.log_test("Batch Categorization", False, error=str(e))

    def test_admin_apis(self):
        """Test admin-specific APIs"""
        print("👑 Testing Admin APIs...")
        
        if not self.admin_token:
            print("   Skipping - No admin token available")
            return

        # Test get all users
        try:
            response = self.session.get(
                f"{API_BASE}/admin/users",
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            self.log_test("Get All Users (Admin)", success, response)
        except Exception as e:
            self.log_test("Get All Users (Admin)", False, error=str(e))

        # Test get system stats
        try:
            response = self.session.get(
                f"{API_BASE}/admin/stats",
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            self.log_test("Get System Stats (Admin)", success, response)
        except Exception as e:
            self.log_test("Get System Stats (Admin)", False, error=str(e))

    def test_settings_apis(self):
        """Test settings APIs"""
        print("⚙️ Testing Settings APIs...")
        
        if not self.auth_token:
            print("   Skipping - No auth token available")
            return

        # Test get user settings
        try:
            response = self.session.get(
                f"{API_BASE}/settings/user",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get User Settings", success, response)
        except Exception as e:
            self.log_test("Get User Settings", False, error=str(e))

        # Test update user settings
        try:
            response = self.session.put(
                f"{API_BASE}/settings/user",
                json={"name": "Updated Test User"},
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Update User Settings", success, response)
        except Exception as e:
            self.log_test("Update User Settings", False, error=str(e))

    def test_notification_apis(self):
        """Test notification APIs"""
        print("🔔 Testing Notification APIs...")
        
        if not self.auth_token:
            print("   Skipping - No auth token available")
            return

        # Test get notifications
        try:
            response = self.session.get(
                f"{API_BASE}/notifications/",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get Notifications", success, response)
        except Exception as e:
            self.log_test("Get Notifications", False, error=str(e))

        # Test get notification rules
        try:
            response = self.session.get(
                f"{API_BASE}/notifications/rules",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get Notification Rules", success, response)
        except Exception as e:
            self.log_test("Get Notification Rules", False, error=str(e))

    def test_reply_apis(self):
        """Test reply template APIs"""
        print("💬 Testing Reply APIs...")
        
        if not self.auth_token:
            print("   Skipping - No auth token available")
            return

        # Test get reply templates
        try:
            response = self.session.get(
                f"{API_BASE}/replies/templates",
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code == 200
            self.log_test("Get Reply Templates", success, response)
        except Exception as e:
            self.log_test("Get Reply Templates", False, error=str(e))

        # Test create reply template
        test_template = {
            "name": "Test Template",
            "subject": "Re: {original_subject}",
            "content": "Thank you for your email. I will get back to you soon.",
            "category": "general"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/replies/templates",
                json=test_template,
                headers=self.get_headers(self.auth_token)
            )
            success = response.status_code in [200, 201]
            self.log_test("Create Reply Template", success, response)
        except Exception as e:
            self.log_test("Create Reply Template", False, error=str(e))

    def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        if self.admin_token:
            # Delete test email account
            try:
                response = self.session.delete(
                    f"{API_BASE}/settings/email-accounts/{TEST_EMAIL_ACCOUNT['email']}",
                    headers=self.get_headers(self.admin_token)
                )
                success = response.status_code in [200, 404]
                self.log_test("Delete Test Email Account", success, response)
            except Exception as e:
                self.log_test("Delete Test Email Account", False, error=str(e))

    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 TEST REPORT")
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
        report_file = "api_test_results.json"
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
        """Run all API tests"""
        print("🚀 Starting Comprehensive API Testing...")
        print("="*60)
        
        # Test health first
        if not self.test_health_check():
            print("❌ Health check failed. Backend may not be running.")
            return False
        
        # Run all test suites
        self.test_auth_apis()
        self.test_email_account_apis()
        self.test_email_fetch_and_listing()
        self.test_read_unread_apis()
        self.test_email_actions()
        self.test_email_filtering()
        self.test_categorization_apis()
        self.test_admin_apis()
        self.test_settings_apis()
        self.test_notification_apis()
        self.test_reply_apis()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Generate report
        return self.generate_report()

def main():
    """Main function"""
    print("Email Automation Backend - Comprehensive API Testing")
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
    tester = APITester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 