# 🏘️ Plug of Lagos Property - Backend API

A production-ready FastAPI backend for a real estate investment platform with role-based access control, admin-managed investor assignments, and property valuation tracking.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Deployment](#deployment)

---

## 🎯 Overview

The Plug of Lagos Property platform enables:

- **Public Access**: Browse available properties and updates
- **User Signup**: Anyone can create an account
- **Admin Control**: Admins promote users to investors and assign investments
- **Investor Dashboard**: Track portfolio growth and valuations

### Key Business Logic

```mermaid
graph LR
    A[Public User] -->|Signup| B[USER Role]
    B -->|Admin Approval| C[INVESTOR Role]
    C -->|Admin Assigns| D[Investment]
    E[ADMIN] -->|Manages| F[Properties]
    E -->|Updates| G[Valuations]
```

---

## 🏗️ Architecture

### System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser]
        B[Mobile App]
    end
    
    subgraph "API Layer"
        C[FastAPI Application]
        D[CORS Middleware]
        E[JWT Authentication]
    end
    
    subgraph "Business Logic"
        F[Auth Service]
        G[Property Service]
        H[Investment Service]
        I[User Service]
    end
    
    subgraph "Data Layer"
        J[(PostgreSQL Database)]
    end
    
    A --> D
    B --> D
    D --> C
    C --> E
    E --> F
    E --> G
    E --> H
    E --> I
    F --> J
    G --> J
    H --> J
    I --> J
```

### Role-Based Access Control

```mermaid
graph TD
    A[Request] --> B{Authenticated?}
    B -->|No| C[401 Unauthorized]
    B -->|Yes| D{Check Role}
    D -->|PUBLIC/USER| E[Public Endpoints Only]
    D -->|INVESTOR| F[Investor Endpoints + Public]
    D -->|ADMIN| G[All Endpoints]
    E --> H[Properties, Updates]
    F --> I[My Investments]
    G --> J[User Management, Property CRUD, Investment Assignment]
```

### Investment Flow

```mermaid
sequenceDiagram
    participant U as User
    participant A as Admin
    participant S as System
    participant D as Database
    
    U->>S: Express Interest
    Note over U,S: Offline verification
    A->>S: Login as Admin
    A->>S: Promote User to INVESTOR
    S->>D: Update user.role = INVESTOR
    A->>S: Assign Investment
    S->>D: Create Investment Record
    U->>S: Login as Investor
    U->>S: View My Investments
    S->>D: Query Investments
    D->>S: Return Portfolio
    S->>U: Display Growth & Valuations
```

---

## ✨ Features

### Public Features
- ✅ Browse available properties
- ✅ View property details
- ✅ Read property updates/news
- ✅ Express interest form

### Authentication

- ✅ Email/password signup
- ✅ **OAuth2 password flow** - FastAPI standard
- ✅ JWT-based authentication (access + refresh tokens)
- ✅ Secure password hashing (bcrypt)
- ✅ **Auto-admin creation** - Admin user created from `.env` on startup

> **Note**: The login endpoint uses OAuth2 password flow. In the request, use `username` (not `email`) and `password` as form data fields. The `username` field should contain the user's email address.

### Admin Features
- ✅ User management
- ✅ Promote users to investors
- ✅ Create/edit/delete properties
- ✅ Assign investments to investors
- ✅ Update property valuations
- ✅ Post property updates/news

### Investor Features
- ✅ View investment portfolio
- ✅ Track growth percentage
- ✅ View detailed property information
- ✅ Real-time valuation updates

---

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic 1.13
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Validation**: Pydantic 2.5
- **Containerization**: Docker & Docker Compose

---

## 🚀 Getting Started

### Prerequisites

- Docker Desktop installed
- Git
- Python 3.11+ (for local development)

### Important: Admin User Auto-Creation

The application automatically creates an admin user on startup using credentials from the `.env` file. This means:

1. **No manual admin creation needed** - The admin user is created automatically
2. **Idempotent** - If the admin already exists, it skips creation
3. **Configurable** - Set admin credentials in `.env` file

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Property-backend
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update the `SECRET_KEY`:
   ```env
   SECRET_KEY=your-super-secret-key-min-32-characters-long
   ```

3. **Start the services**
   ```bash
   docker-compose up --build
   ```
   
   > **Note**: Migrations run automatically via the entrypoint script. No manual migration step needed!

4. **Wait for services to be ready**
   - Database will initialize
   - **Migrations will run automatically** (via entrypoint.sh)
   - Admin user will be created automatically
   - API will start on http://localhost:8000

5. **Seed the database** (in a new terminal)
   ```bash
   docker-compose exec app python seed_data.py
   ```

6. **Access the API**
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

### Local Development (without Docker)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL locally**
   ```bash
   # Update DATABASE_URL in .env to point to your local PostgreSQL
   DATABASE_URL=postgresql://user:password@localhost:5432/propertydb
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Seed database**
   ```bash
   python seed_data.py
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/signup` | Create new user account | No |
| POST | `/api/auth/login` | Login and get JWT tokens | No |
| GET | `/api/auth/me` | Get current user info | Yes |
| POST | `/api/auth/logout` | Logout (client-side) | Yes |

### Public Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/properties` | List available properties | No |
| GET | `/api/properties/{id}` | Get property details | No |
| GET | `/api/updates` | List property updates | No |
| POST | `/api/contact` | Express interest form | No |

### Admin Endpoints (Requires ADMIN role)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users` | List all users |
| PATCH | `/api/admin/users/{id}/role` | Update user role |
| POST | `/api/admin/properties` | Create property |
| PATCH | `/api/admin/properties/{id}` | Update property |
| DELETE | `/api/admin/properties/{id}` | Delete property |
| POST | `/api/admin/investments` | Assign investment |
| PATCH | `/api/admin/investments/{id}/valuation` | Update valuation |
| POST | `/api/admin/updates` | Post property update |

### Investor Endpoints (Requires INVESTOR role)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/investor/investments` | Get my investments |
| GET | `/api/investor/investments/{id}` | Get investment details |

### Example Requests

#### Signup


## 🗄️ Database Schema

```mermaid
erDiagram
    USERS ||--o{ INVESTMENTS : has
    PROPERTIES ||--o{ INVESTMENTS : receives
    PROPERTIES ||--o{ UPDATES : has
    
    USERS {
        int id PK
        string email UK
        string password_hash
        string full_name
        string phone
        enum role
        timestamp created_at
        timestamp updated_at
    }
    
    PROPERTIES {
        int id PK
        string title
        string location
        text description
        enum status
        array image_urls
        timestamp created_at
        timestamp updated_at
    }
    
    INVESTMENTS {
        int id PK
        int user_id FK
        int property_id FK
        float initial_value
        float current_value
        timestamp created_at
        timestamp updated_at
    }
    
    UPDATES {
        int id PK
        int property_id FK
        string title
        text content
        timestamp created_at
        timestamp updated_at
    }
```

### User Roles
- `PUBLIC` - Not logged in
- `USER` - Signed up but not an investor
- `INVESTOR` - Approved investor
- `ADMIN` - Internal staff

### Property Status
- `AVAILABLE` - Available for investment
- `SOLD` - Fully sold
- `INVESTED` - Has active investments

---

## 🧪 Testing

### Run Automated Tests

```bash
# Make sure the application is running
docker-compose up -d

# Run the test script
python test_endpoints.py
```

### Manual Testing with Swagger UI

1. Navigate to http://localhost:8000/docs
2. Use the "Authorize" button to add your JWT token
3. Test endpoints interactively

### OAuth2 Authentication

This API uses **OAuth2 password flow** (FastAPI standard):

- **Login endpoint**: `/api/auth/login`
- **Token URL**: `/api/auth/login` (used by Swagger UI)
- **Form fields**: `username` (email) and `password`
- **Response**: JWT access token and refresh token

**Important**: When calling the login endpoint:
- Use `application/x-www-form-urlencoded` content type
- Send `username` (not `email`) and `password` as form data
- The `username` field should contain the user's email address

This allows seamless integration with:
- FastAPI's interactive docs (Swagger UI "Authorize" button)
- OAuth2 client libraries
- Standard authentication flows

## 🚢 Deployment

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t property-backend:latest .
   ```

2. **Run with docker-compose**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

### Environment Variables for Production


### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## 📁 Project Structure

```
Property-backend/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── auth.py            # Authentication routes
│   │   ├── public.py          # Public routes
│   │   ├── admin.py           # Admin routes
│   │   └── investor.py        # Investor routes
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database connection
│   │   ├── security.py        # JWT & password hashing
│   │   └── permissions.py     # RBAC
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── investment.py
│   │   └── update.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── investment.py
│   │   └── update.py
│   ├── utils/                  # Utilities
│   │   ├── hashing.py
│   │   └── pagination.py
│   └── main.py                 # FastAPI app
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── seed_data.py               # Database seeding
├── test_endpoints.py          # API testing
└── README.md
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

## 📄 License

This project is proprietary and confidential.

