"""
Property Backend API Testing Script
Tests all endpoints: Auth, Properties, Investments, Inquiries, Shortlets, Media, Admin
"""
import requests
import json
from datetime import datetime, timedelta, timezone
import os
import psycopg2
from decimal import Decimal

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use system environment

# Base URL
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api"  # project uses /api (no /v1)

# Database connection helper
def get_db_connection():
    """Get database connection from environment variables"""
    try:
        # First try to parse DATABASE_URL if available
        database_url = os.getenv("DATABASE_URL", "")
        if database_url:
            # Parse postgresql://user:password@host:port/database
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5433,
                database=parsed.path.lstrip('/') if parsed.path else "propertydb",
                user=parsed.username,
                password=parsed.password
            )
        else:
            # Fallback to individual environment variables or defaults for local dev
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5433"),
                database=os.getenv("POSTGRES_DB", "propertydb"),
                user=os.getenv("POSTGRES_USER", "propertyuser"),
                password=os.getenv("POSTGRES_PASSWORD", "propertypass")
            )
        return conn
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        return None

def verify_user_in_db(user_email):
    """Directly verify user in database by setting is_verified=True"""
    conn = get_db_connection()
    if not conn:
        print_warning("Could not connect to database for verification")
        return False
    
    try:
        cursor = conn.cursor()
        # Update the user's is_verified status
        cursor.execute(
            "UPDATE users SET is_verified = TRUE WHERE email = %s",
            (user_email,)
        )
        conn.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        if rows_affected > 0:
            print_success(f"User {user_email} verified in database")
            return True
        else:
            print_warning(f"No user found with email {user_email}")
            return False
    except Exception as e:
        print_error(f"Database verification error: {str(e)}")
        if conn:
            conn.close()
        return False

def make_user_admin(user_email):
    """Make user an admin in the database"""
    conn = get_db_connection()
    if not conn:
        print_warning("Could not connect to database to make user admin")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_admin = TRUE WHERE email = %s",
            (user_email,)
        )
        conn.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        if rows_affected > 0:
            print_success(f"User {user_email} is now an admin")
            return True
        else:
            print_warning(f"No user found with email {user_email}")
            return False
    except Exception as e:
        print_error(f"Database admin update error: {str(e)}")
        if conn:
            conn.close()
        return False

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}[+] {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}[X] {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}[i] {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}[!] {message}{Colors.END}")

def print_section(message):
    print(f"\n{Colors.MAGENTA}{'='*60}{Colors.END}")
    print(f"{Colors.MAGENTA}{message}{Colors.END}")
    print(f"{Colors.MAGENTA}{'='*60}{Colors.END}")

# Global variable to store tokens
auth_tokens = {
    "access_token": None,
    "refresh_token": None,
    "user_id": None,
    "admin_access_token": None
}

# Global storage for created resources
test_resources = {
    "property_id": None,
    "property_ids": [],
    "investment_id": None,
    "investment_ids": [],
    "investment_application_id": None,
    "inquiry_id": None,
    "inquiry_ids": [],
    "wishlist_property_id": None,
    "update_id": None,
    "update_ids": [],
    "occupancy_id": None,
    "revenue_id": None,
    "distribution_id": None,
    "distribution_ids": [],
    "media_url": None,
    "media_urls": [],
    "user_email": None
}

def get_headers():
    """Get authorization headers"""
    return {
        "Authorization": f"Bearer {auth_tokens['access_token']}",
        "Content-Type": "application/json"
    }

def get_admin_headers():
    """Get admin authorization headers"""
    return {
        "Authorization": f"Bearer {auth_tokens['admin_access_token']}",
        "Content-Type": "application/json"
    }

# ============================================================================
# AUTHENTICATION & SETUP
# ============================================================================

def test_register():
    """Test user registration"""
    print_section("Testing User Registration")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    user_data = {
        "email": f"property-test-{timestamp}@example.com",
        "password": "TestPassword123!",
        "full_name": "Property Test User",
        "phone": f"+234801234{timestamp[-4:]}"
    }
    
    try:
        response = requests.post(f"{API_V1}/auth/signup", json=user_data)
        if response.status_code in [200, 201]:
            data = response.json()
            auth_tokens["user_id"] = data.get("id")
            test_resources["user_email"] = user_data["email"]
            print_success("User registration successful")
            print_info(f"User ID: {data.get('id')}")
            print_info(f"Email: {data.get('email')}")
            
            # Verify user directly in database
            verify_user_in_db(user_data["email"])
            
            return True, user_data
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print_error(f"Registration error: {str(e)}")
        return False, None

def test_login(user_data):
    """Test user login"""
    print_section("Testing User Login")
    
    if not user_data:
        print_error("No user data available for login")
        return False
    
    # FastAPI OAuth2 uses form data for login
    login_data = {
        "username": user_data["email"],  # OAuth2 uses 'username' field
        "password": user_data["password"]
    }
    
    try:
        # Use form data instead of JSON
        response = requests.post(
            f"{API_V1}/auth/login",
            data=login_data,  # form data
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Login successful")
            print_info(f"Access token received: {data.get('access_token')[:20]}...")
            auth_tokens["access_token"] = data.get("access_token")
            auth_tokens["refresh_token"] = data.get("refresh_token")
            return True
        else:
            print_error(f"Login failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return False

def test_admin_login():
    """Test admin login"""
    print_section("Testing Admin Login")
    
    admin_email = os.getenv("ADMIN_EMAIL", "akanmuibro@gmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "@Timileyin42")
    
    login_data = {
        "username": admin_email,
        "password": admin_password
    }
    
    try:
        response = requests.post(
            f"{API_V1}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Admin login successful")
            print_info(f"Admin access token received: {data.get('access_token')[:20]}...")
            auth_tokens["admin_access_token"] = data.get("access_token")
            return True
        else:
            print_error(f"Admin login failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Admin login error: {str(e)}")
        return False

def test_get_current_user():
    """Test getting current user profile"""
    print_section("Testing Get Current User")
    
    try:
        response = requests.get(f"{API_V1}/auth/me", headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            print_success("Current user retrieved successfully")
            print_info(f"User: {data.get('full_name')} ({data.get('email')})")
            print_info(f"Role: {'Admin' if data.get('is_admin') else 'User'}")
            return True
        else:
            print_error(f"Get current user failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get current user error: {str(e)}")
        return False

def test_refresh_token():
    """Test token refresh"""
    print_section("Testing Token Refresh")
    
    if not auth_tokens["refresh_token"]:
        print_warning("No refresh token available")
        return False
    
    try:
        response = requests.post(
            f"{API_V1}/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]}
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Token refresh successful")
            auth_tokens["access_token"] = data.get("access_token")
            return True
        else:
            print_error(f"Token refresh failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Token refresh error: {str(e)}")
        return False

# ============================================================================
# PUBLIC ENDPOINTS (No Authentication Required)
# ============================================================================

def test_get_public_properties():
    """Test getting public properties list"""
    print_section("Testing Get Public Properties")
    
    try:
        response = requests.get(f"{API_V1}/properties")
        if response.status_code == 200:
            data = response.json()
            print_success("Public properties retrieved successfully")
            print_info(f"Total properties: {data.get('total', 0)}")
            properties = data.get('properties') or []
            if properties:
                print_info(f"First property: {properties[0].get('title')}")
            return True
        else:
            print_error(f"Get public properties failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get public properties error: {str(e)}")
        return False

def test_get_featured_properties():
    """Test getting featured properties"""
    print_section("Testing Get Featured Properties")
    
    try:
        response = requests.get(f"{API_V1}/public/properties/featured")
        if response.status_code == 200:
            data = response.json()
            print_success("Featured properties retrieved successfully")
            print_info(f"Featured count: {len(data)}")
            return True
        else:
            print_error(f"Get featured properties failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get featured properties error: {str(e)}")
        return False

# ============================================================================
# ADMIN - PROPERTY MANAGEMENT
# ============================================================================

def test_admin_create_property():
    """Test admin creating a property"""
    print_section("Testing Admin Create Property")
    
    property_data = {
        "title": f"Luxury Apartment {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "description": "Beautiful apartment in prime location with modern amenities",
        "location": "Lekki Phase 1, Lagos",
        "status": "AVAILABLE",
        "image_urls": ["https://example.com/property1.jpg", "https://example.com/property2.jpg"],
        "bedrooms": 3,
        "bathrooms": 3,
        "area_sqft": 1800.0,
        "expected_roi": 12.5,
        "total_fractions": 1000,
        "fraction_price": 500000.0,
        "project_value": 500000000.0
    }
    
    try:
        response = requests.post(
            f"{API_V1}/admin/properties",
            json=property_data,
            headers=get_admin_headers()
        )
        if response.status_code in [200, 201]:
            data = response.json()
            test_resources["property_id"] = data.get("id")
            test_resources["property_ids"].append(data.get("id"))
            print_success("Property created successfully")
            print_info(f"Property ID: {data.get('id')}")
            print_info(f"Title: {data.get('title')}")
            price_display = data.get('fraction_price') or data.get('project_value') or 'n/a'
            print_info(f"Price info: {price_display}")
            return True
        else:
            print_error(f"Create property failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Create property error: {str(e)}")
        return False


def test_admin_get_media_upload_signature():
    """Test admin requesting media upload signature for property images"""
    print_section("Testing Admin Media Upload Signature")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    payload = {
        "property_id": test_resources["property_id"],
        "resource_type": "image"
    }
    try:
        response = requests.post(
            f"{API_V1}/media/upload-signature",
            json=payload,
            headers=get_admin_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Media upload signature retrieved")
            print_info(f"Folder: {data.get('folder')}")
            print_info(f"Upload URL: {data.get('upload_url')}")
            return True
        else:
            print_error(f"Media signature failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Media signature error: {str(e)}")
        return False

def test_admin_get_properties():
    """Test admin getting all properties"""
    print_section("Testing Admin Get All Properties")
    
    try:
        response = requests.get(f"{API_V1}/admin/properties", headers=get_admin_headers())
        if response.status_code == 200:
            data = response.json()
            print_success("Admin properties retrieved successfully")
            print_info(f"Total properties: {data.get('total', 0)}")
            return True
        else:
            print_error(f"Admin get properties failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Admin get properties error: {str(e)}")
        return False

def test_admin_update_property():
    """Test admin updating a property"""
    print_section("Testing Admin Update Property")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    update_data = {
        "title": f"Updated Luxury Apartment {datetime.now().strftime('%H%M%S')}",
        "expected_roi": 16.0,
        "status": "AVAILABLE"
    }
    
    try:
        response = requests.patch(
            f"{API_V1}/admin/properties/{test_resources['property_id']}",
            json=update_data,
            headers=get_admin_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Property updated successfully")
            print_info(f"New title: {data.get('title')}")
            print_info(f"New ROI: {data.get('annual_roi')}%")
            return True
        else:
            print_error(f"Update property failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Update property error: {str(e)}")
        return False

def test_admin_get_property_details():
    """Test admin getting property details"""
    print_section("Testing Admin Get Property Details")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    try:
        response = requests.get(
            f"{API_V1}/admin/properties/{test_resources['property_id']}",
            headers=get_admin_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Property details retrieved successfully")
            print_info(f"Title: {data.get('title')}")
            print_info(f"Status: {data.get('status')}")
            return True
        else:
            print_error(f"Get property details failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get property details error: {str(e)}")
        return False

# ============================================================================
# ADMIN - INVESTMENT MANAGEMENT
# ============================================================================

def test_admin_get_investments():
    """Test admin getting all investments"""
    print_section("Testing Admin Get All Investments")
    try:
        response = requests.get(f"{API_V1}/admin/investments", headers=get_admin_headers())
        if response.status_code == 200:
            data = response.json()
            print_success("Admin investments retrieved successfully")
            print_info(f"Total investments: {data.get('total', 0)}")
            return True
        else:
            print_error(f"Admin get investments failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Admin get investments error: {str(e)}")
        return False

def test_admin_get_investment_applications():
    """Test admin getting investment applications"""
    print_section("Testing Admin Get Investment Applications")
    
    try:
        response = requests.get(
            f"{API_V1}/admin/investment-applications",
            headers=get_admin_headers()
        )
        if response.status_code == 200:
            data = response.json()
            # Endpoint returns a list
            if isinstance(data, list):
                print_success("Investment applications retrieved successfully")
                print_info(f"Total applications: {len(data)}")
            else:
                print_success("Investment applications retrieved successfully")
                print_info(f"Response type: {type(data)}")
            return True
        else:
            print_error(f"Get applications failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get applications error: {str(e)}")
        return False

# ============================================================================
# ADMIN - PROPERTY UPDATES
# ============================================================================

def test_admin_create_property_update():
    """Test admin creating property update"""
    print_section("Testing Admin Create Property Update")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    update_data = {
        "property_id": test_resources["property_id"],
        "title": "Construction Progress Update",
        "content": "Foundation work completed. Moving to first floor construction.",
        "update_type": "progress",
        "images": ["https://example.com/progress1.jpg"]
    }
    
    try:
        response = requests.post(
            f"{API_V1}/admin/updates",
            json=update_data,
            headers=get_admin_headers()
        )
        if response.status_code in [200, 201]:
            data = response.json()
            test_resources["update_id"] = data.get("id")
            test_resources["update_ids"].append(data.get("id"))
            print_success("Property update created successfully")
            print_info(f"Update ID: {data.get('id')}")
            print_info(f"Title: {data.get('title')}")
            return True
        else:
            print_error(f"Create update failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Create update error: {str(e)}")
        return False

def test_admin_get_property_updates():
    """Test admin getting property updates"""
    print_section("Testing Admin Get Property Updates")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    try:
        response = requests.get(
            f"{API_V1}/admin/properties/{test_resources['property_id']}/updates",
            headers=get_admin_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Property updates retrieved successfully")
            print_info(f"Total updates: {len(data)}")
            return True
        else:
            print_error(f"Get updates failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get updates error: {str(e)}")
        return False

# ============================================================================
# ADMIN - OCCUPANCY & REVENUE TRACKING
# ============================================================================

def test_admin_add_occupancy_data():
    """Test admin adding occupancy data"""
    print_section("Testing Admin Add Occupancy Data")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    occupancy_data = {
        "property_id": test_resources["property_id"],
        "month": datetime.now().month,
        "year": datetime.now().year,
        "nights_booked": 24,
        "nights_available": 30,
        "notes": "High occupancy during holiday season"
    }
    
    try:
        response = requests.post(
            f"{API_V1}/admin/shortlet/occupancy",
            json=occupancy_data,
            headers=get_admin_headers()
        )
        if response.status_code in [200, 201]:
            data = response.json()
            test_resources["occupancy_id"] = data.get("id")
            print_success("Occupancy data added successfully")
            print_info(f"Occupancy rate: {data.get('occupancy_rate')}%")
            return True
        else:
            print_error(f"Add occupancy failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Add occupancy error: {str(e)}")
        return False

def test_admin_add_revenue_data():
    """Test admin adding revenue data"""
    print_section("Testing Admin Add Revenue Data")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    revenue_data = {
        "property_id": test_resources["property_id"],
        "month": datetime.now().month,
        "year": datetime.now().year,
        "gross_revenue": 2500000.00,
        "expenses": 350000.00,
        "notes": "Monthly rental collection"
    }
    
    try:
        response = requests.post(
            f"{API_V1}/admin/shortlet/revenue",
            json=revenue_data,
            headers=get_admin_headers()
        )
        if response.status_code in [200, 201]:
            data = response.json()
            test_resources["revenue_id"] = data.get("id")
            print_success("Revenue data added successfully")
            net_income = data.get('net_income')
            print_info(f"Revenue net income: {net_income}")
            return True
        else:
            print_error(f"Add revenue failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Add revenue error: {str(e)}")
        return False

# ============================================================================
# ADMIN - INQUIRIES MANAGEMENT
# ============================================================================

def test_admin_get_inquiries():
    """Test admin getting all inquiries"""
    print_section("Testing Admin Get All Inquiries")
    
    try:
        response = requests.get(f"{API_V1}/admin/inquiries", headers=get_admin_headers())
        if response.status_code == 200:
            data = response.json()
            print_success("Inquiries retrieved successfully")
            print_info(f"Total inquiries: {data.get('total', 0)}")
            return True
        else:
            print_error(f"Get inquiries failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get inquiries error: {str(e)}")
        return False

def test_admin_update_inquiry_status():
    """Test admin updating inquiry status"""
    print_section("Testing Admin Update Inquiry Status")
    
    if not test_resources["inquiry_id"]:
        print_warning("No inquiry ID available")
        return False
    
    try:
        response = requests.patch(
            f"{API_V1}/admin/inquiries/{test_resources['inquiry_id']}",
            json={"status": "CONTACTED"},
            headers=get_admin_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Inquiry status updated successfully")
            print_info(f"New status: {data.get('status')}")
            return True
        else:
            print_error(f"Update inquiry status failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Update inquiry status error: {str(e)}")
        return False

# ============================================================================
# INVESTOR - PROPERTY BROWSING
# ============================================================================

def test_investor_get_properties():
    """Test investor getting properties"""
    print_section("Testing Investor Get Properties")
    
    try:
        response = requests.get(f"{API_V1}/properties", headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            print_success("Investor properties retrieved successfully")
            print_info(f"Total properties: {data.get('total', 0)}")
            return True
        else:
            print_error(f"Get properties failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get properties error: {str(e)}")
        return False

def test_investor_get_property_details():
    """Test investor getting property details"""
    print_section("Testing Investor Get Property Details")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    try:
        response = requests.get(
            f"{API_V1}/properties/{test_resources['property_id']}",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Property details retrieved successfully")
            print_info(f"Title: {data.get('title')}")
            print_info(f"Status: {data.get('status')}")
            return True
        else:
            print_error(f"Get property details failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get property details error: {str(e)}")
        return False

# ============================================================================
# INVESTOR - INVESTMENT OPERATIONS
# ============================================================================

def test_investor_create_investment():
    """Test investor creating an investment"""
    print_section("Testing Investor Create Investment")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    investment_data = {
        "property_id": test_resources["property_id"],
        "units_purchased": 2,
        "payment_method": "bank_transfer",
        "payment_reference": f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }
    
    try:
        response = requests.post(
            f"{API_V1}/investor/investments",
            json=investment_data,
            headers=get_headers()
        )
        if response.status_code in [200, 201]:
            data = response.json()
            test_resources["investment_id"] = data.get("id")
            test_resources["investment_ids"].append(data.get("id"))
            print_success("Investment created successfully")
            print_info(f"Investment ID: {data.get('id')}")
            print_info(f"Units: {data.get('units_purchased')}")
            print_info(f"Total amount: ₦{data.get('total_amount'):,.2f}")
            return True
        else:
            print_error(f"Create investment failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Create investment error: {str(e)}")
        return False

def test_investor_get_my_investments():
    """Test investor getting their investments"""
    print_section("Testing Investor Get My Investments")
    
    try:
        response = requests.get(f"{API_V1}/investor/my-investments", headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            print_success("My investments retrieved successfully")
            print_info(f"Total investments: {data.get('total', 0)}")
            return True
        else:
            print_error(f"Get my investments failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get my investments error: {str(e)}")
        return False

def test_investor_get_investment_details():
    """Test investor getting investment details"""
    print_section("Testing Investor Get Investment Details")
    
    if not test_resources["investment_id"]:
        print_warning("No investment ID available")
        return False
    
    try:
        response = requests.get(
            f"{API_V1}/investor/investments/{test_resources['investment_id']}",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Investment details retrieved successfully")
            print_info(f"Property: {data.get('property', {}).get('title', 'N/A')}")
            print_info(f"Units: {data.get('units_purchased')}")
            return True
        else:
            print_error(f"Get investment details failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get investment details error: {str(e)}")
        return False

# ============================================================================
# INVESTOR - WISHLIST
# ============================================================================

def test_investor_add_to_wishlist():
    """Test investor adding property to wishlist"""
    print_section("Testing Investor Add to Wishlist")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    try:
        response = requests.post(
            f"{API_V1}/user/wishlist",
            json={"property_id": test_resources['property_id']},
            headers=get_headers()
        )
        if response.status_code in [200, 201]:
            print_success("Property added to wishlist successfully")
            test_resources["wishlist_property_id"] = test_resources["property_id"]
            return True
        else:
            print_error(f"Add to wishlist failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Add to wishlist error: {str(e)}")
        return False

def test_investor_get_wishlist():
    """Test investor getting wishlist"""
    print_section("Testing Investor Get Wishlist")
    
    try:
        response = requests.get(f"{API_V1}/user/wishlist", headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            print_success("Wishlist retrieved successfully")
            print_info(f"Wishlist items: {len(data)}")
            return True
        else:
            print_error(f"Get wishlist failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get wishlist error: {str(e)}")
        return False

def test_investor_remove_from_wishlist():
    """Test investor removing property from wishlist"""
    print_section("Testing Investor Remove from Wishlist")
    
    if not test_resources["wishlist_property_id"]:
        print_warning("No wishlist property ID available")
        return False
    
    try:
        response = requests.delete(
            f"{API_V1}/user/wishlist/{test_resources['wishlist_property_id']}",
            headers=get_headers()
        )
        if response.status_code in [200, 204]:
            print_success("Property removed from wishlist successfully")
            return True
        else:
            print_error(f"Remove from wishlist failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Remove from wishlist error: {str(e)}")
        return False

# ============================================================================
# INQUIRIES
# ============================================================================

def test_create_inquiry():
    """Test creating a property inquiry"""
    print_section("Testing Create Property Inquiry")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available")
        return False
    
    inquiry_data = {
        "property_id": test_resources["property_id"],
        "message": "I'm interested in learning more about this property investment opportunity."
    }
    
    try:
        response = requests.post(
            f"{API_V1}/user/inquiries",
            json=inquiry_data,
            headers=get_headers()
        )
        if response.status_code in [200, 201]:
            data = response.json()
            test_resources["inquiry_id"] = data.get("id")
            test_resources["inquiry_ids"].append(data.get("id"))
            print_success("Inquiry created successfully")
            print_info(f"Inquiry ID: {data.get('id')}")
            return True
        else:
            print_error(f"Create inquiry failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Create inquiry error: {str(e)}")
        return False

def test_get_my_inquiries():
    """Test getting user's inquiries"""
    print_section("Testing Get My Inquiries")
    
    try:
        response = requests.get(f"{API_V1}/user/inquiries", headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            print_success("My inquiries retrieved successfully")
            print_info(f"Total inquiries: {data.get('total', 0)}")
            return True
        else:
            print_error(f"Get my inquiries failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get my inquiries error: {str(e)}")
        return False

# ============================================================================
# SHORTLET EARNINGS (INVESTOR)
# ============================================================================

def test_investor_get_shortlet_earnings():
    """Test investor getting shortlet earnings"""
    print_section("Testing Investor Get Shortlet Earnings")
    
    try:
        response = requests.get(
            f"{API_V1}/investor/shortlet/earnings",
            headers=get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Shortlet earnings retrieved successfully")
            print_info(f"Total earnings records: {len(data)}")
            return True
        else:
            print_error(f"Get shortlet earnings failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get shortlet earnings error: {str(e)}")
        return False

# ============================================================================
# ADMIN - SHORTLET DISTRIBUTION
# ============================================================================

def test_admin_create_earnings_distribution():
    """Test admin creating earnings distribution"""
    print_section("Testing Admin Create Earnings Distribution")
    
    if not test_resources.get("revenue_id"):
        print_warning("No revenue ID available")
        return False
    
    try:
        response = requests.post(
            f"{API_V1}/admin/shortlet/revenue/{test_resources['revenue_id']}/distribute",
            headers=get_admin_headers()
        )
        if response.status_code in [200, 201]:
            data = response.json()
            distributions_count = data.get("distributions_count", 0)
            print_success("Earnings distribution created successfully")
            print_info(f"Distributions created: {distributions_count}")
            if "total_distributed" in data:
                print_info(f"Total distributed: ₦{data.get('total_distributed'):,.2f}")
            return True
        elif response.status_code == 400 and "No investments found" in response.text:
            print_warning("Skipped distribution: no investments for this property yet")
            return True
        else:
            print_error(f"Create distribution failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Create distribution error: {str(e)}")
        return False

def test_admin_get_distributions():
    """Test admin getting all distributions"""
    print_section("Testing Admin Get All Distributions")
    
    try:
        response = requests.get(
            f"{API_V1}/admin/shortlet/distributions",
            headers=get_admin_headers()
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Distributions retrieved successfully")
            print_info(f"Total distributions: {data.get('total', 0)}")
            return True
        else:
            print_error(f"Get distributions failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get distributions error: {str(e)}")
        return False

# ============================================================================
# CLEANUP
# ============================================================================

def test_admin_delete_property():
    """Test admin deleting a property (cleanup)"""
    print_section("Testing Admin Delete Property (Cleanup)")
    
    if not test_resources["property_id"]:
        print_warning("No property ID available for deletion")
        return False
    
    try:
        response = requests.delete(
            f"{API_V1}/admin/properties/{test_resources['property_id']}",
            headers=get_admin_headers()
        )
        if response.status_code in [200, 204]:
            print_success("Property deleted successfully")
            return True
        else:
            print_error(f"Delete property failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Delete property error: {str(e)}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all API tests in sequence"""
    print("\n" + "="*60)
    print(f"{Colors.CYAN}PROPERTY BACKEND API TESTING SUITE{Colors.END}")
    print(f"{Colors.CYAN}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print("="*60)
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # Phase 1: Authentication & Setup
    print_section("PHASE 1: AUTHENTICATION & SETUP")
    success, user_data = test_register()
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        print_error("Cannot continue without registration")
        return test_results
    
    success = test_login(user_data)
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        print_error("Cannot continue without login")
        return test_results
    
    # Get current user
    if test_get_current_user():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    # Admin login
    success = test_admin_login()
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        print_warning("Admin tests will be skipped")
    
    # Phase 2: Public Endpoints
    print_section("PHASE 2: PUBLIC ENDPOINTS")
    if test_get_public_properties():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    # Phase 3: Admin - Property Management
    if auth_tokens["admin_access_token"]:
        print_section("PHASE 3: ADMIN - PROPERTY MANAGEMENT")
        
        if test_admin_create_property():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1

        if test_admin_get_media_upload_signature():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        if test_admin_update_property():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        # Phase 4: Admin - Updates, Occupancy, Revenue
        print_section("PHASE 4: ADMIN - UPDATES & TRACKING")
        
        if test_admin_create_property_update():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        if test_admin_add_occupancy_data():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        if test_admin_add_revenue_data():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
    
    # Phase 5: Investor - Property Browsing
    print_section("PHASE 5: INVESTOR - PROPERTY BROWSING")
    
    if test_investor_get_properties():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    if test_investor_get_property_details():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    # Phase 7: Investor - Wishlist
    print_section("PHASE 6: INVESTOR - WISHLIST")
    
    if test_investor_add_to_wishlist():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    if test_investor_get_wishlist():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    if test_investor_remove_from_wishlist():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    # Phase 8: Inquiries
    print_section("PHASE 8: INQUIRIES")
    
    if test_create_inquiry():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    if test_get_my_inquiries():
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    if auth_tokens["admin_access_token"]:
        if test_admin_get_inquiries():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        if test_admin_update_inquiry_status():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
    
    # Phase 9: Shortlet Earnings (admin only in this suite)
    print_section("PHASE 9: SHORTLET EARNINGS")
    
    if auth_tokens["admin_access_token"]:
        if test_admin_create_earnings_distribution():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        if test_admin_get_distributions():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        # Phase 10: Admin - Investments
        print_section("PHASE 10: ADMIN - INVESTMENTS")
        
        if test_admin_get_investments():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        if test_admin_get_investment_applications():
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
    
    # Cleanup (optional - comment out if you want to keep test data)
    # if auth_tokens["admin_access_token"]:
    #     print_section("CLEANUP")
    #     if test_admin_delete_property():
    #         test_results["passed"] += 1
    #     else:
    #         test_results["failed"] += 1
    
    # Print summary
    print("\n" + "="*60)
    print(f"{Colors.CYAN}TEST SUMMARY{Colors.END}")
    print("="*60)
    print_success(f"Passed: {test_results['passed']}")
    print_error(f"Failed: {test_results['failed']}")
    print_warning(f"Skipped: {test_results['skipped']}")
    print(f"\nTotal: {sum(test_results.values())} tests")
    print(f"Success Rate: {(test_results['passed'] / sum(test_results.values()) * 100):.2f}%")
    print(f"\n{Colors.CYAN}Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print("="*60 + "\n")
    
    return test_results

if __name__ == "__main__":
    try:
        results = run_all_tests()
        # Exit with error code if any tests failed
        exit(0 if results["failed"] == 0 else 1)
    except KeyboardInterrupt:
        print_warning("\n\nTest execution interrupted by user")
        exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
