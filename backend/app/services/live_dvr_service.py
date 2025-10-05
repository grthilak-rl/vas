"""
Live DVR Service
Handles continuous recording of RTSP camera streams for time-shifted playback
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid
import psutil
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from app.models import Device, DeviceStatus
from app.database import get_db

logger = logging.getLogger(__name__)


class LiveDVRService:
    """Service for continuous recording of camera streams"""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.recording_processes: Dict[str, subprocess.Popen] = {}
        self.recording_status: Dict[str, bool] = {}
        self.recording_config = {
            'segment_duration': 30,  # seconds
            'retention_hours': 48,   # hours
            'overlap_seconds': 3,    # seconds
            'quality': {
                'bitrate': '1M',
                'resolution': '1920x1080',
                'framerate': 30
            },
            'storage': {
                'max_disk_usage': 80,      # percentage
                'cleanup_threshold': 75,  # percentage
                'emergency_threshold': 90  # percentage
            }
        }
        self.recordings_dir = Path("/app/recordings")
        self.recordings_dir.mkdir(exist_ok=True)
        
        # Cleanup service state
        self._cleanup_running = False
        self._cleanup_thread = None
        self._cleanup_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        if not self.ffmpeg_path:
            logger.error("FFmpeg not found. Live DVR functionality will be unavailable.")
        
        # Start background cleanup service
        self._start_cleanup_service()
    
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
    
    def _get_device_recording_dir(self, device_id: str) -> Path:
        """Get recording directory for a specific device"""
        device_dir = self.recordings_dir / str(device_id)
        device_dir.mkdir(exist_ok=True)
        return device_dir
    
    def _generate_segment_filename(self, device_id: str, timestamp: datetime) -> str:
        """Generate filename for a recording segment"""
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")
        return f"{device_id}_{date_str}_{time_str}.mp4"
    
    async def start_recording(self, device: Device, db: Session) -> bool:
        """
        Start continuous recording for a device
        
        Args:
            device: Device to start recording for
            db: Database session
            
        Returns:
            bool: True if recording started successfully
        """
        try:
            device_id = str(device.id)
            
            # Check if already recording
            if self.recording_status.get(device_id, False):
                logger.warning(f"Recording already active for device {device_id}")
                return True
            
            # Validate device is online
            if device.status != DeviceStatus.ONLINE:
                logger.error(f"Device {device_id} is not online (status: {device.status})")
                return False
            
            # Check if device has RTSP URL
            if not device.rtsp_url:
                logger.error(f"Device {device_id} has no RTSP URL")
                return False
            
            if not self.ffmpeg_path:
                logger.error("FFmpeg not available")
                return False
            
            # Create device recording directory
            device_dir = self._get_device_recording_dir(device_id)
            
            # Build FFmpeg command for continuous recording
            output_pattern = str(device_dir / f"{device_id}_%Y%m%d_%H%M%S.mp4")
            
            cmd = [
                self.ffmpeg_path,
                '-rtsp_transport', 'tcp',
                '-i', device.rtsp_url,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-b:v', self.recording_config['quality']['bitrate'],
                '-s', self.recording_config['quality']['resolution'],
                '-r', str(self.recording_config['quality']['framerate']),
                '-f', 'segment',
                '-segment_time', str(self.recording_config['segment_duration']),
                '-segment_format', 'mp4',
                '-reset_timestamps', '1',
                '-avoid_negative_ts', 'make_zero',
                '-y',  # Overwrite output files
                output_pattern
            ]
            
            logger.info(f"Starting recording for device {device_id} with command: {' '.join(cmd).replace(device.password, '********')}")
            
            # Start FFmpeg process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process reference
            self.recording_processes[device_id] = process
            self.recording_status[device_id] = True
            
            # Update database status
            await self._update_recording_status(device_id, True, db)
            
            logger.info(f"Recording started successfully for device {device_id} (PID: {process.pid})")
            
            # Start background task to monitor the process
            asyncio.create_task(self._monitor_recording_process(device_id, process))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording for device {device_id}: {e}", exc_info=True)
            return False
    
    async def stop_recording(self, device_id: str, db: Session) -> bool:
        """
        Stop continuous recording for a device
        
        Args:
            device_id: Device ID to stop recording for
            db: Database session
            
        Returns:
            bool: True if recording stopped successfully
        """
        try:
            device_id = str(device_id)
            
            if not self.recording_status.get(device_id, False):
                logger.warning(f"No active recording for device {device_id}")
                return True
            
            # Get the process
            process = self.recording_processes.get(device_id)
            if not process:
                logger.warning(f"No process found for device {device_id}")
                self.recording_status[device_id] = False
                return True
            
            # Terminate the process gracefully
            process.terminate()
            
            # Wait for process to terminate
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process for device {device_id} did not terminate gracefully, forcing kill")
                process.kill()
                process.wait()
            
            # Clean up
            del self.recording_processes[device_id]
            self.recording_status[device_id] = False
            
            # Update database status
            await self._update_recording_status(device_id, False, db)
            
            logger.info(f"Recording stopped successfully for device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording for device {device_id}: {e}", exc_info=True)
            return False
    
    async def _monitor_recording_process(self, device_id: str, process: subprocess.Popen):
        """Monitor a recording process and restart if needed"""
        try:
            while process.poll() is None:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                # Check if process is still running
                if process.poll() is not None:
                    logger.warning(f"Recording process for device {device_id} died unexpectedly")
                    break
            
            # Process died, clean up
            if device_id in self.recording_processes:
                del self.recording_processes[device_id]
            self.recording_status[device_id] = False
            
            # Update database status
            db = next(get_db())
            try:
                await self._update_recording_status(device_id, False, db)
            finally:
                db.close()
            
            logger.info(f"Recording process monitoring ended for device {device_id}")
            
        except Exception as e:
            logger.error(f"Error monitoring recording process for device {device_id}: {e}", exc_info=True)
    
    async def _update_recording_status(self, device_id: str, is_recording: bool, db: Session):
        """Update recording status in database"""
        try:
            from sqlalchemy import text
            
            if is_recording:
                # Insert or update recording status
                db.execute(text("""
                    INSERT INTO recording_status (device_id, is_recording, updated_at)
                    VALUES (:device_id, :is_recording, CURRENT_TIMESTAMP)
                    ON CONFLICT (device_id) 
                    DO UPDATE SET 
                        is_recording = :is_recording,
                        updated_at = CURRENT_TIMESTAMP
                """), {
                    'device_id': device_id,
                    'is_recording': is_recording
                })
            else:
                # Update recording status to false
                db.execute(text("""
                    UPDATE recording_status 
                    SET is_recording = :is_recording, updated_at = CURRENT_TIMESTAMP
                    WHERE device_id = :device_id
                """), {
                    'device_id': device_id,
                    'is_recording': is_recording
                })
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update recording status for device {device_id}: {e}", exc_info=True)
            db.rollback()
    
    async def get_recording_segments(self, device_id: str, start_time: Optional[datetime] = None, 
                                  end_time: Optional[datetime] = None, db: Session = None) -> List[Dict]:
        """
        Get recording segments for a device within a time range
        
        Args:
            device_id: Device ID
            start_time: Start time filter (optional)
            end_time: End time filter (optional)
            db: Database session
            
        Returns:
            List of segment dictionaries
        """
        try:
            if not db:
                db = next(get_db())
            
            from sqlalchemy import text
            
            query = """
                SELECT id, device_id, segment_file_path, start_timestamp, 
                       end_timestamp, duration_seconds, file_size_bytes, created_at
                FROM recording_segments 
                WHERE device_id = :device_id
            """
            params = {'device_id': device_id}
            
            if start_time:
                query += " AND start_timestamp >= :start_time"
                params['start_time'] = start_time
            
            if end_time:
                query += " AND end_timestamp <= :end_time"
                params['end_time'] = end_time
            
            query += " ORDER BY start_timestamp DESC"
            
            result = db.execute(text(query), params)
            segments = []
            
            for row in result:
                segments.append({
                    'id': str(row.id),
                    'device_id': str(row.device_id),
                    'segment_file_path': row.segment_file_path,
                    'start_timestamp': row.start_timestamp.isoformat(),
                    'end_timestamp': row.end_timestamp.isoformat(),
                    'duration_seconds': row.duration_seconds,
                    'file_size_bytes': row.file_size_bytes,
                    'created_at': row.created_at.isoformat()
                })
            
            return segments
            
        except Exception as e:
            logger.error(f"Failed to get recording segments for device {device_id}: {e}", exc_info=True)
            return []
    
    async def cleanup_expired_segments(self, db: Session) -> int:
        """
        Clean up expired recording segments
        
        Args:
            db: Database session
            
        Returns:
            Number of segments cleaned up
        """
        try:
            from sqlalchemy import text
            
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=self.recording_config['retention_hours'])
            
            # Get expired segments with file size for better logging
            result = db.execute(text("""
                SELECT id, segment_file_path, file_size_bytes, start_timestamp
                FROM recording_segments 
                WHERE start_timestamp < :cutoff_time
                ORDER BY start_timestamp ASC
            """), {'cutoff_time': cutoff_time})
            
            expired_segments = result.fetchall()
            cleaned_count = 0
            total_size_freed = 0
            
            logger.info(f"Found {len(expired_segments)} expired segments to clean up")
            
            for segment in expired_segments:
                try:
                    # Delete file if it exists
                    file_path = Path(segment.segment_file_path)
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        total_size_freed += file_size
                        logger.debug(f"Deleted expired segment file: {file_path} ({file_size} bytes)")
                    else:
                        logger.warning(f"Segment file not found: {file_path}")
                    
                    # Delete database record
                    db.execute(text("DELETE FROM recording_segments WHERE id = :id"), 
                             {'id': segment.id})
                    
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to clean up segment {segment.id}: {e}")
            
            db.commit()
            
            # Log cleanup results
            size_freed_mb = total_size_freed / (1024 * 1024)
            logger.info(f"Cleaned up {cleaned_count} expired recording segments, freed {size_freed_mb:.2f} MB")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired segments: {e}", exc_info=True)
            db.rollback()
            return 0
    
    def get_recording_status(self, device_id: str) -> bool:
        """Get current recording status for a device"""
        return self.recording_status.get(str(device_id), False)
    
    def get_all_recording_status(self) -> Dict[str, bool]:
        """Get recording status for all devices"""
        return self.recording_status.copy()
    
    def get_storage_usage(self) -> Dict[str, int]:
        """Get storage usage for recordings"""
        try:
            total_size = 0
            device_sizes = {}
            
            for device_dir in self.recordings_dir.iterdir():
                if device_dir.is_dir():
                    device_size = sum(f.stat().st_size for f in device_dir.rglob('*') if f.is_file())
                    device_sizes[device_dir.name] = device_size
                    total_size += device_size
            
            device_sizes['total'] = total_size
            return device_sizes
            
        except Exception as e:
            logger.error(f"Failed to get storage usage: {e}", exc_info=True)
            return {'total': 0}

    def _start_cleanup_service(self):
        """Start the background cleanup service"""
        if self._cleanup_running:
            return
        
        self._cleanup_running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info("Background cleanup service started")
    
    def _stop_cleanup_service(self):
        """Stop the background cleanup service"""
        self._cleanup_running = False
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        logger.info("Background cleanup service stopped")
    
    def _cleanup_worker(self):
        """Background worker for automatic cleanup"""
        while self._cleanup_running:
            try:
                # Run cleanup every 30 minutes
                time.sleep(30 * 60)
                
                if not self._cleanup_running:
                    break
                
                # Check if cleanup is needed
                if self._should_run_cleanup():
                    logger.info("Running scheduled cleanup")
                    self._run_cleanup_cycle()
                
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _should_run_cleanup(self) -> bool:
        """Check if cleanup should be run based on storage usage"""
        try:
            storage_usage = self.get_storage_usage()
            total_bytes = storage_usage.get('total', 0)
            
            # Get disk usage percentage
            disk_usage = psutil.disk_usage(str(self.recordings_dir))
            usage_percentage = (disk_usage.used / disk_usage.total) * 100
            
            # Run cleanup if we're above the cleanup threshold
            return usage_percentage > self.recording_config['storage']['cleanup_threshold']
            
        except Exception as e:
            logger.error(f"Failed to check storage usage: {e}")
            return True  # Run cleanup as fallback
    
    def _run_cleanup_cycle(self):
        """Run a complete cleanup cycle"""
        with self._cleanup_lock:
            try:
                # Get database session
                db = next(get_db())
                
                # Run cleanup
                cleaned_count = asyncio.run(self.cleanup_expired_segments(db))
                
                # Check if we need emergency cleanup
                if self._is_emergency_storage():
                    logger.warning("Emergency storage cleanup triggered")
                    emergency_count = asyncio.run(self._emergency_cleanup(db))
                    logger.info(f"Emergency cleanup removed {emergency_count} segments")
                
                # Update recording status tables
                self._update_recording_status_tables(db)
                
                db.close()
                
                logger.info(f"Cleanup cycle completed: {cleaned_count} segments cleaned")
                
            except Exception as e:
                logger.error(f"Failed to run cleanup cycle: {e}", exc_info=True)
    
    def _is_emergency_storage(self) -> bool:
        """Check if we're in emergency storage situation"""
        try:
            disk_usage = psutil.disk_usage(str(self.recordings_dir))
            usage_percentage = (disk_usage.used / disk_usage.total) * 100
            return usage_percentage > self.recording_config['storage']['emergency_threshold']
        except Exception as e:
            logger.error(f"Failed to check emergency storage: {e}")
            return False
    
    async def _emergency_cleanup(self, db: Session) -> int:
        """Emergency cleanup - more aggressive segment removal"""
        try:
            from sqlalchemy import text
            
            # Calculate more aggressive cutoff time (reduce retention by 50%)
            emergency_hours = self.recording_config['retention_hours'] // 2
            cutoff_time = datetime.utcnow() - timedelta(hours=emergency_hours)
            
            # Get segments for emergency cleanup
            result = db.execute(text("""
                SELECT id, segment_file_path, file_size_bytes
                FROM recording_segments 
                WHERE start_timestamp < :cutoff_time
                ORDER BY start_timestamp ASC
                LIMIT 100
            """), {'cutoff_time': cutoff_time})
            
            emergency_segments = result.fetchall()
            cleaned_count = 0
            
            for segment in emergency_segments:
                try:
                    # Delete file if it exists
                    file_path = Path(segment.segment_file_path)
                    if file_path.exists():
                        file_path.unlink()
                        logger.debug(f"Emergency cleanup: Deleted segment file: {file_path}")
                    
                    # Delete database record
                    db.execute(text("DELETE FROM recording_segments WHERE id = :id"), 
                             {'id': segment.id})
                    
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to emergency clean segment {segment.id}: {e}")
            
            db.commit()
            logger.warning(f"Emergency cleanup completed: {cleaned_count} segments removed")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed emergency cleanup: {e}", exc_info=True)
            db.rollback()
            return 0
    
    def _update_recording_status_tables(self, db: Session):
        """Update recording status tables with current statistics"""
        try:
            from sqlalchemy import text
            
            # Update recording_status table for each device
            result = db.execute(text("""
                SELECT device_id, COUNT(*) as segment_count, SUM(file_size_bytes) as total_size
                FROM recording_segments 
                GROUP BY device_id
            """))
            
            device_stats = result.fetchall()
            
            for stat in device_stats:
                db.execute(text("""
                    INSERT INTO recording_status (device_id, total_segments, total_size_bytes, updated_at)
                    VALUES (:device_id, :segment_count, :total_size, :updated_at)
                    ON CONFLICT (device_id) 
                    DO UPDATE SET 
                        total_segments = :segment_count,
                        total_size_bytes = :total_size,
                        updated_at = :updated_at
                """), {
                    'device_id': stat.device_id,
                    'segment_count': stat.segment_count,
                    'total_size': stat.total_size or 0,
                    'updated_at': datetime.utcnow()
                })
            
            db.commit()
            logger.debug("Updated recording status tables")
            
        except Exception as e:
            logger.error(f"Failed to update recording status tables: {e}", exc_info=True)
            db.rollback()
    
    def get_cleanup_status(self) -> Dict[str, any]:
        """Get cleanup service status"""
        try:
            disk_usage = psutil.disk_usage(str(self.recordings_dir))
            usage_percentage = (disk_usage.used / disk_usage.total) * 100
            
            return {
                'cleanup_running': self._cleanup_running,
                'disk_usage_percentage': round(usage_percentage, 2),
                'disk_free_gb': round(disk_usage.free / (1024**3), 2),
                'disk_total_gb': round(disk_usage.total / (1024**3), 2),
                'cleanup_threshold': self.recording_config['storage']['cleanup_threshold'],
                'emergency_threshold': self.recording_config['storage']['emergency_threshold'],
                'retention_hours': self.recording_config['retention_hours'],
                'is_emergency_mode': self._is_emergency_storage()
            }
        except Exception as e:
            logger.error(f"Failed to get cleanup status: {e}")
            return {
                'cleanup_running': False,
                'error': str(e)
            }
    
    def force_cleanup(self) -> Dict[str, any]:
        """Manually trigger cleanup"""
        try:
            logger.info("Manual cleanup triggered")
            self._run_cleanup_cycle()
            
            return {
                'success': True,
                'message': 'Cleanup completed successfully',
                'status': self.get_cleanup_status()
            }
        except Exception as e:
            logger.error(f"Manual cleanup failed: {e}")
            return {
                'success': False,
                'message': f'Cleanup failed: {str(e)}',
                'error': str(e)
            }
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        self._stop_cleanup_service()
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


# Global instance
live_dvr_service = LiveDVRService()
