# VAS Backend Service

FastAPI backend service for Video Aggregation Service (VAS) - Phase 1.

## 🎯 Overview

This backend service provides a robust foundation for discovering, cataloging, and managing RTSP-capable video devices across enterprise networks.

## 🏗 Architecture

- **API Layer**: FastAPI with automatic OpenAPI documentation
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Discovery**: Async network scanning with concurrent subnet processing
- **Validation**: RTSP stream validation using ffprobe
- **Security**: JWT authentication, role-based access control, encrypted credentials
- **Containerization**: Docker with docker-compose for easy deployment

## 🚀 Quick Start

### Running with Docker

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://vas_user:vas_password@localhost:5432/vas_db"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-secret-key-here"

# Run migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/login-json` - Login with JSON body

### Device Management
- `GET /api/devices` - List all discovered devices
- `POST /api/devices` - Create a new device
- `GET /api/devices/{id}` - Get device details
- `PATCH /api/devices/{id}` - Update device metadata
- `DELETE /api/devices/{id}` - Remove device
- `POST /api/devices/validate` - Validate RTSP stream URL
- `GET /api/devices/{id}/status` - Device status check

### Device Discovery
- `POST /api/discover` - Scan subnets for RTSP devices
- `GET /api/discover/{task_id}` - Get discovery task status
- `GET /api/discover` - List all discovery tasks

### Health Monitoring
- `GET /api/health` - Service health check
- `GET /` - Root endpoint with API information

## 🔧 Configuration

Environment variables can be set in `.env` file:

```env
# Database
DATABASE_URL=postgresql://vas_user:vas_password@localhost:5432/vas_db

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Discovery Settings
SCAN_TIMEOUT=5
MAX_CONCURRENT_SCANS=50
RTSP_PORTS=554,8554

# Validation Settings
FFPROBE_TIMEOUT=10
VALIDATION_RETRIES=3
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_discovery.py
```

## 📊 Database Schema

### Devices Table
- `id` (UUID) - Primary key
- `name` (String) - Device name
- `device_type` (String) - Type of device
- `manufacturer` (String) - Device manufacturer
- `model` (String) - Device model
- `ip_address` (String) - Device IP
- `port` (Integer) - RTSP port
- `rtsp_url` (String) - Validated RTSP stream
- `username` (String) - Device username
- `password` (Text) - Encrypted password
- `location` (String) - Device location
- `description` (Text) - Device description
- `tags` (Text) - JSON array of tags
- `device_metadata` (Text) - JSON object of metadata
- `hostname` (String) - DNS-resolved name
- `vendor` (String) - Device vendor
- `resolution` (String) - Video resolution
- `codec` (String) - Video codec
- `fps` (Integer) - Frames per second
- `last_seen` (Timestamp) - Last successful check
- `status` (Enum) - ONLINE/OFFLINE/UNREACHABLE
- `credentials_secure` (Boolean) - True if stored securely
- `encrypted_credentials` (Text) - Encrypted credentials
- `created_at` (Timestamp) - Creation timestamp
- `updated_at` (Timestamp) - Last update timestamp

## 🔒 Security Features

- JWT-based authentication
- Role-based access control (Admin, Viewer)
- Encrypted credential storage (AES-256)
- HTTPS support
- API rate limiting

## 📈 Performance

- Concurrent subnet scanning (500 IPs in <60 seconds)
- Redis caching for discovery results
- Async RTSP validation
- Database connection pooling

## 🐳 Docker Services

- **api**: FastAPI application
- **db**: PostgreSQL database
- **redis**: Redis cache
- **nginx**: Reverse proxy (optional)

## 📝 API Documentation

Once the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Development Tools

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Adding Sample Data
```bash
# Add sample devices
python add_sample_devices.py

# Add live cameras from .env
python add_live_cameras.py
```

### Testing API
```bash
# Test with authentication
python test_device_creation.py

# Comprehensive API test
python test_api.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details 