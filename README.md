# Mental Health Wellness Center - Employee Tracking System

A production-ready Django REST API backend for tracking mental health practitioners' visits to client locations. This system provides GPS-based clock in/out functionality with comprehensive session management and administrative oversight.

## 🏥 Overview

This application is designed for mental health wellness centers to track when practitioners visit client locations, ensuring accurate billing, compliance, and safety monitoring. The system uses GPS coordinates to verify practitioner locations and provides real-time session tracking.

## ✨ Key Features

### 📱 Mobile App Support
- **Phone Number Authentication**: Practitioners log in using their unique phone numbers
- **GPS-Based Clock In/Out**: Real-time location tracking with accuracy verification
- **Offline Resilience**: Automatic session timeout and recovery for connectivity issues
- **Emergency Features**: Emergency session termination and safety monitoring

### 👥 User Management
- **Custom User Model**: Phone number as primary identifier
- **Role-Based Access**: Practitioners, supervisors, and administrators
- **Department Organization**: Hierarchical access control
- **Profile Management**: Complete practitioner profiles with emergency contacts

### 📍 Location Tracking
- **Client Location Database**: Complete client address and GPS coordinates
- **GPS Verification**: Automatic verification of practitioner location against client location
- **Location Updates**: Periodic location tracking during active sessions
- **Distance Calculation**: Haversine formula for accurate distance measurement

### 📊 Session Management
- **Complete Session Lifecycle**: Clock in, active monitoring, clock out
- **Service Type Tracking**: Different types of services provided
- **Duration Calculation**: Automatic session duration in minutes and hours
- **Session Notes**: Detailed notes and documentation
- **Status Tracking**: Active, completed, disconnected, auto-clocked-out

### 🔧 Administrative Features
- **Django Admin Integration**: Full administrative interface
- **Session Review System**: Supervisor review of flagged sessions
- **Reporting & Analytics**: Session statistics and reports
- **Data Export**: CSV/Excel export capabilities
- **Audit Trail**: Complete logging and tracking

### 🚨 Safety & Compliance
- **Auto Clock-Out**: Automatic session termination after timeout
- **Location Verification**: GPS accuracy threshold checking
- **Review Flagging**: Automatic flagging of suspicious sessions
- **Emergency Protocols**: Emergency session termination
- **Background Monitoring**: Celery-based background task processing

## 🛠 Technical Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL with spatial data support
- **Authentication**: JWT (JSON Web Tokens) with phone number login
- **Background Tasks**: Celery with Redis
- **Documentation**: Auto-generated API documentation
- **Security**: Production-ready security settings

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (for Celery)
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ClockIn_ClockOut_Employee
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\\Scripts\\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy `.env` file and update with your settings:
```bash
# Update the .env file with your database credentials
DB_NAME=clockin_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### 5. Database Setup
```bash
# Create PostgreSQL database
createdb clockin_db

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6. Create Sample Data (Optional)
```bash
python manage.py create_sample_data --users 5 --clients 10 --sessions 20
```

### 7. Run Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/logout/` - User logout
- `GET /api/v1/auth/profile/` - Get user profile
- `PATCH /api/v1/auth/profile/` - Update user profile
- `POST /api/v1/auth/password/change/` - Change password

### Session Management
- `POST /api/v1/sessions/clock-in/` - Clock in to start session
- `POST /api/v1/sessions/clock-out/` - Clock out to end session
- `GET /api/v1/sessions/active/` - Get current active session
- `GET /api/v1/sessions/my-sessions/` - Get user's sessions
- `GET /api/v1/sessions/all/` - Get all sessions (supervisors only)
- `POST /api/v1/sessions/location-update/` - Update location during session

### Client Management
- `GET /api/v1/clients/` - List clients
- `GET /api/v1/clients/{id}/` - Get client details
- `GET /api/v1/clients/search/` - Search clients
- `GET /api/v1/clients/nearby/` - Find nearby clients

### Example API Usage

#### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "phone_number": "+15551234567",
    "password": "your_password"
  }'
```

#### Clock In
```bash
curl -X POST http://localhost:8000/api/v1/sessions/clock-in/ \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your_jwt_token" \\
  -d '{
    "client": 1,
    "latitude": "39.7817",
    "longitude": "-89.6501",
    "accuracy": 15.5,
    "service_type": "counseling"
  }'
```

#### Clock Out
```bash
curl -X POST http://localhost:8000/api/v1/sessions/clock-out/ \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your_jwt_token" \\
  -d '{
    "latitude": "39.7818",
    "longitude": "-89.6502",
    "accuracy": 12.3,
    "session_notes": "Session completed successfully"
  }'
```

## 🔧 Configuration

### Key Settings

#### GPS Configuration
```python
GPS_ACCURACY_THRESHOLD = 100  # meters
SESSION_TIMEOUT_MINUTES = 480  # 8 hours
LOCATION_UPDATE_INTERVAL = 300  # 5 minutes
```

#### JWT Configuration
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=1440),
    'ROTATE_REFRESH_TOKENS': True,
}
```

## 🏗 Production Deployment

### 1. Environment Variables
Set the following in production:
```bash
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgres://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
```

### 2. Static Files
```bash
python manage.py collectstatic
```

### 3. Database Migration
```bash
python manage.py migrate
```

### 4. Start Celery (Background Tasks)
```bash
# Start Celery worker
celery -A clockin_project worker -l info

# Start Celery beat (scheduler)
celery -A clockin_project beat -l info
```

### 5. Web Server
Use Gunicorn with Nginx:
```bash
gunicorn clockin_project.wsgi:application --bind 0.0.0.0:8000
```

## 📊 Administrative Interface

Access the Django admin at `http://localhost:8000/admin/` to:

- Manage users and practitioners
- View and edit client information
- Monitor active sessions
- Review flagged sessions
- Generate reports
- Manage system settings

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Phone Number Verification**: Unique phone number identification
- **GPS Verification**: Location-based session verification
- **Session Timeout**: Automatic session termination
- **Audit Logging**: Complete activity logging
- **Role-Based Access**: Hierarchical permission system
- **CORS Configuration**: Secure cross-origin requests

## 📈 Monitoring & Maintenance

### Background Tasks
The system includes several Celery tasks:
- **Auto Clock-Out**: Runs every 5 minutes to timeout long sessions
- **Location Cleanup**: Hourly cleanup of old location data
- **Daily Reports**: Automated daily session reports
- **GPS Verification**: Background GPS verification processing

### Management Commands
```bash
# Auto clock out timed-out sessions
python manage.py auto_clockout_sessions

# Create sample data for testing
python manage.py create_sample_data

# Generate daily reports
python manage.py generate_daily_report 2024-01-15
```

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

## 📱 Mobile App Integration

This backend is designed to work with React Native mobile apps. Key integration points:

### Authentication Flow
1. User enters phone number and password
2. App receives JWT tokens
3. Store tokens securely on device
4. Include Bearer token in all API requests

### GPS Integration
1. Request location permissions
2. Get high-accuracy GPS coordinates
3. Send coordinates with clock in/out requests
4. Handle offline scenarios gracefully

### Real-time Updates
1. Periodic location updates during active sessions
2. Background sync for offline actions
3. Push notifications for session reminders

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, email support@yourcompany.com or create an issue in the repository.

## 🗂 Project Structure

```
ClockIn_ClockOut_Employee/
├── authentication/          # User management and authentication
│   ├── models.py           # Custom User model
│   ├── serializers.py      # API serializers
│   ├── views.py           # API views
│   ├── admin.py           # Django admin configuration
│   └── urls.py            # URL routing
├── clients/                # Client management
│   ├── models.py          # Client model
│   ├── serializers.py     # Client serializers
│   ├── views.py          # Client views
│   ├── admin.py          # Client admin
│   └── urls.py           # Client URLs
├── sessions/              # Session tracking
│   ├── models.py         # ClockSession model
│   ├── serializers.py    # Session serializers
│   ├── views.py         # Session views
│   ├── admin.py         # Session admin
│   ├── urls.py          # Session URLs
│   ├── tasks.py         # Celery background tasks
│   └── management/      # Django management commands
├── clockin_project/       # Main project settings
│   ├── settings.py       # Django settings
│   ├── urls.py          # Main URL configuration
│   ├── wsgi.py          # WSGI configuration
│   └── celery.py        # Celery configuration
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 🔮 Future Enhancements

- **Real-time Notifications**: Push notifications for session events
- **Advanced Analytics**: Detailed reporting and analytics dashboard
- **Geofencing**: Automatic clock-in when entering client locations
- **Offline Support**: Enhanced offline functionality
- **Integration APIs**: Third-party integrations (billing, scheduling)
- **Mobile SDKs**: Native mobile SDKs for easier integration
