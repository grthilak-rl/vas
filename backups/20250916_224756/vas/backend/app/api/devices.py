from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Device, DeviceStatus
from app.schemas import (
    DeviceResponse, DeviceUpdate, DeviceListResponse,
    ValidationRequest, ValidationResponse, DeviceCreate
)
from app.api.dependencies import get_current_user, get_current_admin_user
from app.services.validation import validation_service
from app.services.encryption import encryption_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[DeviceStatus] = Query(None),
    vendor_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of discovered devices with pagination and filtering."""
    query = db.query(Device)
    
    if status_filter:
        query = query.filter(Device.status == status_filter)
    
    if vendor_filter:
        query = query.filter(Device.vendor.ilike(f"%{vendor_filter}%"))
    
    total = query.count()
    devices = query.offset(skip).limit(limit).all()
    
    # Use the model's to_dict method for proper serialization
    device_responses = []
    for device in devices:
        device_dict = device.to_dict()
        device_responses.append(DeviceResponse(**device_dict))
    
    return DeviceListResponse(
        devices=device_responses,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.post("/", response_model=DeviceResponse)
async def create_device(
    device_create: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """Create a new device manually."""
    # Check if device with same IP already exists
    existing_device = db.query(Device).filter(
        Device.ip_address == device_create.ip_address
    ).first()
    
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device with this IP address already exists"
        )
    
    # Create new device
    import json
    new_device = Device(
        name=device_create.name,
        device_type=device_create.device_type,
        manufacturer=device_create.manufacturer,
        model=device_create.model,
        ip_address=device_create.ip_address,
        port=device_create.port,
        rtsp_url=device_create.rtsp_url,
        username=device_create.username,
        password=encryption_service.encrypt_text(device_create.password) if device_create.password else None,
        location=device_create.location,
        description=device_create.description,
        tags=json.dumps(device_create.tags) if device_create.tags else None,
        device_metadata=json.dumps(device_create.metadata) if device_create.metadata else None,
        status=DeviceStatus.ONLINE
    )
    
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    # Use the model's to_dict method for proper serialization
    device_dict = new_device.to_dict()
    return DeviceResponse(**device_dict)


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific device by ID."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Use the model's to_dict method for proper serialization
    device_dict = device.to_dict()
    return DeviceResponse(**device_dict)


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """Update device metadata."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Update only provided fields
    update_data = device_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    db.commit()
    db.refresh(device)
    
    # Use the model's to_dict method for proper serialization
    device_dict = device.to_dict()
    return DeviceResponse(**device_dict)


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """Delete a device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    db.delete(device)
    db.commit()
    return {"message": "Device deleted successfully"}


@router.post("/validate", response_model=ValidationResponse)
async def validate_device(
    validation_request: ValidationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Validate RTSP stream for a device."""
    result = await validation_service.validate_rtsp_stream(
        ip_address=validation_request.ip_address,
        username=validation_request.username,
        password=validation_request.password,
        rtsp_url=validation_request.rtsp_url
    )
    
    return ValidationResponse(
        ip_address=result["ip_address"],
        is_valid=result["is_valid"],
        rtsp_url=result.get("rtsp_url"),
        resolution=result.get("resolution"),
        codec=result.get("codec"),
        fps=result.get("fps"),
        error_message=result.get("error_message")
    )


@router.get("/{device_id}/status")
async def get_device_status(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current status of a device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Perform health check
    device_info = {
        "ip_address": device.ip_address,
        "rtsp_url": device.rtsp_url
    }
    
    health_result = await validation_service.validate_device_health(device_info)
    
    # Update device status in database
    device.status = health_result["status"]
    db.commit()
    
    return {
        "device_id": device_id,
        "status": health_result["status"],
        "error": health_result.get("error"),
        "last_checked": device.updated_at.isoformat()
    } 