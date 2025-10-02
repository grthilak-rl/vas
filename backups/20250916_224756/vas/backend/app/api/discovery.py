import asyncio
import uuid
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Device, DeviceStatus
from app.schemas import DiscoveryRequest, DiscoveryResponse
from app.api.dependencies import get_current_admin_user
from app.services.discovery import discovery_service
from app.services.validation import validation_service

router = APIRouter(prefix="/discover", tags=["discovery"])

# In-memory storage for discovery tasks (in production, use Redis or database)
discovery_tasks = {}


@router.post("/", response_model=DiscoveryResponse)
async def start_discovery(
    discovery_request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_admin_user)
):
    """Start network discovery for specified subnets."""
    task_id = str(uuid.uuid4())
    
    # Calculate estimated duration (rough estimate: 1 second per 10 IPs)
    total_ips = 0
    for subnet in discovery_request.subnets:
        try:
            import ipaddress
            network = ipaddress.IPv4Network(subnet, strict=False)
            total_ips += network.num_addresses - 2  # Exclude network and broadcast
        except:
            total_ips += 256  # Default estimate
    
    estimated_duration = max(30, total_ips // 10)  # Minimum 30 seconds
    
    # Store task info
    discovery_tasks[task_id] = {
        "status": "running",
        "subnets": discovery_request.subnets,
        "progress": 0,
        "results": {},
        "error": None
    }
    
    # Start background discovery task
    background_tasks.add_task(
        run_discovery_task,
        task_id,
        discovery_request.subnets
    )
    
    return DiscoveryResponse(
        task_id=task_id,
        message="Discovery started",
        subnets=discovery_request.subnets,
        estimated_duration=estimated_duration
    )


@router.get("/{task_id}")
async def get_discovery_status(
    task_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Get status of a discovery task."""
    if task_id not in discovery_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery task not found"
        )
    
    task = discovery_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "subnets": task["subnets"],
        "results": task["results"] if task["status"] == "completed" else None,
        "error": task["error"]
    }


async def run_discovery_task(task_id: str, subnets: List[str]):
    """Background task to run network discovery."""
    try:
        # Run discovery
        results = await discovery_service.scan_subnets(subnets)
        
        # Update task status
        discovery_tasks[task_id]["status"] = "completed"
        discovery_tasks[task_id]["progress"] = 100
        discovery_tasks[task_id]["results"] = results
        
        # Store discovered devices in database
        await store_discovered_devices(results)
        
    except Exception as e:
        discovery_tasks[task_id]["status"] = "failed"
        discovery_tasks[task_id]["error"] = str(e)


async def store_discovered_devices(results: Dict[str, List[Dict]]):
    """Store discovered devices in the database."""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        for subnet, devices in results.items():
            for device_info in devices:
                # Check if device already exists
                existing_device = db.query(Device).filter(
                    Device.ip_address == device_info["ip_address"]
                ).first()
                
                if existing_device:
                    # Update existing device
                    existing_device.hostname = device_info.get("hostname", existing_device.hostname)
                    existing_device.vendor = device_info.get("vendor", existing_device.vendor)
                    existing_device.rtsp_url = device_info.get("rtsp_url", existing_device.rtsp_url)
                    existing_device.status = DeviceStatus.ONLINE
                else:
                    # Create new device with default values for required fields
                    device_name = device_info.get("hostname") or f"Camera-{device_info['ip_address']}"
                    device_type = "IP Camera"
                    manufacturer = device_info.get("vendor", "Unknown")
                    model = "Unknown"
                    rtsp_url = device_info.get("rtsp_url") or f"rtsp://{device_info['ip_address']}:554/stream1"
                    
                    new_device = Device(
                        name=device_name,
                        device_type=device_type,
                        manufacturer=manufacturer,
                        model=model,
                        ip_address=device_info["ip_address"],
                        port=device_info.get("rtsp_ports", [554])[0] if device_info.get("rtsp_ports") else 554,
                        rtsp_url=rtsp_url,
                        hostname=device_info.get("hostname"),
                        vendor=device_info.get("vendor"),
                        status=DeviceStatus.ONLINE
                    )
                    db.add(new_device)
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"Error storing discovered devices: {e}")
    finally:
        db.close()


@router.get("/")
async def list_discovery_tasks(
    current_user: dict = Depends(get_current_admin_user)
):
    """List all discovery tasks."""
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": task["status"],
                "subnets": task["subnets"],
                "progress": task["progress"]
            }
            for task_id, task in discovery_tasks.items()
        ]
    } 