from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, IPvAnyAddress, validator, field_validator
from app.models import DeviceStatus
import json


class DeviceBase(BaseModel):
    ip_address: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    rtsp_url: Optional[str] = None
    resolution: Optional[str] = None
    codec: Optional[str] = None
    fps: Optional[int] = None
    status: Optional[DeviceStatus] = DeviceStatus.UNREACHABLE
    credentials_secure: Optional[bool] = False


class DeviceCreate(BaseModel):
    name: str
    device_type: str
    manufacturer: str
    model: str
    ip_address: str
    port: int = 554
    rtsp_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    rtsp_url: Optional[str] = None
    resolution: Optional[str] = None
    codec: Optional[str] = None
    fps: Optional[int] = None
    status: Optional[DeviceStatus] = None
    credentials_secure: Optional[bool] = None


class DeviceResponse(BaseModel):
    id: str
    name: str
    device_type: str
    manufacturer: str
    model: str
    ip_address: str
    port: int
    rtsp_url: str
    username: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    resolution: Optional[str] = None
    codec: Optional[str] = None
    fps: Optional[int] = None
    last_seen: Optional[datetime] = None
    status: Optional[DeviceStatus] = DeviceStatus.UNREACHABLE
    credentials_secure: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm method to handle UUID and JSON serialization."""
        if hasattr(obj, 'to_dict'):
            # Use the model's to_dict method which handles serialization properly
            data = obj.to_dict()
            return cls(**data)
        else:
            # Fallback to default behavior
            return super().from_orm(obj)
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_id(cls, v):
        """Convert UUID to string if needed."""
        if hasattr(v, '__str__'):
            return str(v)
        return v
    
    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags(cls, v):
        """Deserialize tags from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []
    
    @field_validator('metadata', mode='before')
    @classmethod
    def validate_metadata(cls, v):
        """Deserialize metadata from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {}
        return v or {}


class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total: int
    page: int
    per_page: int


class DiscoveryRequest(BaseModel):
    subnets: List[str]
    
    @validator('subnets')
    def validate_subnets(cls, v):
        if not v:
            raise ValueError('At least one subnet must be provided')
        return v


class DiscoveryResponse(BaseModel):
    task_id: str
    message: str
    subnets: List[str]
    estimated_duration: int  # seconds


class ValidationRequest(BaseModel):
    ip_address: str
    username: Optional[str] = None
    password: Optional[str] = None
    rtsp_url: Optional[str] = None


class ValidationResponse(BaseModel):
    ip_address: str
    is_valid: bool
    rtsp_url: Optional[str] = None
    resolution: Optional[str] = None
    codec: Optional[str] = None
    fps: Optional[int] = None
    error_message: Optional[str] = None


class CredentialsRequest(BaseModel):
    username: str
    password: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: str
    redis: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime


# Janus Schemas
class JanusMountpoint(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    streaming: bool = False
    enabled: bool = True
    media: List[Dict[str, Any]] = []
    viewers: int = 0


# Stream Management Schemas
class StreamStatus(str, Enum):
    """Stream status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"


class StreamCreate(BaseModel):
    """Schema for creating a new stream"""
    device_id: str
    description: Optional[str] = None
    audio: bool = False
    video: bool = True


class StreamResponse(BaseModel):
    """Schema for stream response"""
    id: str
    name: str
    description: Optional[str] = None
    device_type: str
    ip_address: str
    rtsp_url: str
    status: StreamStatus
    mountpoint_info: Optional[JanusMountpoint] = None
    webrtc_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_id(cls, v):
        """Convert UUID to string if needed."""
        if hasattr(v, '__str__'):
            return str(v)
        return v 