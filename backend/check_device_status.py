#!/usr/bin/env python3
"""
Device Status Checker Script
This script checks the status of all devices in the database and updates them.
"""

import asyncio
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append('/app')

from app.config import settings
from app.models import Device, DeviceStatus
from app.services.validation import RTSPValidationService

async def check_all_devices():
    """Check status of all devices and update the database."""
    validation_service = RTSPValidationService()
    
    # Connect to database
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        # Get all devices
        devices = db.query(Device).all()
        
        if not devices:
            print("No devices found in database.")
            return
        
        print(f"Checking status for {len(devices)} devices...")
        print("-" * 60)
        
        for device in devices:
            device_info = {
                "ip_address": device.ip_address,
                "rtsp_url": device.rtsp_url
            }
            
            try:
                print(f"Checking {device.name} ({device.ip_address})...", end=" ")
                
                # Check device health
                health_result = await validation_service.validate_device_health(device_info)
                new_status = DeviceStatus(health_result.get("status", "UNREACHABLE"))
                error = health_result.get("error")
                
                # Update device status if changed
                if device.status != new_status:
                    old_status = device.status
                    device.status = new_status
                    device.last_seen = datetime.utcnow()
                    print(f"{old_status} → {new_status}")
                    if error:
                        print(f"  Error: {error}")
                else:
                    print(f"{new_status} (unchanged)")
                    if error:
                        print(f"  Error: {error}")
                
            except Exception as e:
                print(f"ERROR: {e}")
                device.status = DeviceStatus.UNREACHABLE
        
        # Commit all changes
        db.commit()
        print("-" * 60)
        print("Device status check completed!")
        
        # Print summary
        status_counts = {}
        for device in devices:
            status = device.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nStatus Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count} devices")

if __name__ == "__main__":
    print("🔍 Device Status Checker")
    print("=" * 60)
    asyncio.run(check_all_devices()) 