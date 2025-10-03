import asyncio
import json
import re
import subprocess
from typing import Dict, Optional, Tuple
from app.config import settings


class RTSPValidationService:
    def __init__(self):
        self.timeout = settings.ffprobe_timeout
        self.retries = settings.validation_retries
        
    async def validate_rtsp_stream(
        self, 
        ip_address: str, 
        username: Optional[str] = None, 
        password: Optional[str] = None,
        rtsp_url: Optional[str] = None
    ) -> Dict:
        """
        Validate RTSP stream and extract metadata using ffprobe.
        
        Args:
            ip_address: Device IP address
            username: Optional username for authentication
            password: Optional password for authentication
            rtsp_url: Optional specific RTSP URL to test
            
        Returns:
            Dictionary with validation results and metadata
        """
        if rtsp_url:
            urls_to_test = [rtsp_url]
        else:
            urls_to_test = self._generate_common_rtsp_urls(ip_address)
        
        for attempt in range(self.retries):
            for url in urls_to_test:
                try:
                    # Add authentication if provided
                    if username and password:
                        url = self._add_authentication(url, username, password)
                    
                    result = await self._probe_rtsp_stream(url)
                    if result["is_valid"]:
                        return {
                            "ip_address": ip_address,
                            "is_valid": True,
                            "rtsp_url": url,
                            "resolution": result.get("resolution"),
                            "codec": result.get("codec"),
                            "fps": result.get("fps"),
                            "error_message": None
                        }
                        
                except Exception as e:
                    print(f"Validation attempt {attempt + 1} failed for {url}: {e}")
                    continue
        
        return {
            "ip_address": ip_address,
            "is_valid": False,
            "rtsp_url": None,
            "resolution": None,
            "codec": None,
            "fps": None,
            "error_message": "All validation attempts failed"
        }
    
    def _generate_common_rtsp_urls(self, ip_address: str) -> list:
        """Generate common RTSP URL patterns for testing."""
        return [
            f"rtsp://{ip_address}:554/stream1",
            f"rtsp://{ip_address}:554/live",
            f"rtsp://{ip_address}/live1s1.sdp",  # Added for IP cameras like the ones in this deployment
            f"rtsp://{ip_address}:554/live1s1.sdp",
            f"rtsp://{ip_address}:554/cam/realmonitor",
            f"rtsp://{ip_address}:554/axis-media/media.amp",
            f"rtsp://{ip_address}:554/onvif1",
            f"rtsp://{ip_address}:554/h264Preview_01_main",
            f"rtsp://{ip_address}:554/live/ch0",
            f"rtsp://{ip_address}:554/streaming/channels/101",
            f"rtsp://{ip_address}:554/11",
            f"rtsp://{ip_address}:554/1",
            # Alternative ports
            f"rtsp://{ip_address}:8554/stream1",
            f"rtsp://{ip_address}:8554/live",
            f"rtsp://{ip_address}:8554/cam/realmonitor",
        ]
    
    def _add_authentication(self, url: str, username: str, password: str) -> str:
        """Add authentication credentials to RTSP URL."""
        if "://" in url:
            protocol, rest = url.split("://", 1)
            return f"{protocol}://{username}:{password}@{rest}"
        return url
    
    async def _probe_rtsp_stream(self, url: str) -> Dict:
        """Use ffprobe to analyze RTSP stream."""
        try:
            # Build ffprobe command
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                "-timeout", str(self.timeout * 1000000),  # Convert to microseconds
                url
            ]
            
            # Run ffprobe command
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), 
                timeout=self.timeout + 5
            )
            
            if proc.returncode != 0:
                return {
                    "is_valid": False,
                    "error": stderr.decode() if stderr else "Unknown error"
                }
            
            # Parse JSON output
            probe_data = json.loads(stdout.decode())
            
            # Extract video stream information
            video_stream = None
            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            if not video_stream:
                return {
                    "is_valid": False,
                    "error": "No video stream found"
                }
            
            # Extract metadata
            resolution = f"{video_stream.get('width', 'unknown')}x{video_stream.get('height', 'unknown')}"
            codec = video_stream.get("codec_name", "unknown")
            
            # Calculate FPS
            fps = self._calculate_fps(video_stream)
            
            return {
                "is_valid": True,
                "resolution": resolution,
                "codec": codec,
                "fps": fps,
                "error": None
            }
            
        except asyncio.TimeoutError:
            return {
                "is_valid": False,
                "error": "Timeout during stream validation"
            }
        except json.JSONDecodeError:
            return {
                "is_valid": False,
                "error": "Invalid JSON response from ffprobe"
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e)
            }
    
    def _calculate_fps(self, video_stream: Dict) -> Optional[int]:
        """Calculate frames per second from video stream data."""
        try:
            # Try to get FPS from r_frame_rate
            r_frame_rate = video_stream.get("r_frame_rate")
            if r_frame_rate:
                if "/" in r_frame_rate:
                    num, den = map(int, r_frame_rate.split("/"))
                    if den > 0:
                        return round(num / den)
            
            # Try to get FPS from avg_frame_rate
            avg_frame_rate = video_stream.get("avg_frame_rate")
            if avg_frame_rate:
                if "/" in avg_frame_rate:
                    num, den = map(int, avg_frame_rate.split("/"))
                    if den > 0:
                        return round(num / den)
            
            return None
            
        except (ValueError, ZeroDivisionError):
            return None
    
    async def validate_device_health(self, device_info: Dict) -> Dict:
        """Validate device health by checking RTSP stream status."""
        ip_address = device_info.get("ip_address")
        rtsp_url = device_info.get("rtsp_url")
        
        if not ip_address:
            return {"status": "UNREACHABLE", "error": "No IP address provided"}
        
        # First check if device is reachable
        if not await self._is_device_reachable(ip_address):
            return {"status": "UNREACHABLE", "error": "Device not reachable"}
        
        # If we have an RTSP URL, validate it
        if rtsp_url:
            validation_result = await self.validate_rtsp_stream(ip_address, rtsp_url=rtsp_url)
            if validation_result["is_valid"]:
                return {"status": "ONLINE", "error": None}
            else:
                return {"status": "OFFLINE", "error": validation_result["error_message"]}
        
        # Try to find a valid RTSP stream
        validation_result = await self.validate_rtsp_stream(ip_address)
        if validation_result["is_valid"]:
            return {"status": "ONLINE", "error": None}
        else:
            return {"status": "OFFLINE", "error": "No valid RTSP stream found"}
    
    async def _is_device_reachable(self, ip_address: str) -> bool:
        """Check if device is reachable using ping."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "3", ip_address,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait_for(proc.wait(), timeout=5)
            return proc.returncode == 0
        except (asyncio.TimeoutError, Exception):
            return False


# Global instance
validation_service = RTSPValidationService() 