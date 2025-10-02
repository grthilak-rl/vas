"""
Snapshot API
Handles snapshot capture and retrieval endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models import Device, Snapshot, DeviceStatus
from app.schemas import (
    SnapshotResponse, 
    SnapshotListResponse, 
    SnapshotImageResponse,
    SnapshotCreate
)
from app.services.snapshot_service import snapshot_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.post("/capture/{device_id}", response_model=SnapshotResponse)
async def capture_snapshot(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Capture a snapshot from a device's RTSP stream"""
    try:
        # Get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Device not found"
            )
        
        # Check if device is online
        if device.status != DeviceStatus.ONLINE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device is not online. Current status: {device.status.value}"
            )
        
        # Capture snapshot
        snapshot = await snapshot_service.capture_snapshot(device, db)
        
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to capture snapshot. Check device connectivity and RTSP stream."
            )
        
        return SnapshotResponse.model_validate(snapshot)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error capturing snapshot for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while capturing snapshot"
        )


@router.get("/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get snapshot metadata by ID"""
    try:
        snapshot = db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Snapshot not found"
            )
        
        return SnapshotResponse.model_validate(snapshot)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting snapshot {snapshot_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving snapshot"
        )


@router.get("/{snapshot_id}/image", response_model=SnapshotImageResponse)
async def get_snapshot_image(
    snapshot_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get snapshot image data by ID"""
    try:
        snapshot = db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Snapshot not found"
            )
        
        # Get base64 encoded image data
        image_data = snapshot_service.get_snapshot_image(snapshot)
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve image data"
            )
        
        return SnapshotImageResponse(
            id=str(snapshot.id),
            device_id=str(snapshot.device_id),
            image_data=image_data,
            image_format=snapshot.image_format,
            width=snapshot.width,
            height=snapshot.height,
            file_size=snapshot.file_size,
            captured_at=snapshot.captured_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting snapshot image {snapshot_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving snapshot image"
        )


@router.get("/{snapshot_id}/binary", response_class=Response)
async def get_snapshot_image_binary(
    snapshot_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Retrieves the raw image data for a specific snapshot.
    Returns the image directly with the appropriate Content-Type header.
    """
    snapshot = db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")

    if not snapshot.image_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image data not found for this snapshot.")

    media_type = f"image/{snapshot.image_format}"
    return Response(content=snapshot.image_data, media_type=media_type)


@router.get("/", response_model=SnapshotListResponse)
async def get_snapshots(
    device_id: Optional[str] = Query(None, description="Optional device ID to filter by"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get snapshots, optionally filtered by device"""
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get snapshots
        snapshots, total_count = await snapshot_service.get_snapshots(
            device_id, db, per_page, offset
        )
        
        # Convert to response format
        snapshot_responses = [SnapshotResponse.model_validate(s) for s in snapshots]
        
        return SnapshotListResponse(
            snapshots=snapshot_responses,
            total=total_count,
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting snapshots for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving snapshots"
        )


@router.delete("/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete a snapshot"""
    try:
        success = await snapshot_service.delete_snapshot(snapshot_id, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Snapshot not found"
            )
        
        return {"message": "Snapshot deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting snapshot {snapshot_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting snapshot"
        )


@router.get("/", response_model=SnapshotListResponse)
async def list_all_snapshots(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all snapshots with optional device filtering"""
    try:
        # Build query
        query = db.query(Snapshot)
        
        if device_id:
            query = query.filter(Snapshot.device_id == device_id)
        
        # Get total count
        total_count = query.count()
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get snapshots with pagination
        snapshots = query.order_by(Snapshot.captured_at.desc())\
                         .offset(offset)\
                         .limit(per_page)\
                         .all()
        
        # Convert to response format
        snapshot_responses = [SnapshotResponse.from_orm(s) for s in snapshots]
        
        return SnapshotListResponse(
            snapshots=snapshot_responses,
            total=total_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving snapshots"
        )


@router.get("/device/{device_id}/latest", response_model=SnapshotResponse)
async def get_latest_snapshot(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get the latest snapshot for a specific device"""
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Get latest snapshot
        snapshot = db.query(Snapshot)\
                    .filter(Snapshot.device_id == device_id)\
                    .order_by(Snapshot.captured_at.desc())\
                    .first()
        
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No snapshots found for this device"
            )
        
        return SnapshotResponse.model_validate(snapshot)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest snapshot for device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving latest snapshot"
        )
