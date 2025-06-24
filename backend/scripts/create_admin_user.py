import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ..backend.models.user_models import User
from ..backend.models.db_models import db_manager
from datetime import datetime

# Change these credentials as needed
email = 'superadmin@emailautomation.com'
password = 'superadmin123'
name = 'Super Admin User'
role = 'super_admin'

# Create user object
user = User(email=email, name=name, role=role, created_at=datetime.now())
user.set_password(password)

# Save to database
if db_manager.create_user(user):
    print(f"Super admin user created: {email} / {password}")
else:
    print("Failed to create super admin user (maybe already exists)") 