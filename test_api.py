#!/usr/bin/env python3
"""
API Test Script for Mental Health Wellness Center Employee Tracking System
Tests the main API endpoints to verify functionality.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
TEST_USER = {
    "phone_number": "+15551234567",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "employee_id": "TEST001",
    "department": "Testing",
    "position": "Test Practitioner",
    "password": "testpass123",
    "password_confirm": "testpass123"
}

TEST_CLIENT = {
    "client_id": "TEST_CLIENT_001",
    "first_name": "Test",
    "last_name": "Client",
    "phone_number": "+15551234568",
    "email": "testclient@example.com",
    "street_address": "123 Test Street",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
    "latitude": "39.7817",
    "longitude": "-89.6501",
    "care_level": "medium"
}

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.client_id = None
        self.session_id = None
    
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
    
    def make_request(self, method, endpoint, data=None, auth_required=True):
        """Make HTTP request with proper headers."""
        url = f"{API_BASE}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth_required and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except Exception as e:
            self.log(f"Request failed: {e}", "ERROR")
            return None
    
    def test_health_check(self):
        """Test health check endpoint."""
        self.log("Testing health check endpoint...")
        try:
            response = requests.get("http://localhost:8000/health/")
            if response.status_code == 200:
                self.log("✅ Health check passed")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Health check failed: {e}", "ERROR")
            return False
    
    def test_user_registration(self):
        """Test user registration."""
        self.log("Testing user registration...")
        response = self.make_request("POST", "/auth/register/", TEST_USER, auth_required=False)
        
        if response and response.status_code == 201:
            data = response.json()
            self.access_token = data.get("tokens", {}).get("access")
            self.user_id = data.get("user", {}).get("id")
            self.log("✅ User registration successful")
            return True
        else:
            error_msg = response.json() if response else "No response"
            self.log(f"❌ User registration failed: {error_msg}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test user login."""
        self.log("Testing user login...")
        login_data = {
            "phone_number": TEST_USER["phone_number"],
            "password": TEST_USER["password"]
        }
        
        response = self.make_request("POST", "/auth/login/", login_data, auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            self.access_token = data.get("tokens", {}).get("access")
            self.log("✅ User login successful")
            return True
        else:
            error_msg = response.json() if response else "No response"
            self.log(f"❌ User login failed: {error_msg}", "ERROR")
            return False
    
    def test_user_profile(self):
        """Test user profile retrieval."""
        self.log("Testing user profile retrieval...")
        response = self.make_request("GET", "/auth/profile/")
        
        if response and response.status_code == 200:
            data = response.json()
            self.log(f"✅ User profile retrieved: {data.get('full_name')}")
            return True
        else:
            self.log("❌ User profile retrieval failed", "ERROR")
            return False
    
    def test_client_creation(self):
        """Test client creation (if user has permissions)."""
        self.log("Testing client creation...")
        response = self.make_request("POST", "/clients/create/", TEST_CLIENT)
        
        if response and response.status_code == 201:
            data = response.json()
            self.client_id = data.get("id")
            self.log(f"✅ Client created: {data.get('full_name')}")
            return True
        elif response and response.status_code == 403:
            self.log("⚠️  Client creation requires supervisor permissions", "WARN")
            # Try to get existing clients instead
            return self.test_client_list()
        else:
            error_msg = response.json() if response else "No response"
            self.log(f"❌ Client creation failed: {error_msg}", "ERROR")
            return False
    
    def test_client_list(self):
        """Test client listing."""
        self.log("Testing client listing...")
        response = self.make_request("GET", "/clients/")
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("results"):
                self.client_id = data["results"][0]["id"]
                self.log(f"✅ Client list retrieved: {len(data['results'])} clients")
                return True
            else:
                self.log("⚠️  No clients found in the system", "WARN")
                return False
        else:
            self.log("❌ Client listing failed", "ERROR")
            return False
    
    def test_clock_in(self):
        """Test clock in functionality."""
        if not self.client_id:
            self.log("❌ Cannot test clock in: No client available", "ERROR")
            return False
        
        self.log("Testing clock in...")
        clock_in_data = {
            "client": self.client_id,
            "latitude": "39.7817",
            "longitude": "-89.6501",
            "accuracy": 15.5,
            "service_type": "counseling"
        }
        
        response = self.make_request("POST", "/sessions/clock-in/", clock_in_data)
        
        if response and response.status_code == 201:
            data = response.json()
            self.session_id = data.get("session", {}).get("session_id")
            self.log("✅ Clock in successful")
            return True
        else:
            error_msg = response.json() if response else "No response"
            self.log(f"❌ Clock in failed: {error_msg}", "ERROR")
            return False
    
    def test_active_session(self):
        """Test active session retrieval."""
        self.log("Testing active session retrieval...")
        response = self.make_request("GET", "/sessions/active/")
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("active_session"):
                self.log("✅ Active session retrieved")
                return True
            else:
                self.log("⚠️  No active session found", "WARN")
                return False
        else:
            self.log("❌ Active session retrieval failed", "ERROR")
            return False
    
    def test_clock_out(self):
        """Test clock out functionality."""
        self.log("Testing clock out...")
        clock_out_data = {
            "latitude": "39.7818",
            "longitude": "-89.6502",
            "accuracy": 12.3,
            "session_notes": "Test session completed successfully"
        }
        
        response = self.make_request("POST", "/sessions/clock-out/", clock_out_data)
        
        if response and response.status_code == 200:
            data = response.json()
            self.log("✅ Clock out successful")
            return True
        else:
            error_msg = response.json() if response else "No response"
            self.log(f"❌ Clock out failed: {error_msg}", "ERROR")
            return False
    
    def test_session_list(self):
        """Test session listing."""
        self.log("Testing session listing...")
        response = self.make_request("GET", "/sessions/my-sessions/")
        
        if response and response.status_code == 200:
            data = response.json()
            self.log(f"✅ Session list retrieved: {len(data.get('results', []))} sessions")
            return True
        else:
            self.log("❌ Session listing failed", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all API tests."""
        self.log("🏥 Starting API Tests for Mental Health Wellness Center System")
        self.log("=" * 70)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("User Profile", self.test_user_profile),
            ("Client Management", self.test_client_creation),
            ("Clock In", self.test_clock_in),
            ("Active Session", self.test_active_session),
            ("Clock Out", self.test_clock_out),
            ("Session List", self.test_session_list),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"Running test: {test_name}")
            if test_func():
                passed += 1
            self.log("-" * 50)
        
        self.log("=" * 70)
        self.log(f"Tests completed: {passed}/{total} passed")
        
        if passed == total:
            self.log("🎉 All tests passed! API is working correctly.")
            return True
        else:
            self.log(f"⚠️  {total - passed} tests failed. Please check the issues above.")
            return False

def main():
    """Main function to run API tests."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("API Test Script for Mental Health Wellness Center Employee Tracking System")
        print("Usage: python test_api.py [BASE_URL]")
        print("Default BASE_URL: http://localhost:8000")
        return
    
    # Allow custom base URL
    if len(sys.argv) > 1:
        global BASE_URL, API_BASE
        BASE_URL = sys.argv[1].rstrip('/')
        API_BASE = f"{BASE_URL}/api/v1"
    
    tester = APITester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
