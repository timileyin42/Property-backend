"""
Endpoint Testing Script

This script tests all API endpoints to ensure they work correctly.
Run this after starting the application with docker-compose.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.investor_token = None
        self.test_results = {"passed": 0, "failed": 0}
    
    def print_test(self, name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{status} - {name}")
        if details:
            print(f"       {details}")
        
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
    
    def test_health_check(self):
        """Test health check endpoint"""
        print(f"\n{BLUE}=== Testing Health Check ==={RESET}")
        try:
            response = requests.get(f"{self.base_url}/health")
            self.print_test(
                "GET /health",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("GET /health", False, str(e))
    
    def test_signup_and_login(self):
        """Test signup and login endpoints"""
        print(f"\n{BLUE}=== Testing Authentication ==={RESET}")
        
        # Test signup
        try:
            signup_data = {
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
                "phone": "+234-800-000-9999"
            }
            response = requests.post(f"{self.base_url}/api/auth/signup", json=signup_data)
            self.print_test(
                "POST /api/auth/signup",
                response.status_code == 201,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("POST /api/auth/signup", False, str(e))
        
        # Test login with admin
        try:
            login_data = {
                "username": "admin@plugoflagosproperty.com",  # OAuth2 uses 'username' field
                "password": "Admin123!"
            }
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                data=login_data  # Use data instead of json for form data
            )
            if response.status_code == 200:
                self.admin_token = response.json()["access_token"]
            self.print_test(
                "POST /api/auth/login (Admin)",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("POST /api/auth/login (Admin)", False, str(e))
        
        # Test login with investor
        try:
            login_data = {
                "username": "jane.smith@example.com",  # OAuth2 uses 'username' field
                "password": "Password123!"
            }
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                data=login_data  # Use data instead of json for form data
            )
            if response.status_code == 200:
                self.investor_token = response.json()["access_token"]
            self.print_test(
                "POST /api/auth/login (Investor)",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("POST /api/auth/login (Investor)", False, str(e))
        
        # Test /me endpoint
        if self.admin_token:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
                self.print_test(
                    "GET /api/auth/me",
                    response.status_code == 200,
                    f"User: {response.json().get('email', 'N/A')}"
                )
            except Exception as e:
                self.print_test("GET /api/auth/me", False, str(e))
    
    def test_public_endpoints(self):
        """Test public endpoints"""
        print(f"\n{BLUE}=== Testing Public Endpoints ==={RESET}")
        
        # Test get properties
        try:
            response = requests.get(f"{self.base_url}/api/properties")
            self.print_test(
                "GET /api/properties",
                response.status_code == 200,
                f"Found {response.json().get('total', 0)} properties"
            )
        except Exception as e:
            self.print_test("GET /api/properties", False, str(e))
        
        # Test get property by ID
        try:
            response = requests.get(f"{self.base_url}/api/properties/1")
            self.print_test(
                "GET /api/properties/1",
                response.status_code in [200, 404],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("GET /api/properties/1", False, str(e))
        
        # Test get updates
        try:
            response = requests.get(f"{self.base_url}/api/updates")
            self.print_test(
                "GET /api/updates",
                response.status_code == 200,
                f"Found {response.json().get('total', 0)} updates"
            )
        except Exception as e:
            self.print_test("GET /api/updates", False, str(e))
        
        # Test contact form
        try:
            contact_data = {
                "name": "Test Contact",
                "email": "contact@example.com",
                "phone": "+234-800-000-0000",
                "message": "I'm interested in your properties"
            }
            response = requests.post(f"{self.base_url}/api/contact", json=contact_data)
            self.print_test(
                "POST /api/contact",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("POST /api/contact", False, str(e))
    
    def test_admin_endpoints(self):
        """Test admin endpoints"""
        print(f"\n{BLUE}=== Testing Admin Endpoints ==={RESET}")
        
        if not self.admin_token:
            print(f"{YELLOW}⚠ Skipping admin tests (no admin token){RESET}")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test get all users
        try:
            response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
            self.print_test(
                "GET /api/admin/users",
                response.status_code == 200,
                f"Found {response.json().get('total', 0)} users"
            )
        except Exception as e:
            self.print_test("GET /api/admin/users", False, str(e))
        
        # Test create property
        try:
            property_data = {
                "title": "Test Property",
                "location": "Test Location",
                "description": "This is a test property",
                "status": "AVAILABLE",
                "image_urls": []
            }
            response = requests.post(
                f"{self.base_url}/api/admin/properties",
                json=property_data,
                headers=headers
            )
            self.print_test(
                "POST /api/admin/properties",
                response.status_code == 201,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("POST /api/admin/properties", False, str(e))
    
    def test_media_endpoints(self):
        """Test media upload endpoints"""
        print(f"\n{BLUE}=== Testing Media Upload Endpoints ==={RESET}")
        
        if not self.admin_token:
            print(f"{YELLOW}⚠ Skipping media tests (no admin token){RESET}")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test get image upload signature
        try:
            response = requests.get(
                f"{self.base_url}/api/media/upload-signature/image",
                headers=headers
            )
            self.print_test(
                "GET /api/media/upload-signature/image",
                response.status_code == 200,
                f"Signature generated" if response.status_code == 200 else f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("GET /api/media/upload-signature/image", False, str(e))
        
        # Test get video upload signature
        try:
            response = requests.get(
                f"{self.base_url}/api/media/upload-signature/video",
                headers=headers
            )
            self.print_test(
                "GET /api/media/upload-signature/video",
                response.status_code == 200,
                f"Signature generated" if response.status_code == 200 else f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("GET /api/media/upload-signature/video", False, str(e))
        
        # Test POST upload signature
        try:
            signature_data = {
                "property_id": 1,
                "resource_type": "image"
            }
            response = requests.post(
                f"{self.base_url}/api/media/upload-signature",
                json=signature_data,
                headers=headers
            )
            self.print_test(
                "POST /api/media/upload-signature",
                response.status_code == 200,
                f"Signature generated" if response.status_code == 200 else f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("POST /api/media/upload-signature", False, str(e))
    
    def test_investor_endpoints(self):
        """Test investor endpoints"""
        print(f"\n{BLUE}=== Testing Investor Endpoints ==={RESET}")
        
        if not self.investor_token:
            print(f"{YELLOW}⚠ Skipping investor tests (no investor token){RESET}")
            return
        
        headers = {"Authorization": f"Bearer {self.investor_token}"}
        
        # Test get my investments
        try:
            response = requests.get(
                f"{self.base_url}/api/investor/investments",
                headers=headers
            )
            self.print_test(
                "GET /api/investor/investments",
                response.status_code == 200,
                f"Found {response.json().get('total', 0)} investments"
            )
        except Exception as e:
            self.print_test("GET /api/investor/investments", False, str(e))
    
    def test_rbac(self):
        """Test role-based access control"""
        print(f"\n{BLUE}=== Testing RBAC ==={RESET}")
        
        # Test that non-admin cannot access admin endpoints
        if self.investor_token:
            try:
                headers = {"Authorization": f"Bearer {self.investor_token}"}
                response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
                self.print_test(
                    "RBAC: Investor blocked from admin endpoint",
                    response.status_code == 403,
                    f"Status: {response.status_code}"
                )
            except Exception as e:
                self.print_test("RBAC: Investor blocked from admin endpoint", False, str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}  Property Backend API - Endpoint Testing{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")
        
        self.test_health_check()
        self.test_signup_and_login()
        self.test_public_endpoints()
        self.test_admin_endpoints()
        self.test_media_endpoints()
        self.test_investor_endpoints()
        self.test_rbac()
        
        # Print summary
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}  Test Summary{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")
        print(f"{GREEN}Passed: {self.test_results['passed']}{RESET}")
        print(f"{RED}Failed: {self.test_results['failed']}{RESET}")
        total = self.test_results['passed'] + self.test_results['failed']
        percentage = (self.test_results['passed'] / total * 100) if total > 0 else 0
        print(f"Success Rate: {percentage:.1f}%\n")


if __name__ == "__main__":
    tester = APITester(BASE_URL)
    tester.run_all_tests()
