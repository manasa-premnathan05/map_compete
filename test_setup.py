#!/usr/bin/env python3
"""
Simple test to verify the backend components can be imported and initialized
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")

        # Add backend to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

        # Test database
        from database import DatabaseManager
        print("[PASS] DatabaseManager imported successfully")

        # Test scraper
        from scraper import GoogleMapsScraper
        print("[PASS] GoogleMapsScraper imported successfully")

        # Test AI service
        from ai_service import AIServiceManager
        print("[PASS] AIServiceManager imported successfully")

        # Test API
        from api import app
        print("[PASS] Flask app imported successfully")

        print("\nAll imports successful!")
        return True

    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False

def test_database_initialization():
    """Test that database can be initialized"""
    try:
        print("\nTesting database initialization...")

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from database import DatabaseManager

        # Create a temporary database for testing
        db = DatabaseManager("test_database.db")
        print("[PASS] Database initialized successfully")

        # Clean up test database
        if os.path.exists("test_database.db"):
            os.remove("test_database.db")

        return True

    except Exception as e:
        print(f"[FAIL] Database initialization error: {e}")
        return False

if __name__ == "__main__":
    print("Running setup tests...\n")

    success = True
    success &= test_imports()
    success &= test_database_initialization()

    if success:
        print("\n[INFO] All tests passed! The setup appears to be working correctly.")
        sys.exit(0)
    else:
        print("\n[ERROR] Some tests failed. Please check the error messages above.")
        sys.exit(1)