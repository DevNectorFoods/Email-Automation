import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models.db_models import db_manager

users = []
try:
    conn = db_manager.db_path
    import sqlite3
    con = sqlite3.connect(conn)
    cur = con.cursor()
    cur.execute('SELECT id, email, password, name, role, created_at, last_login FROM users')
    users = cur.fetchall()
    con.close()
except Exception as e:
    print(f"Error reading users: {e}")

print("\nUsers in DB:")
for u in users:
    print(f"id={u[0]}, email={u[1]}, password={u[2][:20]}..., name={u[3]}, role={u[4]}, created_at={u[5]}, last_login={u[6]}") 