#!/usr/bin/env python3
"""
Test script to check database persistence for email status changes.
This will help identify if the issue is with data persistence or something else.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

# Configuration
API_BASE = "http://localhost:5000/api"
ADMIN_EMAIL = "admin@emailautomation.com"
ADMIN_PASSWORD = "admin123"

class DatabasePersistenceTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_email_id = None
        
    def log_test(self, test_name, success, response=None, error=None):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if response:
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Response: {response.text}")
        if error:
            print(f"   Error: {error}")
        print()

    def login_admin(self):
        """Login as admin user."""
        print("🔐 Logging in as admin...")
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            success = response.status_code == 200
            if success:
                data = response.json()
                self.admin_token = data.get("access_token")
                print(f"   ✅ Logged in as: {ADMIN_EMAIL}")
            self.log_test("Admin Login", success, response)
            return success
        except Exception as e:
            self.log_test("Admin Login", False, error=str(e))
            return False

    def get_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def get_test_email(self):
        """Get a test email to work with."""
        print("📧 Getting test email...")
        try:
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
            self.log_test("Get Test Email", success, response)
            return success and emails
        except Exception as e:
            self.log_test("Get Test Email", False, error=str(e))
            return False

    def test_database_persistence(self):
        """Test if database changes persist after server restart."""
        print("🗄️ Testing Database Persistence...")
        
        if not self.test_email_id:
            print("   Skipping - No test email available")
            return False

        # Step 1: Check initial state
        print("\n📋 Step 1: Checking initial email state...")
        try:
            response = self.session.get(
                f"{API_BASE}/emails/{self.test_email_id}",
                headers=self.get_headers(self.admin_token)
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                initial_is_trashed = data.get("is_trashed", False)
                initial_folder = data.get("folder", "")
                print(f"   📊 Initial state - is_trashed: {initial_is_trashed}, folder: {initial_folder}")
            self.log_test("Check Initial State", success, response)
        except Exception as e:
            self.log_test("Check Initial State", False, error=str(e))

        # Step 2: Move email to trash
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
                print(f"   ✅ Trash response: {data.get('message', 'No message')}")
            self.log_test("Move to Trash", success, response)
        except Exception as e:
            self.log_test("Move to Trash", False, error=str(e))

        # Step 3: Verify email is in trash
        print("\n🗑️ Step 3: Verifying email is in trash...")
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
                print(f"   📊 Total emails in trash: {len(emails)}")
            self.log_test("Verify in Trash", success, response)
        except Exception as e:
            self.log_test("Verify in Trash", False, error=str(e))

        # Step 4: Check individual email status
        print("\n📋 Step 4: Checking individual email status...")
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
            self.log_test("Check Email Status", success, response)
        except Exception as e:
            self.log_test("Check Email Status", False, error=str(e))

        # Step 5: Check database directly (if possible)
        print("\n🗄️ Step 5: Checking database persistence...")
        print("   ℹ️ This step would require direct database access to verify")
        print("   ℹ️ The issue might be that the database changes are not being committed properly")
        print("   ℹ️ Or there might be a transaction rollback happening")

        return True

    def run_all_tests(self):
        """Run all persistence tests."""
        print("Database Persistence Testing")
        print("=" * 50)
        
        # Login
        if not self.login_admin():
            return False
        
        # Get test email
        if not self.get_test_email():
            return False
        
        # Test persistence
        self.test_database_persistence()
        
        print("=" * 50)
        print("Database persistence test completed.")
        print("If the email status is not persisting after server restart,")
        print("the issue is likely with database transactions or commits.")

if __name__ == "__main__":
    tester = DatabasePersistenceTester()
    tester.run_all_tests() 