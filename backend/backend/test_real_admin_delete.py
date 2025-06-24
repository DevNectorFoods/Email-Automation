#!/usr/bin/env python3
"""
Real Admin Delete Test - Using actual admin credentials
Tests delete functionality with real admin account to verify emails go to trash
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

# Real admin credentials
ADMIN_CREDENTIALS = {
    "email": "admin@emailautomation.com",
    "password": "admin123"
}

class RealAdminDeleteTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
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

    def login_admin(self):
        """Login with real admin credentials"""
        print("🔐 Logging in with real admin credentials...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=ADMIN_CREDENTIALS,
                headers=self.get_headers()
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                print(f"   ✅ Logged in as: {user_info.get('email')} (Role: {user_info.get('role')})")
            else:
                print(f"   ❌ Login failed: {response.text}")
            self.log_test("Admin Login", success, response)
            return success
        except Exception as e:
            self.log_test("Admin Login", False, error=str(e))
            return False

    def get_test_email(self):
        """Get a test email to work with"""
        print("📧 Getting test email...")
        
        try:
            # First fetch some emails
            response = self.session.post(
                f"{API_BASE}/emails/fetch",
                json={"limit": 10},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            self.log_test("Fetch Emails", success, response)
            
            # Get list of emails from inbox
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "inbox", "page": 1, "per_page": 10},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                if emails:
                    self.test_email_id = emails[0]["id"]
                    email_subject = emails[0].get("subject", "No subject")
                    print(f"   📧 Using email: {email_subject} (ID: {self.test_email_id})")
                else:
                    print("   ⚠️ No emails found in inbox")
            self.log_test("Get Inbox Emails", success, response)
            return success and emails
        except Exception as e:
            self.log_test("Get Test Email", False, error=str(e))
            return False

    def test_delete_to_trash(self):
        """Test that deleting an email moves it to trash and removes from inbox"""
        print("🗑️ Testing Delete to Trash Functionality...")
        
        if not self.test_email_id:
            print("   ❌ No test email available")
            return False

        # Step 1: Verify email is initially in inbox
        print("\n📋 Step 1: Verifying email is in inbox...")
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "inbox", "page": 1, "per_page": 20},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                found_in_inbox = any(email["id"] == self.test_email_id for email in emails)
                print(f"   📥 Email found in inbox: {found_in_inbox}")
                inbox_count = len(emails)
                print(f"   📊 Total emails in inbox: {inbox_count}")
            self.log_test("Check Email in Inbox (Before Delete)", success, response)
        except Exception as e:
            self.log_test("Check Email in Inbox (Before Delete)", False, error=str(e))

        # Step 2: Delete the email (move to trash)
        print("\n🗑️ Step 2: Moving email to trash...")
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/action",
                json={"action": "trash"},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"   ✅ Delete response: {data.get('message', 'No message')}")
            self.log_test("Move Email to Trash", success, response)
        except Exception as e:
            self.log_test("Move Email to Trash", False, error=str(e))

        # Step 3: Verify email is NOT in inbox anymore
        print("\n📋 Step 3: Verifying email is removed from inbox...")
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "inbox", "page": 1, "per_page": 20},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                found_in_inbox = any(email["id"] == self.test_email_id for email in emails)
                print(f"   📥 Email found in inbox: {found_in_inbox}")
                inbox_count = len(emails)
                print(f"   📊 Total emails in inbox: {inbox_count}")
                
                if not found_in_inbox:
                    print("   ✅ SUCCESS: Email successfully removed from inbox!")
                else:
                    print("   ❌ FAILURE: Email still appears in inbox!")
            self.log_test("Check Email Removed from Inbox", success, response)
        except Exception as e:
            self.log_test("Check Email Removed from Inbox", False, error=str(e))

        # Step 4: Verify email IS in trash
        print("\n🗑️ Step 4: Verifying email is in trash...")
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "trash", "page": 1, "per_page": 20},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                found_in_trash = any(email["id"] == self.test_email_id for email in emails)
                print(f"   🗑️ Email found in trash: {found_in_trash}")
                trash_count = len(emails)
                print(f"   📊 Total emails in trash: {trash_count}")
                
                if found_in_trash:
                    print("   ✅ SUCCESS: Email successfully moved to trash!")
                else:
                    print("   ❌ FAILURE: Email not found in trash!")
            self.log_test("Check Email in Trash", success, response)
        except Exception as e:
            self.log_test("Check Email in Trash", False, error=str(e))

        # Step 5: Check individual email status
        print("\n📋 Step 5: Checking individual email status...")
        try:
            response = self.session.get(
                f"{API_BASE}/emails/{self.test_email_id}",
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                is_trashed = data.get("is_trashed", False)
                folder = data.get("folder", "")
                print(f"   📊 Email status - is_trashed: {is_trashed}, folder: {folder}")
                
                if is_trashed and folder == "trash":
                    print("   ✅ SUCCESS: Email status correctly updated!")
                else:
                    print("   ❌ FAILURE: Email status not updated correctly!")
            self.log_test("Check Individual Email Status", success, response)
        except Exception as e:
            self.log_test("Check Individual Email Status", False, error=str(e))

    def test_restore_from_trash(self):
        """Test restoring email from trash back to inbox"""
        print("\n🔄 Testing Restore from Trash...")
        
        if not self.test_email_id:
            print("   ❌ No test email available")
            return False

        # Step 1: Restore email from trash
        print("\n🔄 Step 1: Restoring email from trash...")
        try:
            response = self.session.post(
                f"{API_BASE}/emails/{self.test_email_id}/action",
                json={"action": "restore"},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"   ✅ Restore response: {data.get('message', 'No message')}")
            self.log_test("Restore Email from Trash", success, response)
        except Exception as e:
            self.log_test("Restore Email from Trash", False, error=str(e))

        # Step 2: Verify email is back in inbox
        print("\n📋 Step 2: Verifying email is back in inbox...")
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "inbox", "page": 1, "per_page": 20},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                found_in_inbox = any(email["id"] == self.test_email_id for email in emails)
                print(f"   📥 Email found in inbox: {found_in_inbox}")
                
                if found_in_inbox:
                    print("   ✅ SUCCESS: Email successfully restored to inbox!")
                else:
                    print("   ❌ FAILURE: Email not restored to inbox!")
            self.log_test("Check Email Restored to Inbox", success, response)
        except Exception as e:
            self.log_test("Check Email Restored to Inbox", False, error=str(e))

        # Step 3: Verify email is removed from trash
        print("\n🗑️ Step 3: Verifying email is removed from trash...")
        try:
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "trash", "page": 1, "per_page": 20},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                found_in_trash = any(email["id"] == self.test_email_id for email in emails)
                print(f"   🗑️ Email found in trash: {found_in_trash}")
                
                if not found_in_trash:
                    print("   ✅ SUCCESS: Email successfully removed from trash!")
                else:
                    print("   ❌ FAILURE: Email still appears in trash!")
            self.log_test("Check Email Removed from Trash", success, response)
        except Exception as e:
            self.log_test("Check Email Removed from Trash", False, error=str(e))

    def test_multiple_deletes(self):
        """Test deleting multiple emails"""
        print("\n🗑️ Testing Multiple Email Deletes...")
        
        try:
            # Get multiple emails
            response = self.session.get(
                f"{API_BASE}/emails/",
                params={"folder": "inbox", "page": 1, "per_page": 5},
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                emails = data.get("emails", [])
                print(f"   📊 Found {len(emails)} emails in inbox")
                
                # Delete first 2 emails
                deleted_count = 0
                for i, email in enumerate(emails[:2]):
                    email_id = email["id"]
                    email_subject = email.get("subject", "No subject")
                    print(f"   🗑️ Deleting email {i+1}: {email_subject[:50]}...")
                    
                    try:
                        delete_response = self.session.post(
                            f"{API_BASE}/emails/{email_id}/action",
                            json={"action": "trash"},
                            headers=self.get_headers(self.admin_token)
                        )
                        if delete_response.status_code == 200:
                            deleted_count += 1
                            print(f"   ✅ Successfully deleted email {i+1}")
                        else:
                            print(f"   ❌ Failed to delete email {i+1}")
                    except Exception as e:
                        print(f"   ❌ Error deleting email {i+1}: {str(e)}")
                
                print(f"   📊 Successfully deleted {deleted_count}/2 emails")
                
                # Verify they're in trash
                time.sleep(1)  # Small delay to ensure database updates
                trash_response = self.session.get(
                    f"{API_BASE}/emails/",
                    params={"folder": "trash", "page": 1, "per_page": 10},
                    headers=self.get_headers(self.admin_token)
                )
                if trash_response.status_code == 200:
                    trash_data = trash_response.json()
                    trash_emails = trash_data.get("emails", [])
                    print(f"   🗑️ Total emails in trash: {len(trash_emails)}")
                
            self.log_test("Multiple Email Deletes", success, response)
        except Exception as e:
            self.log_test("Multiple Email Deletes", False, error=str(e))

    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 REAL ADMIN DELETE TEST REPORT")
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
        report_file = "real_admin_delete_test_results.json"
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
        """Run all delete tests with real admin"""
        print("🚀 Starting Real Admin Delete Testing...")
        print("="*60)
        
        # Login with real admin
        if not self.login_admin():
            print("❌ Failed to login with admin credentials")
            return False
        
        # Get test email
        if not self.get_test_email():
            print("❌ Failed to get test email")
            return False
        
        # Run tests
        self.test_delete_to_trash()
        self.test_restore_from_trash()
        self.test_multiple_deletes()
        
        # Generate report
        return self.generate_report()

def main():
    """Main function"""
    print("Email Automation Backend - Real Admin Delete Testing")
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
    tester = RealAdminDeleteTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 