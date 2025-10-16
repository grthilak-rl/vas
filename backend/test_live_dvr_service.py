#!/usr/bin/env python3
"""
Test script for LiveDVRService
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.live_dvr_service import live_dvr_service
from app.database import get_db
from app.models import Device, DeviceStatus

async def test_live_dvr_service():
    """Test the LiveDVRService functionality"""
    
    print("Testing LiveDVRService...")
    
    # Test 1: Check FFmpeg availability
    print(f"FFmpeg path: {live_dvr_service.ffmpeg_path}")
    
    if not live_dvr_service.ffmpeg_path:
        print("ERROR: FFmpeg not found. Please install FFmpeg.")
        return False
    
    # Test 2: Check recording directory
    print(f"Recordings directory: {live_dvr_service.recordings_dir}")
    print(f"Directory exists: {live_dvr_service.recordings_dir.exists()}")
    
    # Test 3: Get database session
    db = next(get_db())
    try:
        # Test 4: Get a test device
        device = db.query(Device).filter(Device.status == DeviceStatus.ONLINE).first()
        
        if not device:
            print("ERROR: No online devices found for testing")
            return False
        
        print(f"Found test device: {device.name} ({device.id})")
        print(f"RTSP URL: {device.rtsp_url}")
        
        # Test 5: Check recording status
        status = live_dvr_service.get_recording_status(str(device.id))
        print(f"Current recording status: {status}")
        
        # Test 6: Get storage usage
        storage = live_dvr_service.get_storage_usage()
        print(f"Storage usage: {storage}")
        
        # Test 7: Get recording segments
        segments = await live_dvr_service.get_recording_segments(str(device.id), db=db)
        print(f"Found {len(segments)} recording segments")
        
        print("LiveDVRService test completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_live_dvr_service())
    sys.exit(0 if success else 1)
