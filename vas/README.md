# Video Aggregation Service (VAS)

A comprehensive video aggregation and management platform for RTSP/IP cameras and video streams.

## Project Structure

```
vas/
├── backend/           # FastAPI backend service (Phase 1)
├── docs/             # Project documentation
├── scripts/          # Utility scripts
├── nginx/            # Nginx configuration
└── logs/             # Application logs
```

## Phase 1: Backend Foundation ✅

The backend service provides a robust foundation for video device management with the following features:

### Core Features
- **RTSP Device Discovery**: Automated network scanning for RTSP devices
- **Device Validation**: RTSP stream validation and metadata extraction
- **RESTful API**: Complete CRUD operations for device management
- **Authentication**: JWT-based authentication system
- **Database**: PostgreSQL with Alembic migrations
- **Caching**: Redis for performance optimization
- **Containerization**: Docker and Docker Compose setup

### Technology Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Authentication**: JWT
- **Containerization**: Docker & Docker Compose
- **Documentation**: OpenAPI/Swagger

### Quick Start

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

4. **Default credentials:**
   - Username: `admin`
   - Password: `admin123`

### API Endpoints

The backend provides comprehensive REST APIs for:
- **Authentication**: Login and token management
- **Devices**: CRUD operations, validation, status monitoring
- **Discovery**: Network scanning and device discovery
- **Health**: System health monitoring

For detailed API documentation, see [backend/api_usage_guide.md](backend/api_usage_guide.md).

## Future Phases

- **Phase 2**: Frontend Web Application
- **Phase 3**: Real-time Video Streaming
- **Phase 4**: Advanced Analytics and AI
- **Phase 5**: Mobile Applications

## Development

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (for local development)

### Local Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Testing
```bash
cd backend
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository. 