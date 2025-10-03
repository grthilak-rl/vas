import pytest
import json
from unittest.mock import patch, AsyncMock
from app.services.validation import RTSPValidationService


@pytest.fixture
def validation_service():
    return RTSPValidationService()


@pytest.mark.asyncio
async def test_validate_rtsp_stream_success(validation_service):
    """Test successful RTSP stream validation."""
    mock_ffprobe_output = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "25/1"
            }
        ]
    }
    
    with patch('asyncio.create_subprocess_exec') as mock_subprocess:
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (json.dumps(mock_ffprobe_output).encode(), b"")
        mock_subprocess.return_value = mock_proc
        
        result = await validation_service.validate_rtsp_stream("192.168.1.1")
        
        assert result["is_valid"] is True
        assert result["resolution"] == "1920x1080"
        assert result["codec"] == "h264"
        assert result["fps"] == 25


@pytest.mark.asyncio
async def test_validate_rtsp_stream_no_video(validation_service):
    """Test RTSP stream validation with no video stream."""
    mock_ffprobe_output = {
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "aac"
            }
        ]
    }
    
    with patch('asyncio.create_subprocess_exec') as mock_subprocess:
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (json.dumps(mock_ffprobe_output).encode(), b"")
        mock_subprocess.return_value = mock_proc
        
        result = await validation_service.validate_rtsp_stream("192.168.1.1")
        
        assert result["is_valid"] is False
        assert "No video stream found" in result["error_message"]


@pytest.mark.asyncio
async def test_validate_rtsp_stream_ffprobe_error(validation_service):
    """Test RTSP stream validation with ffprobe error."""
    with patch('asyncio.create_subprocess_exec') as mock_subprocess:
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"Connection failed")
        mock_subprocess.return_value = mock_proc
        
        result = await validation_service.validate_rtsp_stream("192.168.1.1")
        
        assert result["is_valid"] is False
        assert "Connection failed" in result["error_message"]


@pytest.mark.asyncio
async def test_validate_rtsp_stream_timeout(validation_service):
    """Test RTSP stream validation with timeout."""
    with patch('asyncio.create_subprocess_exec') as mock_subprocess:
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = TimeoutError("Operation timed out")
        mock_subprocess.return_value = mock_proc
        
        result = await validation_service.validate_rtsp_stream("192.168.1.1")
        
        assert result["is_valid"] is False
        assert "Timeout during stream validation" in result["error_message"]


def test_generate_common_rtsp_urls(validation_service):
    """Test generation of common RTSP URLs."""
    urls = validation_service._generate_common_rtsp_urls("192.168.1.1")
    
    assert len(urls) > 0
    assert any("192.168.1.1:554" in url for url in urls)
    assert any("192.168.1.1:8554" in url for url in urls)


def test_add_authentication(validation_service):
    """Test adding authentication to RTSP URL."""
    url = "rtsp://192.168.1.1:554/stream1"
    auth_url = validation_service._add_authentication(url, "admin", "password123")
    
    assert auth_url == "rtsp://admin:password123@192.168.1.1:554/stream1"


def test_calculate_fps_r_frame_rate(validation_service):
    """Test FPS calculation from r_frame_rate."""
    video_stream = {"r_frame_rate": "30/1"}
    fps = validation_service._calculate_fps(video_stream)
    assert fps == 30


def test_calculate_fps_avg_frame_rate(validation_service):
    """Test FPS calculation from avg_frame_rate."""
    video_stream = {"avg_frame_rate": "25/1"}
    fps = validation_service._calculate_fps(video_stream)
    assert fps == 25


def test_calculate_fps_invalid(validation_service):
    """Test FPS calculation with invalid data."""
    video_stream = {"r_frame_rate": "invalid"}
    fps = validation_service._calculate_fps(video_stream)
    assert fps is None


@pytest.mark.asyncio
async def test_validate_device_health_reachable(validation_service):
    """Test device health validation for reachable device."""
    device_info = {"ip_address": "192.168.1.1"}
    
    with patch.object(validation_service, '_is_device_reachable', return_value=True), \
         patch.object(validation_service, 'validate_rtsp_stream', return_value={"is_valid": True}):
        
        result = await validation_service.validate_device_health(device_info)
        assert result["status"] == "ONLINE"


@pytest.mark.asyncio
async def test_validate_device_health_unreachable(validation_service):
    """Test device health validation for unreachable device."""
    device_info = {"ip_address": "192.168.1.999"}
    
    with patch.object(validation_service, '_is_device_reachable', return_value=False):
        result = await validation_service.validate_device_health(device_info)
        assert result["status"] == "UNREACHABLE" 