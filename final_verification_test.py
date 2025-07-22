#!/usr/bin/env python3
"""
Final Verification Test for Mental Health Wellness Center Employee Tracking System
Tests all core functionality to ensure the system is working correctly.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class SystemVerificationTest:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.client_id = None
        self.session_id = None
        self.test_results = []
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        
    def run_test(self, test_name, test_func):
        """Run a test and track results"""
        self.log(f"🧪 Testing: {test_name}")
        try:
            result = test_func()
            if result:
                self.log(f"✅ {test_name} - PASSED")
                self.test_results.append((test_name, True, None))
            else:
                self.log(f"❌ {test_name} - FAILED")
                self.test_results.append((test_name, False, "Test returned False"))
        except Exception as e:
            self.log(f"❌ {test_name} - ERROR: {str(e)}")
            self.test_results.append((test_name, False, str(e)))
        print("-" * 60)
        
    def test_1_health_check(self):
        """Test system health check"""
        response = requests.get(f"{BASE_URL}/health/", timeout=10)
        return response.status_code == 200
        
    def test_2_admin_access(self):
        """Test admin panel accessibility"""
        response = requests.get(f"{BASE_URL}/admin/", timeout=10)
        return response.status_code in [200, 302]  # 302 for redirect to login
        
    def test_3_user_registration(self):
        """Test user registration functionality"""
        user_data = {
            "phone_number": "+254769628123",
            "email": "test.practitioner@wellness.com",
            "first_name": "Test",
            "last_name": "Practitioner",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "department": "Mental Health",
            "position": "Counselor"
        }
        
        response = requests.post(f"{API_URL}/auth/register/", json=user_data, timeout=10)
        if response.status_code == 201:
            data = response.json()
            self.user_id = data.get('user', {}).get('id')
            self.log(f"User registered with ID: {self.user_id}")
            return True
        else:
            self.log(f"Registration failed with status {response.status_code}: {response.text}")
            return False
            
    def test_4_user_login(self):
        """Test user login and token generation"""
        login_data = {
            "phone_number": "+254769628123",
            "password": "SecurePass123!"
        }
        
        response = requests.post(f"{API_URL}/auth/login/", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Try different token paths
            self.token = (data.get('tokens', {}).get('access') or 
                         data.get('access') or 
                         data.get('access_token') or
                         data.get('token'))
            if self.token:
                self.log(f"Login successful, token received: {self.token[:20]}...")
                return True
            else:
                self.log(f"No access token found in response: {data}")
                return False
        else:
            self.log(f"Login failed with status {response.status_code}: {response.text}")
            return False
            
    def test_5_user_profile(self):
        """Test authenticated user profile retrieval"""
        if not self.token:
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{API_URL}/auth/profile/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Profile retrieved for: {data.get('first_name')} {data.get('last_name')}")
            return True
        else:
            self.log(f"Profile retrieval failed with status {response.status_code}")
            return False
            
    def test_6_client_creation(self):
        """Test client creation functionality"""
        if not self.token:
            return False
            
        client_data = {
            "name": "John Doe",
            "address": "123 Wellness Street, Nairobi",
            "latitude": -1.286389,
            "longitude": 36.817223,
            "phone_number": "+254712345678",
            "care_level": "standard",
            "safety_instructions": "Client is cooperative and friendly."
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{API_URL}/clients/create/", json=client_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            data = response.json()
            self.client_id = data.get('id')
            self.log(f"Client created with ID: {self.client_id}")
            return True
        else:
            self.log(f"Client creation failed with status {response.status_code}: {response.text}")
            return False
            
    def test_7_client_list(self):
        """Test client listing functionality"""
        if not self.token:
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{API_URL}/clients/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            client_count = len(data.get('results', []))
            self.log(f"Retrieved {client_count} clients from database")
            return client_count > 0
        else:
            self.log(f"Client listing failed with status {response.status_code}")
            return False
            
    def test_8_clock_in(self):
        """Test clock in functionality"""
        if not self.token or not self.client_id:
            return False
            
        clock_in_data = {
            "client_id": self.client_id,
            "latitude": -1.286389,
            "longitude": 36.817223,
            "accuracy": 10.0,
            "notes": "Starting session with client for routine check-up"
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{API_URL}/sessions/clock-in/", json=clock_in_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            data = response.json()
            self.session_id = data.get('session_id')
            self.log(f"Clock in successful, session ID: {self.session_id}")
            return True
        else:
            self.log(f"Clock in failed with status {response.status_code}: {response.text}")
            return False
            
    def test_9_active_session(self):
        """Test active session retrieval"""
        if not self.token:
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{API_URL}/sessions/active/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('session_id') == self.session_id:
                self.log(f"Active session confirmed: {data.get('session_id')}")
                return True
            else:
                self.log("No active session found or session ID mismatch")
                return False
        else:
            self.log(f"Active session check failed with status {response.status_code}")
            return False
            
    def test_10_location_update(self):
        """Test location update during session"""
        if not self.token or not self.session_id:
            return False
            
        location_data = {
            "latitude": -1.286500,
            "longitude": 36.817300,
            "accuracy": 8.0
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{API_URL}/sessions/location-update/", json=location_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            self.log("Location update successful")
            return True
        else:
            self.log(f"Location update failed with status {response.status_code}")
            return False
            
    def test_11_clock_out(self):
        """Test clock out functionality"""
        if not self.token:
            return False
            
        clock_out_data = {
            "latitude": -1.286389,
            "longitude": 36.817223,
            "accuracy": 10.0,
            "notes": "Session completed successfully. Client is in good spirits."
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{API_URL}/sessions/clock-out/", json=clock_out_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            duration = data.get('duration_minutes', 0)
            self.log(f"Clock out successful, session duration: {duration} minutes")
            return True
        else:
            self.log(f"Clock out failed with status {response.status_code}: {response.text}")
            return False
            
    def test_12_session_history(self):
        """Test session history retrieval"""
        if not self.token:
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{API_URL}/sessions/my-sessions/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            session_count = len(data.get('results', []))
            self.log(f"Retrieved {session_count} sessions from history")
            return session_count > 0
        else:
            self.log(f"Session history failed with status {response.status_code}")
            return False
            
    def run_all_tests(self):
        """Run the complete test suite"""
        self.log("🏥 Starting Final System Verification")
        self.log("=" * 60)
        
        # Define test sequence
        tests = [
            ("Health Check", self.test_1_health_check),
            ("Admin Panel Access", self.test_2_admin_access),
            ("User Registration", self.test_3_user_registration),
            ("User Login", self.test_4_user_login),
            ("User Profile", self.test_5_user_profile),
            ("Client Creation", self.test_6_client_creation),
            ("Client Listing", self.test_7_client_list),
            ("Clock In", self.test_8_clock_in),
            ("Active Session Check", self.test_9_active_session),
            ("Location Update", self.test_10_location_update),
            ("Clock Out", self.test_11_clock_out),
            ("Session History", self.test_12_session_history),
        ]
        
        # Run each test
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            time.sleep(1)  # Brief pause between tests
            
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        self.log("=" * 60)
        self.log("🎯 FINAL VERIFICATION SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        self.log(f"Total Tests: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {total - passed}")
        self.log(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! System is fully operational!")
            return True
        else:
            self.log("⚠️  Some tests failed. Check the details above.")
            self.log("\nFailed Tests:")
            for name, success, error in self.test_results:
                if not success:
                    self.log(f"  ❌ {name}: {error}")
            return False

if __name__ == "__main__":
    tester = SystemVerificationTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
