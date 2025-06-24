#!/usr/bin/env python3
"""
Script to grant test email access to users
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.models.db_models import db_manager
from backend.services.auth_service import AuthService

def grant_test_access():
    """Grant some test email access to users."""
    print("Granting Test Email Access")
    print("=" * 40)
    
    # Initialize services
    auth_service = AuthService()
    
    # Get all users and email accounts
    users = auth_service.get_all_users()
    email_accounts = db_manager.get_email_accounts()
    
    if not users:
        print("No users found!")
        return
    
    if not email_accounts:
        print("No email accounts found!")
        return
    
    # Find regular users (not admin/super_admin)
    regular_users = [user for user in users if user['role'] == 'user']
    
    if not regular_users:
        print("No regular users found!")
        return
    
    print(f"Found {len(regular_users)} regular users and {len(email_accounts)} email accounts")
    
    # Grant access to first user for first email account
    first_user = regular_users[0]
    first_account = email_accounts[0]
    
    print(f"\nGranting access to {first_user['name']} for {first_account.email}...")
    success = db_manager.grant_email_access(
        user_id=first_user['id'],
        account_email=first_account.email,
        access_level='read',
        created_by=1  # Super admin
    )
    
    if success:
        print("✅ Access granted successfully!")
    else:
        print("❌ Failed to grant access")
    
    # Grant access to second user for second email account (if exists)
    if len(regular_users) > 1 and len(email_accounts) > 1:
        second_user = regular_users[1]
        second_account = email_accounts[1]
        
        print(f"\nGranting access to {second_user['name']} for {second_account.email}...")
        success = db_manager.grant_email_access(
            user_id=second_user['id'],
            account_email=second_account.email,
            access_level='write',
            created_by=1  # Super admin
        )
        
        if success:
            print("✅ Access granted successfully!")
        else:
            print("❌ Failed to grant access")
    
    # Verify the grants
    print("\n" + "=" * 40)
    print("Verifying access grants:")
    
    for user in regular_users[:2]:  # Check first 2 users
        user_access = db_manager.get_user_email_access(user['id'])
        print(f"\n{user['name']} has access to {len(user_access)} email accounts:")
        for access in user_access:
            print(f"  - {access['account_email']} (Level: {access['access_level']})")
    
    print("\n" + "=" * 40)
    print("Test access grants completed!")

if __name__ == "__main__":
    grant_test_access() 