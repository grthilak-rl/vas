#!/usr/bin/env python3
"""
Device Population Script for VAS
This script automatically populates the database with the standard devices
after the application starts, ensuring devices are always available.
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import logging

# Add the app directory to the path
sys.path.append('/app')

from app.config import settings
from app.models import Device, DeviceStatus
from app.database import Base, get_db
from app.services.validation import RTSPValidationService
from app.core.constants import STANDARD_DEVICES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard devices are now imported from constants.py

def wait_for_database(max_retries=30, delay=2):
    """Wait for the database to be ready."""
    engine = create_engine(settings.database_url)
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database is ready!")
            return True
        except OperationalError as e:
            logger.info(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(delay)
    
    logger.error("Database failed to become ready after maximum retries")
    return False

def wait_for_tables(max_retries=30, delay=2):
    """Wait for the application to create the necessary tables."""
    engine = create_engine(settings.database_url)
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                # Check if the devices table exists
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'devices'
                    );
                """))
                if result.scalar():
                    logger.info("Tables are ready!")
                    return True
                else:
                    logger.info(f"Tables not ready (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
        except Exception as e:
            logger.info(f"Error checking tables (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(delay)
    
    logger.error("Tables failed to become ready after maximum retries")
    return False

async def check_device_status(device_data):
    """Check the actual status of a device using the validation service."""
    validation_service = RTSPValidationService()
    
    device_info = {
        "ip_address": device_data["ip_address"],
        "rtsp_url": device_data["rtsp_url"]
    }
    
    try:
        logger.info(f"Checking status for device {device_data['name']} ({device_data['ip_address']})...")
        health_result = await validation_service.validate_device_health(device_info)
        status = health_result.get("status", "UNREACHABLE")
        error = health_result.get("error")
        
        if error:
            logger.info(f"Device {device_data['name']}: {status} - {error}")
        else:
            logger.info(f"Device {device_data['name']}: {status}")
        
        return DeviceStatus(status)
    except Exception as e:
        logger.error(f"Error checking status for device {device_data['name']}: {e}")
        return DeviceStatus.UNREACHABLE

async def populate_devices():
    """Populate the database with standard devices and check their actual status."""
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # Check if devices already exist
            existing_count = db.query(Device).count()
            if existing_count > 0:
                logger.info(f"Database already contains {existing_count} devices. Skipping population.")
                return
            
            logger.info("Populating database with standard devices...")
            
            for device_data in STANDARD_DEVICES:
                # Check if device with this IP already exists
                existing = db.query(Device).filter(Device.ip_address == device_data["ip_address"]).first()
                if existing:
                    logger.info(f"Device {device_data['name']} already exists. Skipping.")
                    continue
                
                # Check the actual device status
                device_status = await check_device_status(device_data)
                
                # Create new device with properly serialized JSON fields and actual status
                device = Device(
                    id=device_data["id"],
                    name=device_data["name"],
                    device_type=device_data["device_type"],
                    manufacturer=device_data["manufacturer"],
                    model=device_data["model"],
                    ip_address=device_data["ip_address"],
                    port=device_data["port"],
                    rtsp_url=device_data["rtsp_url"],
                    username=device_data["username"],
                    password=device_data["password"],
                    location=device_data["location"],
                    description=device_data["description"],
                    tags=json.dumps(device_data["tags"]),  # Serialize as JSON string
                    device_metadata=json.dumps(device_data["device_metadata"]),  # Serialize as JSON string
                    hostname=device_data["hostname"],
                    vendor=device_data["vendor"],
                    resolution=device_data["resolution"],
                    codec=device_data["codec"],
                    fps=device_data["fps"],
                    status=device_status,  # Use actual checked status
                    last_seen=datetime.utcnow(),
                    credentials_secure=False,
                    encrypted_credentials=None
                )
                
                db.add(device)
                logger.info(f"Added device: {device_data['name']} ({device_data['ip_address']}) - Status: {device_status}")
            
            db.commit()
            logger.info("Successfully populated database with standard devices!")
            
    except Exception as e:
        logger.error(f"Error populating devices: {e}")
        raise

def main():
    """Main function to populate devices."""
    logger.info("Starting device population script...")
    
    # Wait for database to be ready
    if not wait_for_database():
        logger.error("Database is not ready. Exiting.")
        sys.exit(1)
    
    # Wait for tables to be created
    if not wait_for_tables():
        logger.error("Tables are not ready. Exiting.")
        sys.exit(1)
    
    # Populate devices (async function)
    asyncio.run(populate_devices())
    
    logger.info("Device population completed successfully!")

if __name__ == "__main__":
    main() 