#!/usr/bin/env python3
"""
Script to add email account to the database.
"""

import requests
import json

def add_email_account():
    # Login to get token
    login_data = {
        "email": "admin@emailautomation.com",
        "password": "admin123"
    }
    
    login_response = requests.post(
        "http://localhost:5000/api/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print("Login failed:", login_response.text)
        return
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    print("✅ Login successful!")
    
    # Add email account
    email_data = {
        "email": "developer.testing@nectorinternational.com",
        "password": "Test.Nector87&^*",
        "imap_server": "mail.hostinger.com",
        "imap_port": 993,
        "account_type": "hostinger"
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    add_response = requests.post(
        "http://localhost:5000/api/settings/email-accounts",
        json=email_data,
        headers=headers
    )
    
    print(f"Add email account response: {add_response.status_code}")
    print(f"Response: {add_response.text}")
    
    if add_response.status_code == 200:
        print("✅ Email account added successfully!")
    else:
        print("❌ Failed to add email account")

if __name__ == "__main__":
    add_email_account() 