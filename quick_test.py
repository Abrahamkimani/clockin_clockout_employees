#!/usr/bin/env python3
"""
Quick Manual Test - Testing core functionality step by step
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_registration():
    print("=== Testing User Registration ===")
    user_data = {
        "phone_number": "+254769628999",
        "email": "quick.test@wellness.com",
        "first_name": "Quick",
        "last_name": "Test",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
        "department": "Mental Health",
        "position": "Counselor"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register/", json=user_data)
    print(f"Registration Status: {response.status_code}")
    print(f"Registration Response: {response.text}")
    return response.status_code == 201

def test_login():
    print("\n=== Testing User Login ===")
    login_data = {
        "phone_number": "+254769628999",
        "password": "TestPass123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    print(f"Login Status: {response.status_code}")
    print(f"Login Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access') or data.get('access_token') or data.get('token')
        print(f"Token found: {token is not None}")
        return token
    return None

def test_endpoints():
    print("=== Testing API Endpoints ===")
    
    # Test health check
    health = requests.get("http://localhost:8000/health/")
    print(f"Health Check: {health.status_code}")
    
    # Test admin
    admin = requests.get("http://localhost:8000/admin/")
    print(f"Admin Access: {admin.status_code}")
    
    # Test registration
    if test_registration():
        print("✅ Registration works!")
        
        # Test login
        token = test_login()
        if token:
            print("✅ Login works!")
            
            # Test authenticated endpoint
            headers = {"Authorization": f"Bearer {token}"}
            profile = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
            print(f"Profile Access: {profile.status_code}")
            
            if profile.status_code == 200:
                print("✅ Authentication works!")
            else:
                print(f"❌ Profile failed: {profile.text}")
        else:
            print("❌ Login failed")
    else:
        print("❌ Registration failed")

if __name__ == "__main__":
    test_endpoints()
