import asyncio
import ipaddress
import socket
import time
from typing import List, Dict, Set
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from app.config import settings


class NetworkDiscoveryService:
    def __init__(self):
        self.scan_timeout = settings.scan_timeout
        self.max_concurrent = settings.max_concurrent_scans
        self.rtsp_ports = settings.rtsp_port_list
        
    async def scan_subnets(self, subnets: List[str]) -> Dict[str, List[Dict]]:
        """
        Scan multiple subnets concurrently for RTSP-capable devices.
        
        Args:
            subnets: List of subnets in CIDR notation (e.g., ["10.50.0.0/16"])
            
        Returns:
            Dictionary with subnet as key and list of discovered devices as value
        """
        results = {}
        
        # Create tasks for each subnet
        tasks = []
        for subnet in subnets:
            task = asyncio.create_task(self._scan_subnet(subnet))
            tasks.append(task)
        
        # Execute all subnet scans concurrently
        subnet_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(subnet_results):
            if isinstance(result, Exception):
                results[subnets[i]] = []
            else:
                results[subnets[i]] = result
                
        return results
    
    async def _scan_subnet(self, subnet: str) -> List[Dict]:
        """Scan a single subnet for RTSP devices."""
        try:
            network = ipaddress.IPv4Network(subnet, strict=False)
            ip_addresses = [str(ip) for ip in network.hosts()]
            
            # Use semaphore to limit concurrent scans
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            # Create tasks for each IP
            tasks = []
            for ip in ip_addresses:
                task = asyncio.create_task(
                    self._scan_ip_with_semaphore(semaphore, ip)
                )
                tasks.append(task)
            
            # Execute all IP scans
            ip_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and None results
            devices = []
            for result in ip_results:
                if isinstance(result, dict) and result:
                    devices.append(result)
            
            return devices
            
        except Exception as e:
            print(f"Error scanning subnet {subnet}: {e}")
            return []
    
    async def _scan_ip_with_semaphore(self, semaphore: asyncio.Semaphore, ip: str) -> Dict:
        """Scan a single IP address with semaphore control."""
        async with semaphore:
            return await self._scan_single_ip(ip)
    
    async def _scan_single_ip(self, ip: str) -> Dict:
        """Scan a single IP address for RTSP services."""
        try:
            # Check if IP is reachable
            if not await self._is_ip_reachable(ip):
                return {}
            
            # Check for RTSP ports
            rtsp_ports = await self._check_rtsp_ports(ip)
            if not rtsp_ports:
                return {}
            
            # Get hostname
            hostname = await self._get_hostname(ip)
            
            # Basic device info
            device_info = {
                "ip_address": ip,
                "hostname": hostname,
                "rtsp_ports": rtsp_ports,
                "discovered_at": time.time()
            }
            
            # Try to identify vendor
            vendor_info = await self._identify_vendor(ip, rtsp_ports[0])
            device_info.update(vendor_info)
            
            return device_info
            
        except Exception as e:
            print(f"Error scanning IP {ip}: {e}")
            return {}
    
    async def _is_ip_reachable(self, ip: str) -> bool:
        """Check if IP address is reachable using ping."""
        try:
            # Use asyncio to run ping command
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", str(self.scan_timeout), ip,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait_for(proc.wait(), timeout=self.scan_timeout + 2)
            return proc.returncode == 0
        except (asyncio.TimeoutError, Exception):
            return False
    
    async def _check_rtsp_ports(self, ip: str) -> List[int]:
        """Check which RTSP ports are open on the IP."""
        open_ports = []
        
        for port in self.rtsp_ports:
            try:
                # Use asyncio to run netcat command
                proc = await asyncio.create_subprocess_exec(
                    "nc", "-z", "-w", str(self.scan_timeout), ip, str(port),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(proc.wait(), timeout=self.scan_timeout + 1)
                if proc.returncode == 0:
                    open_ports.append(port)
            except (asyncio.TimeoutError, Exception):
                continue
        
        return open_ports
    
    async def _get_hostname(self, ip: str) -> str:
        """Perform reverse DNS lookup for hostname."""
        try:
            loop = asyncio.get_event_loop()
            hostname = await loop.run_in_executor(
                None, socket.gethostbyaddr, ip
            )
            return hostname[0]
        except Exception:
            return ""
    
    async def _identify_vendor(self, ip: str, port: int) -> Dict:
        """Try to identify device vendor by checking common RTSP URLs."""
        common_urls = [
            f"rtsp://{ip}:{port}/stream1",
            f"rtsp://{ip}:{port}/live",
            f"rtsp://{ip}:{port}/cam/realmonitor",
            f"rtsp://{ip}:{port}/axis-media/media.amp",
            f"rtsp://{ip}:{port}/onvif1",
            f"rtsp://{ip}:{port}/h264Preview_01_main",
            f"rtsp://{ip}:{port}/live/ch0",
        ]
        
        vendor_patterns = {
            "Hikvision": ["/h264Preview_", "/live/ch"],
            "Dahua": ["/cam/realmonitor"],
            "Axis": ["/axis-media/"],
            "Generic": ["/stream", "/live", "/onvif"]
        }
        
        for url in common_urls:
            try:
                # Quick check if URL might be valid (without full validation)
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url.replace("rtsp://", "http://").replace("/stream1", "/"),
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as response:
                        if response.status < 500:  # Not a server error
                            # Try to identify vendor from URL pattern
                            for vendor, patterns in vendor_patterns.items():
                                if any(pattern in url for pattern in patterns):
                                    return {
                                        "vendor": vendor,
                                        "rtsp_url": url
                                    }
                            return {"vendor": "Unknown", "rtsp_url": url}
            except Exception:
                continue
        
        return {"vendor": "Unknown", "rtsp_url": None}


# Global instance
discovery_service = NetworkDiscoveryService() 