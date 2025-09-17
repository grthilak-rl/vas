import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class DeviceStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNREACHABLE = "UNREACHABLE"


class Device(Base):
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False)
    manufacturer = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False, unique=True, index=True)
    port = Column(Integer, default=554)
    rtsp_url = Column(String(500), nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(Text, nullable=True)  # Encrypted password
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON string of tags
    device_metadata = Column(Text, nullable=True)  # JSON string of metadata
    hostname = Column(String(255), nullable=True)
    vendor = Column(String(100), nullable=True)
    resolution = Column(String(50), nullable=True)
    codec = Column(String(50), nullable=True)
    fps = Column(Integer, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default=DeviceStatus.UNREACHABLE)
    credentials_secure = Column(Boolean, default=False)
    encrypted_credentials = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Device(id={self.id}, ip={self.ip_address}, status={self.status})>"
    
    def to_dict(self):
        """Convert device to dictionary for API responses."""
        import json
        return {
            "id": str(self.id),
            "name": self.name,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "ip_address": self.ip_address,
            "port": self.port,
            "rtsp_url": self.rtsp_url,
            "username": self.username,
            "location": self.location,
            "description": self.description,
            "tags": json.loads(self.tags) if self.tags else [],
            "metadata": json.loads(self.device_metadata) if self.device_metadata else {},
            "hostname": self.hostname,
            "vendor": self.vendor,
            "resolution": self.resolution,
            "codec": self.codec,
            "fps": self.fps,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "status": self.status,
            "credentials_secure": self.credentials_secure,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 