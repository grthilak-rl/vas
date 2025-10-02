"""
Snapshot Service
Handles capturing snapshots from RTSP camera streams
"""

import asyncio
import base64
import logging
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path
import uuid

from sqlalchemy.orm import Session
from app.models import Device, Snapshot, DeviceStatus
from app.core.constants import DEVICE_TO_MOUNTPOINT_MAP

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for capturing and managing camera snapshots"""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        if not self.ffmpeg_path:
            logger.warning("FFmpeg not found. Snapshot functionality will be limited.")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable path"""
        try:
            result = subprocess.run(['which', 'ffmpeg'], 
                                 capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # Try common paths
            common_paths = ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg']
            for path in common_paths:
                if Path(path).exists():
                    return path
            return None
    
    async def capture_snapshot(self, device: Device, db: Session) -> Optional[Snapshot]:
        """
        Capture a snapshot from the device's RTSP stream
        
        Args:
            device: Device to capture snapshot from
            db: Database session
            
        Returns:
            Snapshot object if successful, None otherwise
        """
        try:
            # Validate device is online
            if device.status != DeviceStatus.ONLINE:
                logger.warning(f"Device {device.id} is not online (status: {device.status})")
                return None
            
            # Check if device has RTSP URL
            if not device.rtsp_url:
                logger.error(f"Device {device.id} has no RTSP URL")
                return None
            
            # Capture image using FFmpeg
            image_data, width, height = await self._capture_image_from_rtsp(device)
            
            if not image_data:
                logger.error(f"Failed to capture image from device {device.id}")
                return None
            
            # Create snapshot record
            snapshot = Snapshot(
                id=uuid.uuid4(),
                device_id=device.id,
                image_data=image_data,
                image_format='jpeg',
                width=width,
                height=height,
                file_size=len(image_data),
                captured_at=datetime.utcnow()
            )
            
            # Save to database
            db.add(snapshot)
            db.commit()
            db.refresh(snapshot)
            
            logger.info(f"Successfully captured snapshot for device {device.id}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Error capturing snapshot for device {device.id}: {e}", exc_info=True)
            db.rollback()
            return None
    
    async def _capture_image_from_rtsp(self, device: Device) -> Tuple[Optional[bytes], Optional[int], Optional[int]]:
        """
        Capture image from RTSP stream using FFmpeg
        
        Args:
            device: Device with RTSP stream
            
        Returns:
            Tuple of (image_data, width, height) or (None, None, None) if failed
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg not available")
            return None, None, None
        
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Build FFmpeg command
            cmd = [
                self.ffmpeg_path,
                '-rtsp_transport', 'tcp',  # Use TCP for better reliability
                '-i', device.rtsp_url,
                '-vframes', '1',  # Capture only 1 frame
                '-q:v', '2',  # High quality
                '-f', 'image2',
                '-y',  # Overwrite output file
                temp_path
            ]
            
            # Add authentication if credentials are available
            if device.username and device.password:
                # For RTSP URLs with embedded credentials, FFmpeg should handle them
                # But we can also try to add them explicitly
                rtsp_url_with_auth = device.rtsp_url
                if '@' not in rtsp_url_with_auth:
                    # Add credentials to URL if not already present
                    rtsp_url_with_auth = device.rtsp_url.replace('rtsp://', f'rtsp://{device.username}:{device.password}@')
                cmd[3] = rtsp_url_with_auth
            
            logger.debug(f"Running FFmpeg command: {' '.join(cmd[:4])} [RTSP_URL] {' '.join(cmd[5:])}")
            
            # Run FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg failed with return code {process.returncode}")
                logger.error(f"FFmpeg stderr: {stderr.decode()}")
                return None, None, None
            
            # Read the captured image
            if not Path(temp_path).exists():
                logger.error("FFmpeg did not create output file")
                return None, None, None
            
            with open(temp_path, 'rb') as f:
                image_data = f.read()
            
            if not image_data:
                logger.error("Captured image is empty")
                return None, None, None
            
            # Try to get image dimensions using FFprobe
            width, height = await self._get_image_dimensions(temp_path)
            
            logger.info(f"Successfully captured image: {len(image_data)} bytes, {width}x{height}")
            return image_data, width, height
            
        except Exception as e:
            logger.error(f"Error capturing image from RTSP: {e}", exc_info=True)
            return None, None, None
        
        finally:
            # Clean up temporary file
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")
    
    async def _get_image_dimensions(self, image_path: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Get image dimensions using FFprobe
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (width, height) or (None, None) if failed
        """
        try:
            # Try to find FFprobe
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe') if self.ffmpeg_path else None
            if not ffprobe_path or not Path(ffprobe_path).exists():
                # Try common paths
                common_paths = ['/usr/bin/ffprobe', '/usr/local/bin/ffprobe', '/opt/homebrew/bin/ffprobe']
                for path in common_paths:
                    if Path(path).exists():
                        ffprobe_path = path
                        break
            
            if not ffprobe_path:
                logger.warning("FFprobe not found, cannot get image dimensions")
                return None, None
            
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                image_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.warning(f"FFprobe failed: {stderr.decode()}")
                return None, None
            
            import json
            data = json.loads(stdout.decode())
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width = stream.get('width')
                    height = stream.get('height')
                    return width, height
            
            return None, None
            
        except Exception as e:
            logger.warning(f"Error getting image dimensions: {e}")
            return None, None
    
    def get_snapshot_image(self, snapshot: Snapshot) -> Optional[str]:
        """
        Get base64 encoded image data from snapshot
        
        Args:
            snapshot: Snapshot object
            
        Returns:
            Base64 encoded image string or None if failed
        """
        try:
            if not snapshot.image_data:
                logger.error(f"Snapshot {snapshot.id} has no image data")
                return None
            
            # Encode image data as base64
            image_base64 = base64.b64encode(snapshot.image_data).decode('utf-8')
            return image_base64
            
        except Exception as e:
            logger.error(f"Error encoding snapshot image: {e}", exc_info=True)
            return None
    
    async def get_snapshots(self, device_id: Optional[str], db: Session, 
                           limit: int = 10, offset: int = 0) -> Tuple[list, int]:
        """
        Get snapshots, optionally filtered by device
        
        Args:
            device_id: Optional device UUID to filter by
            db: Database session
            limit: Maximum number of snapshots to return
            offset: Number of snapshots to skip
            
        Returns:
            Tuple of (snapshots_list, total_count)
        """
        try:
            # Build query
            query = db.query(Snapshot)
            if device_id:
                query = query.filter(Snapshot.device_id == device_id)
            
            # Get total count
            total_count = query.count()
            
            # Get snapshots with pagination
            snapshots = query.order_by(Snapshot.captured_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return snapshots, total_count
            
        except Exception as e:
            logger.error(f"Error getting snapshots: {e}", exc_info=True)
            return [], 0
    
    async def delete_snapshot(self, snapshot_id: str, db: Session) -> bool:
        """
        Delete a snapshot
        
        Args:
            snapshot_id: Snapshot UUID
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            snapshot = db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()
            if not snapshot:
                logger.warning(f"Snapshot {snapshot_id} not found")
                return False
            
            db.delete(snapshot)
            db.commit()
            
            logger.info(f"Successfully deleted snapshot {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting snapshot {snapshot_id}: {e}", exc_info=True)
            db.rollback()
            return False


# Global instance
snapshot_service = SnapshotService()
