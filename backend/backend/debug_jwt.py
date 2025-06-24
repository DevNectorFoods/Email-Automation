#!/usr/bin/env python3
"""
Debug script to test JWT token creation and validation.
"""

import jwt
from datetime import datetime, timedelta
from config import Config

def test_jwt_token():
    """Test JWT token creation and validation."""
    print("Testing JWT token creation and validation...")
    
    # Test data
    user_id = 2
    secret = Config.JWT_SECRET_KEY
    
    print(f"Using secret: {secret}")
    print(f"User ID: {user_id}")
    
    # Create a token
    payload = {
        'sub': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24),
        'type': 'access'
    }
    
    try:
        # Create token
        token = jwt.encode(payload, secret, algorithm='HS256')
        print(f"Created token: {token}")
        
        # Decode token
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        print(f"Decoded payload: {decoded}")
        
        # Test with different secret (should fail)
        try:
            wrong_decoded = jwt.decode(token, 'wrong_secret', algorithms=['HS256'])
            print("ERROR: Token decoded with wrong secret!")
        except jwt.InvalidSignatureError:
            print("✓ Token correctly rejected with wrong secret")
        
        return token
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_jwt_token() 