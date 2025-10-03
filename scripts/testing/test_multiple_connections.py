#!/usr/bin/env python3
"""
VAS WebRTC API Gateway - Multiple Connection Test Script

This script tests the WebRTC API Gateway by:
1. Authenticating with the API
2. Discovering available streams
3. Creating multiple concurrent WebRTC connections
4. Monitoring connection status and performance

Usage:
    python3 test_multiple_connections.py
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionStats:
    stream_id: str
    start_time: float
    end_time: float = None
    status: str = "connecting"
    error: str = None
    duration: float = None
    
    def finish(self, status: str = "completed", error: str = None):
        self.end_time = time.time()
        self.status = status
        self.error = error
        self.duration = self.end_time - self.start_time

class WebRTCAPITester:
    def __init__(self, base_url: str = "http://10.30.250.245:8000"):
        self.base_url = base_url
        self.auth_token = None
        self.session = None
        self.available_streams = []
        self.connection_stats = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self, username: str = "admin", password: str = "admin123") -> bool:
        """Authenticate with the API and get access token"""
        try:
            logger.info(f"Authenticating with {self.base_url}")
            
            async with self.session.post(
                f"{self.base_url}/api/auth/login-json",
                json={"username": username, "password": password}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data["access_token"]
                    logger.info("✅ Authentication successful")
                    return True
                else:
                    logger.error(f"❌ Authentication failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    async def discover_streams(self) -> List[Dict[str, Any]]:
        """Discover available WebRTC streams"""
        try:
            logger.info("Discovering available streams...")
            
            async with self.session.get(
                f"{self.base_url}/api/streams/webrtc/streams",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_streams = data["streams"]
                    logger.info(f"✅ Found {len(self.available_streams)} streams")
                    
                    for stream in self.available_streams:
                        logger.info(f"  - Stream {stream['stream_id']}: {stream['name']} ({stream['status']})")
                    
                    return self.available_streams
                else:
                    logger.error(f"❌ Stream discovery failed: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Stream discovery error: {e}")
            return []
    
    async def get_stream_config(self, stream_id: str) -> Dict[str, Any]:
        """Get WebRTC configuration for a specific stream"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/streams/webrtc/streams/{stream_id}/config",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"❌ Failed to get config for stream {stream_id}: HTTP {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"❌ Error getting config for stream {stream_id}: {e}")
            return {}
    
    async def check_stream_status(self, stream_id: str) -> Dict[str, Any]:
        """Check status of a specific stream"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/streams/webrtc/streams/{stream_id}/status",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"❌ Failed to get status for stream {stream_id}: HTTP {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"❌ Error getting status for stream {stream_id}: {e}")
            return {}
    
    async def check_system_status(self) -> Dict[str, Any]:
        """Check overall system status"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/streams/webrtc/system/status",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"❌ Failed to get system status: HTTP {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"❌ Error getting system status: {e}")
            return {}
    
    async def simulate_connection(self, stream_id: str, duration: float = 10.0) -> ConnectionStats:
        """Simulate a WebRTC connection to a stream"""
        stats = ConnectionStats(stream_id=stream_id, start_time=time.time())
        self.connection_stats.append(stats)
        
        try:
            logger.info(f"🔗 Simulating connection to stream {stream_id}")
            
            # Get stream configuration
            config = await self.get_stream_config(stream_id)
            if not config:
                stats.finish("failed", "No configuration available")
                return stats
            
            # Get stream status
            status = await self.check_stream_status(stream_id)
            if not status or status.get("status") != "active":
                stats.finish("failed", "Stream not active")
                return stats
            
            logger.info(f"✅ Stream {stream_id} is active and ready")
            stats.status = "connected"
            
            # Simulate connection duration
            await asyncio.sleep(duration)
            
            stats.finish("completed")
            logger.info(f"✅ Connection to stream {stream_id} completed ({duration}s)")
            
        except Exception as e:
            stats.finish("failed", str(e))
            logger.error(f"❌ Connection to stream {stream_id} failed: {e}")
        
        return stats
    
    async def test_multiple_connections(self, num_connections: int = 3, duration: float = 10.0):
        """Test multiple concurrent connections to different streams"""
        logger.info(f"🧪 Testing {num_connections} concurrent connections for {duration} seconds each")
        
        # Get available streams
        if not self.available_streams:
            await self.discover_streams()
        
        if not self.available_streams:
            logger.error("❌ No streams available for testing")
            return
        
        # Select streams for testing (cycle through available streams)
        test_streams = []
        for i in range(num_connections):
            stream_id = self.available_streams[i % len(self.available_streams)]["stream_id"]
            test_streams.append(stream_id)
        
        logger.info(f"📡 Testing streams: {test_streams}")
        
        # Start all connections concurrently
        start_time = time.time()
        tasks = [
            self.simulate_connection(stream_id, duration)
            for stream_id in test_streams
        ]
        
        # Wait for all connections to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Analyze results
        self.analyze_results(results, end_time - start_time)
    
    def analyze_results(self, results: List[Any], total_time: float):
        """Analyze test results and generate report"""
        logger.info("\n" + "="*60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        successful = 0
        failed = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Connection {i+1}: Exception - {result}")
                failed += 1
            elif isinstance(result, ConnectionStats):
                if result.status == "completed":
                    logger.info(f"✅ Connection {i+1} (Stream {result.stream_id}): {result.duration:.2f}s")
                    successful += 1
                else:
                    logger.error(f"❌ Connection {i+1} (Stream {result.stream_id}): {result.error}")
                    failed += 1
        
        logger.info(f"\n📈 SUMMARY:")
        logger.info(f"  Total Connections: {len(results)}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Success Rate: {(successful/len(results)*100):.1f}%")
        logger.info(f"  Total Test Time: {total_time:.2f}s")
        
        if successful > 0:
            avg_duration = sum(r.duration for r in self.connection_stats if r.duration) / successful
            logger.info(f"  Average Connection Duration: {avg_duration:.2f}s")
    
    async def run_comprehensive_test(self):
        """Run a comprehensive test of the WebRTC API Gateway"""
        logger.info("🚀 Starting Comprehensive WebRTC API Gateway Test")
        logger.info("="*60)
        
        # Step 1: Authenticate
        if not await self.authenticate():
            logger.error("❌ Authentication failed. Cannot proceed.")
            return
        
        # Step 2: Discover streams
        streams = await self.discover_streams()
        if not streams:
            logger.error("❌ No streams discovered. Cannot proceed.")
            return
        
        # Step 3: Check system status
        logger.info("🔍 Checking system status...")
        system_status = await self.check_system_status()
        if system_status:
            logger.info(f"  System Status: {system_status.get('system_status', 'unknown')}")
            logger.info(f"  Total Streams: {system_status.get('total_streams', 0)}")
            logger.info(f"  Active Streams: {system_status.get('active_streams', 0)}")
            logger.info(f"  Janus Healthy: {system_status.get('janus_healthy', False)}")
        
        # Step 4: Test individual stream configurations
        logger.info("\n🔧 Testing individual stream configurations...")
        for stream in streams[:3]:  # Test first 3 streams
            stream_id = stream["stream_id"]
            config = await self.get_stream_config(stream_id)
            status = await self.check_stream_status(stream_id)
            
            logger.info(f"  Stream {stream_id} ({stream['name']}):")
            logger.info(f"    Config Available: {'✅' if config else '❌'}")
            logger.info(f"    Status: {status.get('status', 'unknown')}")
            logger.info(f"    WebRTC Ready: {status.get('webrtc_ready', False)}")
        
        # Step 5: Test multiple concurrent connections
        logger.info("\n🧪 Testing multiple concurrent connections...")
        await self.test_multiple_connections(num_connections=4, duration=5.0)
        
        logger.info("\n✅ Comprehensive test completed!")

async def main():
    """Main function to run the test"""
    async with WebRTCAPITester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
