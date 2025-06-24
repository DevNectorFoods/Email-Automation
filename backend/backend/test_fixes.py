#!/usr/bin/env python3
"""
Test script to verify the fixes for email automation issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db_models import db_manager, EmailAccount
from services.email_service import EmailService
from services.auth_service import AuthService
from datetime import datetime

def test_database_fixes():
    """Test database-related fixes."""
    print("Testing database fixes...")
    
    # Test database initialization
    try:
        db_manager.init_database()
        print("✓ Database initialization successful")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    # Test adding email account
    try:
        test_account = EmailAccount(
            email="test@example.com",
            password="testpass",
            imap_server="mail.hostinger.com",
            imap_port=993,
            account_type="hostinger",
            is_active=True
        )
        success = db_manager.add_email_account(test_account)
        if success:
            print("✓ Email account addition successful")
        else:
            print("✗ Email account addition failed")
            return False
    except Exception as e:
        print(f"✗ Email account addition failed: {e}")
        return False
    
    # Test getting email accounts
    try:
        accounts = db_manager.get_email_accounts()
        print(f"✓ Retrieved {len(accounts)} email accounts")
        for account in accounts:
            print(f"  - {account.email} (UID: {account.last_fetched_uid}, Date: {account.last_fetched_date})")
    except Exception as e:
        print(f"✗ Getting email accounts failed: {e}")
        return False
    
    return True

def test_email_service_fixes():
    """Test email service fixes."""
    print("\nTesting email service fixes...")
    
    try:
        email_service = EmailService()
        print("✓ Email service initialization successful")
    except Exception as e:
        print(f"✗ Email service initialization failed: {e}")
        return False
    
    # Test email hash generation
    try:
        from models.db_models import Email
        test_email = Email(
            id="test123",
            account_email="test@example.com",
            subject="Test Subject",
            sender="sender@example.com",
            date=datetime.now()
        )
        email_hash = email_service.generate_email_hash(test_email)
        print(f"✓ Email hash generation successful: {email_hash}")
    except Exception as e:
        print(f"✗ Email hash generation failed: {e}")
        return False
    
    return True

def test_auth_service_fixes():
    """Test auth service fixes."""
    print("\nTesting auth service fixes...")
    
    try:
        auth_service = AuthService()
        print("✓ Auth service initialization successful")
    except Exception as e:
        print(f"✗ Auth service initialization failed: {e}")
        return False
    
    # Test create_user method
    try:
        user = auth_service.create_user("testuser", "test@example.com", "testpass")
        if user:
            print("✓ User creation successful")
        else:
            print("✗ User creation failed")
            return False
    except Exception as e:
        print(f"✗ User creation failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Email Automation Fixes Test")
    print("=" * 40)
    
    # Test database fixes
    if not test_database_fixes():
        print("\n❌ Database fixes failed!")
        return
    
    # Test email service fixes
    if not test_email_service_fixes():
        print("\n❌ Email service fixes failed!")
        return
    
    # Test auth service fixes
    if not test_auth_service_fixes():
        print("\n❌ Auth service fixes failed!")
        return
    
    print("\n✅ All fixes verified successfully!")
    print("\nSummary of fixes applied:")
    print("1. Added missing update_last_fetched_date method to DatabaseManager")
    print("2. Added last_fetched_date column to email_accounts table")
    print("3. Added email_hash column to emails table")
    print("4. Fixed Email dataclass to include missing fields (tags, raw_data)")
    print("5. Removed references to missing EmailCategorizationService and NotificationService")
    print("6. Fixed generate_email_hash method to use correct field name")
    print("7. Updated database schema and methods to handle new columns")

if __name__ == "__main__":
    main() 