"""
Janus WebRTC Gateway Service
Handles interaction with the Janus Admin API for stream management.
"""

import aiohttp  # Ensure aiohttp is imported for type checking
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.config import settings
from app.core.constants import DEVICE_TO_MOUNTPOINT_MAP

logger = logging.getLogger(__name__)

class JanusService:
    """Service for managing Janus WebRTC Gateway mountpoints via Core API (not Admin API)."""
    def __init__(self):
        self.core_ws_url = settings.janus_ws_url  # ws://janus:8188
        self.admin_ws_url = f"ws://{settings.janus_http_url.split('//')[1].split(':')[0]}:7188/admin"
        self.admin_secret = settings.janus_admin_secret
        self._session: Optional[aiohttp.ClientSession] = None  # Type hint for linter

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _core_api_flow(self, plugin_request_body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handles the Janus Core API session, plugin attach, and message flow."""
        session = await self._get_session()
        try:
            async with session.ws_connect(self.core_ws_url, headers={"Origin": "*"}) as ws:
                # 1. Create session
                create_txn = f"vas_{datetime.now().timestamp()}_create"
                await ws.send_json({"janus": "create", "transaction": create_txn})
                create_resp = await ws.receive_json()
                session_id = create_resp.get("data", {}).get("id")
                if not session_id:
                    logger.error(f"Failed to create Janus session: {create_resp}")
                    return None

                # 2. Attach to streaming plugin
                attach_txn = f"vas_{datetime.now().timestamp()}_attach"
                await ws.send_json({
                    "janus": "attach",
                    "plugin": "janus.plugin.streaming",
                    "transaction": attach_txn,
                    "session_id": session_id
                })
                attach_resp = await ws.receive_json()
                handle_id = attach_resp.get("data", {}).get("id")
                if not handle_id:
                    logger.error(f"Failed to attach to streaming plugin: {attach_resp}")
                    return None

                # 3. Send plugin message
                msg_txn = f"vas_{datetime.now().timestamp()}_msg"
                await ws.send_json({
                    "janus": "message",
                    "body": plugin_request_body,
                    "transaction": msg_txn,
                    "session_id": session_id,
                    "handle_id": handle_id
                })
                # 4. Wait for plugin data response
                while True:
                    msg = await ws.receive_json()
                    if msg.get("janus") == "event" and msg.get("plugindata", {}).get("plugin") == "janus.plugin.streaming":
                        return msg.get("plugindata", {}).get("data")
                    # Handle errors
                    if msg.get("janus") == "error":
                        logger.error(f"Janus plugin error: {msg}")
                        return None
        except Exception as e:
            logger.error(f"Error in Janus Core API flow: {e}", exc_info=True)
            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None
            return None

    async def list_mountpoints(self) -> List[Dict[str, Any]]:
        """List all mountpoints from Janus streaming plugin - using hardcoded list for now."""
        # For now, return the known mountpoints from Janus configuration
        # This is a temporary solution until we fix the HTTP API access issue
        return [
            {
                "id": 1,
                "type": "rtsp",
                "description": "Edge Camera 1 - Office",
                "enabled": True,
                "streaming": True,
                "metadata": "Unit-001 Camera 1 - Office/Entrance"
            },
            {
                "id": 2,
                "type": "rtsp", 
                "description": "Edge Camera 2 - Lobby",
                "enabled": True,
                "streaming": True,
                "metadata": "Unit-001 Camera 2 - Lobby/Reception"
            },
            {
                "id": 3,
                "type": "rtsp",
                "description": "Edge Camera 3 - Parking", 
                "enabled": True,
                "streaming": True,
                "metadata": "Unit-001 Camera 3 - Parking/Exterior"
            },
            {
                "id": 4,
                "type": "rtsp",
                "description": "Edge Camera 4 - Warehouse",
                "enabled": True,
                "streaming": True,
                "metadata": "Unit-001 Camera 4 - Warehouse/Storage"
            },
            {
                "id": 5,
                "type": "rtsp",
                "description": "Edge Camera 5 - Production",
                "enabled": True,
                "streaming": True,
                "metadata": "Unit-001 Camera 5 - Production/Workshop"
            },
            {
                "id": 6,
                "type": "rtsp",
                "description": "Edge Camera 6 - Security",
                "enabled": True,
                "streaming": True,
                "metadata": "Unit-001 Camera 6 - Security/Perimeter"
            }
        ]

    def get_webrtc_url(self) -> str:
        """Returns the public-facing WebRTC URL for client connections."""
        return self.core_ws_url

    def get_proxy_mountpoint_for_device_sync(self, device_id: str) -> Optional[int]:
        return DEVICE_TO_MOUNTPOINT_MAP.get(device_id)

    async def get_mountpoint_info(self, mountpoint_id: int) -> Optional[Dict[str, Any]]:
        mountpoints = await self.list_mountpoints()
        for mountpoint in mountpoints:
            if mountpoint.get("id") == mountpoint_id:
                return mountpoint
        return None

    async def health_check(self) -> bool:
        """Check if Janus is healthy by querying the HTTP info endpoint."""
        session = await self._get_session()
        try:
            async with session.get(f"{self.core_ws_url.replace('ws://', 'http://').replace(':8188/', ':8088/janus/info')}") as response:
                if response.status == 200:
                    result = await response.json()
                    is_healthy = result.get("janus") == "server_info"
                    if not is_healthy:
                        logger.warning(f"Janus health check failed. Response: {result}")
                    return is_healthy
                return False
        except Exception as e:
            logger.error(f"Janus health check exception: {e}", exc_info=True)
            return False

    async def is_proxy_mountpoint_active(self, mountpoint_id: int) -> bool:
        info = await self.get_mountpoint_info(mountpoint_id)
        return info is not None and info.get("streaming", False) is True

# Singleton instance
janus_service = JanusService() 