#!/usr/bin/env python3
"""
Diagnostic script to check authentication setup
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.db_models import User, Base
from app.auth import authenticate_user, get_password_hash
from sqlalchemy import text

def diagnose():
    print("=" * 60)
    print("AUTHENTICATION DIAGNOSTIC")
    print("=" * 60)
    
    # Check database connection
    print("\n1. Database Connection:")
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        print("   ✓ Database connected")
        db.close()
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return
    
    # Check tables exist
    print("\n2. Database Tables:")
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        print(f"   ✓ Users table exists ({user_count} users)")
    except Exception as e:
        print(f"   ✗ Users table error: {e}")
        db.close()
        return
    
    # List users
    print("\n3. Users in Database:")
    users = db.query(User).all()
    if not users:
        print("   ✗ No users found!")
    else:
        for user in users:
            print(f"   - {user.username} (ID: {user.id}, Email: {user.email})")
    
    # Test authentication
    print("\n4. Authentication Test:")
    test_creds = [
        ("admin", "admin123"),
        ("stalin", "password123"),
        ("sarah", "password123"),
        ("mike", "password123"),
    ]
    
    for username, password in test_creds:
        user = authenticate_user(db, username, password)
        status = "✓" if user else "✗"
        print(f"   {status} {username}:{password}")
    
    # Check SECRET_KEY
    print("\n5. Configuration:")
    secret = os.getenv("SECRET_KEY", "default")
    print(f"   SECRET_KEY: {secret[:20]}..." if len(secret) > 20 else f"   SECRET_KEY: {secret}")
    
    db.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    diagnose()
