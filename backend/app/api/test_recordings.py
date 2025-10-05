"""
Test Recording API (No Authentication)
Simple test version to verify the recordings API is working
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Device, DeviceStatus
from app.services.live_dvr_service import live_dvr_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test-recordings", tags=["test-recordings"])


@router.get("/status/all")
async def test_get_all_recording_status(
    db: Session = Depends(get_db)
):
    """
    Test endpoint to get recording status for all devices (no auth required)
    """
    try:
        # Get all devices
        devices = db.query(Device).all()
        
        status_data = []
        for device in devices:
            is_recording = live_dvr_service.get_recording_status(str(device.id))
            storage_usage = live_dvr_service.get_storage_usage()
            device_storage = storage_usage.get(str(device.id), 0)
            
            status_data.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "device_status": device.status.value,
                "is_recording": is_recording,
                "storage_bytes": device_storage,
                "storage_mb": round(device_storage / (1024 * 1024), 2)
            })
        
        return {
            "message": "Test recordings API working!",
            "devices": status_data,
            "total_devices": len(devices),
            "recording_devices": sum(1 for d in status_data if d["is_recording"]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in test recordings API: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/storage/usage")
async def test_get_storage_usage(
    db: Session = Depends(get_db)
):
    """
    Test endpoint to get storage usage (no auth required)
    """
    try:
        storage_usage = live_dvr_service.get_storage_usage()
        
        # Convert bytes to MB and GB
        total_bytes = storage_usage.get('total', 0)
        total_mb = round(total_bytes / (1024 * 1024), 2)
        total_gb = round(total_bytes / (1024 * 1024 * 1024), 2)
        
        return {
            "message": "Storage usage test successful!",
            "total_storage": {
                "bytes": total_bytes,
                "mb": total_mb,
                "gb": total_gb
            },
            "recordings_directory": str(live_dvr_service.recordings_dir),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting storage usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
