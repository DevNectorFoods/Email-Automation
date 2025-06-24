#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.email_models import EmailAccount
from models.db_models import db_manager
from services.email_service import EmailService

def test_add_account():
    try:
        print("Testing email account addition...")
        
        # Create email account
        account = EmailAccount(
            email="developer.testing@nectorinternational.com",
            password="Test.Nector87&^*",
            imap_server="imap.hostinger.com",
            imap_port=993,
            is_active=True
        )
        
        print(f"Created account object: {account.email}")
        
        # Test connection
        email_service = EmailService()
        print("Testing connection...")
        if email_service.test_account_connection(account):
            print("Connection test successful!")
        else:
            print("Connection test failed!")
            return False
        
        # Save to database
        print("Saving to database...")
        if db_manager.add_email_account(account):
            print("Account saved successfully!")
            return True
        else:
            print("Failed to save account!")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_add_account()
    if success:
        print("✅ Email account added successfully!")
    else:
        print("❌ Failed to add email account!") 