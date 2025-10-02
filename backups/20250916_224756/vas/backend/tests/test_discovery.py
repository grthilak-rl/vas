import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.services.discovery import NetworkDiscoveryService


@pytest.fixture
def discovery_service():
    return NetworkDiscoveryService()


@pytest.mark.asyncio
async def test_scan_subnets_empty_list(discovery_service):
    """Test scanning empty subnet list."""
    results = await discovery_service.scan_subnets([])
    assert results == {}


@pytest.mark.asyncio
async def test_scan_subnets_invalid_subnet(discovery_service):
    """Test scanning invalid subnet."""
    with patch('ipaddress.IPv4Network') as mock_network:
        mock_network.side_effect = ValueError("Invalid subnet")
        results = await discovery_service.scan_subnets(["invalid-subnet"])
        assert results["invalid-subnet"] == []


@pytest.mark.asyncio
async def test_scan_single_ip_reachable(discovery_service):
    """Test scanning a single reachable IP."""
    with patch.object(discovery_service, '_is_ip_reachable', return_value=True), \
         patch.object(discovery_service, '_check_rtsp_ports', return_value=[554]), \
         patch.object(discovery_service, '_get_hostname', return_value="test-device"), \
         patch.object(discovery_service, '_identify_vendor', return_value={"vendor": "Test", "rtsp_url": "rtsp://192.168.1.1:554/stream1"}):
        
        result = await discovery_service._scan_single_ip("192.168.1.1")
        
        assert result["ip_address"] == "192.168.1.1"
        assert result["hostname"] == "test-device"
        assert result["vendor"] == "Test"
        assert result["rtsp_url"] == "rtsp://192.168.1.1:554/stream1"


@pytest.mark.asyncio
async def test_scan_single_ip_unreachable(discovery_service):
    """Test scanning an unreachable IP."""
    with patch.object(discovery_service, '_is_ip_reachable', return_value=False):
        result = await discovery_service._scan_single_ip("192.168.1.999")
        assert result == {}


@pytest.mark.asyncio
async def test_check_rtsp_ports(discovery_service):
    """Test checking RTSP ports."""
    with patch('asyncio.create_subprocess_exec') as mock_subprocess:
        # Mock successful port check
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_subprocess.return_value = mock_proc
        
        result = await discovery_service._check_rtsp_ports("192.168.1.1")
        assert 554 in result


@pytest.mark.asyncio
async def test_get_hostname_success(discovery_service):
    """Test successful hostname resolution."""
    with patch('socket.gethostbyaddr', return_value=("test-device.local", [], ["192.168.1.1"])):
        result = await discovery_service._get_hostname("192.168.1.1")
        assert result == "test-device.local"


@pytest.mark.asyncio
async def test_get_hostname_failure(discovery_service):
    """Test failed hostname resolution."""
    with patch('socket.gethostbyaddr', side_effect=Exception("DNS resolution failed")):
        result = await discovery_service._get_hostname("192.168.1.1")
        assert result == ""


@pytest.mark.asyncio
async def test_identify_vendor(discovery_service):
    """Test vendor identification."""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await discovery_service._identify_vendor("192.168.1.1", 554)
        assert "vendor" in result
        assert "rtsp_url" in result 