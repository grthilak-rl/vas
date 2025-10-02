from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql://vas_user:vas_password@localhost:5432/vas_db",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # Security
    secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # Discovery Settings
    scan_timeout: int = Field(default=5, env="SCAN_TIMEOUT")
    max_concurrent_scans: int = Field(default=50, env="MAX_CONCURRENT_SCANS")
    rtsp_ports: str = Field(default="554,8554", env="RTSP_PORTS")
    
    # Validation Settings
    ffprobe_timeout: int = Field(default=10, env="FFPROBE_TIMEOUT")
    validation_retries: int = Field(default=3, env="VALIDATION_RETRIES")
    
    # Janus WebRTC Settings
    janus_http_url: str = Field(
        default="http://localhost:8088/janus",
        env="JANUS_HTTP_URL"
    )
    janus_ws_url: str = Field(
        default="ws://janus:8188/",
        env="JANUS_WS_URL"
    )
    janus_admin_secret: str = Field(
        default="supersecretkey",
        env="JANUS_ADMIN_SECRET"
    )
    
    # API Settings
    api_v1_prefix: str = "/api"
    project_name: str = "Video Aggregation Service"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # CORS
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    @property
    def rtsp_port_list(self) -> List[int]:
        """Convert RTSP ports string to list of integers."""
        return [int(port.strip()) for port in self.rtsp_ports.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 