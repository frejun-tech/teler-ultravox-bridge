import os

from pydantic_settings import BaseSettings 
from app.utils.ngrok_utils import get_server_domain

class Setting(BaseSettings):
    """Application settings"""
    
    # Ultravox configuration
    ULTRAVOX_API_KEY: str = os.getenv("ULTRAVOX_API_KEY", "")
    ULTRAVOX_AGENT_ID: str = os.getenv("ULTRAVOX_AGENT_ID", "")
    
    #server configuration - dynamically get ngrok URL
    @property
    def SERVER_DOMAIN(self) -> str:
        return get_server_domain()
    
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    
    # Teler configuration
    TELER_API_KEY: str = os.getenv("TELER_API_KEY", "")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Other config
    CHUNK_BUFFER_SIZE: int = int(os.getenv("CHUNK_BUFFER_SIZE", 15000))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    
# settings instance
settings = Setting()