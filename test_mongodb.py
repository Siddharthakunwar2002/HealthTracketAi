#!/usr/bin/env python3
"""
MongoDB Connection Test Script
Tests the MongoDB connection and basic operations
"""

import os
from mongoengine import connect, disconnect
from models import User, UserRole
from config import Config

def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    print("Testing MongoDB connection...")
    
    try:
        # Connect to MongoDB
        config = Config()
        connect(host=config.MONGODB_URI)
        print("✓ Successfully connected to MongoDB")
        
        # Test basic operations
        print("\nTesting basic operations...")
        
        # Count users
        user_count = User.objects.count()
        print(f"✓ Current user count: {user_count}")
        
        # Test creating a test user
        test_user = User(
            username='test_user',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role=UserRole.PATIENT,
            is_active=True
        )
        test_user.set_password('test123')
        test_user.save()
        print("✓ Successfully created test user")
        
        # Test querying the user
        found_user = User.objects(email='test@example.com').first()
        if found_user:
            print(f"✓ Successfully found user: {found_user.get_full_name()}")
        
        # Test updating the user
        found_user.first_name = 'Updated'
        found_user.save()
        print("✓ Successfully updated user")
        
        # Test deleting the user
        found_user.delete()
        print("✓ Successfully deleted test user")
        
        # Final count
        final_count = User.objects.count()
        print(f"✓ Final user count: {final_count}")
        
        print("\n🎉 All MongoDB tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ MongoDB test failed: {e}")
        return False
    
    finally:
        # Disconnect from MongoDB
        disconnect()
        print("✓ Disconnected from MongoDB")

if __name__ == '__main__':
    success = test_mongodb_connection()
    if not success:
        exit(1)
