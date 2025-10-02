
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import SessionLocal
from app.models import Device
from app.schemas import DeviceCreate
from app.core.security import get_password_hash

async def add_devices(db: AsyncSession):
    """
    Adds the two Vivotek cameras to the database.
    """
    devices_to_add = [
        DeviceCreate(
            name="Vivotek Camera 1",
            device_type="IP Camera",
            manufacturer="Vivotek",
            model="FD9360-H",
            ip_address="172.16.16.122",
            port=554,
            rtsp_url="rtsp://root:G3M13m0b@172.16.16.122/live.sdp",
            username="root",
            password="G3M13m0b",
            location="Lab",
            description="Vivotek camera 1",
            tags=["dev", "test"],
            metadata={},
        ),
        DeviceCreate(
            name="Vivotek Camera 2",
            device_type="IP Camera",
            manufacturer="Vivotek",
            model="FD9360-H",
            ip_address="172.16.16.123",
            port=554,
            rtsp_url="rtsp://root:G3M13m0b@172.16.16.123/live.sdp",
            username="root",
            password="G3M13m0b",
            location="Lab",
            description="Vivotek camera 2",
            tags=["dev", "test"],
            metadata={},
        ),
    ]

    for device_data in devices_to_add:
        # Check if device already exists
        existing_device = await db.execute(
            Device.__table__.select().where(Device.ip_address == device_data.ip_address)
        )
        if existing_device.first():
            print(f"Device with IP {device_data.ip_address} already exists. Skipping.")
            continue

        # Create new device
        hashed_password = get_password_hash(device_data.password)
        new_device = Device(
            id=uuid.uuid4(),
            name=device_data.name,
            device_type=device_data.device_type,
            manufacturer=device_data.manufacturer,
            model=device_data.model,
            ip_address=device_data.ip_address,
            port=device_data.port,
            rtsp_url=device_data.rtsp_url,
            username=device_data.username,
            encrypted_credentials=hashed_password,
            location=device_data.location,
            description=device_data.description,
            tags=str(device_data.tags),
            device_metadata=str(device_data.metadata),
            credentials_secure=True,
        )
        db.add(new_device)
        print(f"Adding device: {device_data.name} ({device_data.ip_address})")

    await db.commit()
    print("Finished adding devices.")

async def main():
    """Main function to run the script."""
    print("Starting device creation script...")
    db = SessionLocal()
    try:
        await add_devices(db)
    finally:
        await db.close()
    print("Script finished.")

if __name__ == "__main__":
    asyncio.run(main()) 