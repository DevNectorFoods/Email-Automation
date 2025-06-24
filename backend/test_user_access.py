#!/usr/bin/env python3
"""
Test script for user email access functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.models.db_models import db_manager
from backend.services.auth_service import AuthService

def test_user_email_access():
    """Test the user email access functionality."""
    print("Testing User Email Access Functionality")
    print("=" * 50)
    
    # Initialize services
    auth_service = AuthService()
    
    # Test 1: Get all users
    print("\n1. Getting all users...")
    users = auth_service.get_all_users()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  - {user['name']} ({user['email']}) - Role: {user['role']}")
    
    # Test 2: Get all email accounts
    print("\n2. Getting all email accounts...")
    email_accounts = db_manager.get_email_accounts()
    print(f"Found {len(email_accounts)} email accounts:")
    for account in email_accounts:
        print(f"  - {account.email} (Active: {account.is_active})")
    
    # Test 3: Get user email access for first user (if exists)
    if users:
        first_user = users[0]
        print(f"\n3. Getting email access for user: {first_user['name']}")
        user_access = db_manager.get_user_email_access(first_user['id'])
        print(f"User has access to {len(user_access)} email accounts:")
        for access in user_access:
            print(f"  - {access['account_email']} (Level: {access['access_level']})")
    
    # Test 4: Get users with access for first email account (if exists)
    if email_accounts:
        first_account = email_accounts[0]
        print(f"\n4. Getting users with access to: {first_account.email}")
        users_with_access = db_manager.get_users_with_email_access(first_account.email)
        print(f"Found {len(users_with_access)} users with access:")
        for user_access in users_with_access:
            print(f"  - {user_access['name']} ({user_access['email']}) - Level: {user_access['access_level']}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_user_email_access() 