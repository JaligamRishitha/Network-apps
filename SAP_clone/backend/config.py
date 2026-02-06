"""Application configuration management using Pydantic Settings"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "postgresql+asyncpg://sapuser:sappassword@149.102.158.71:5432/saperp"
    
    # JWT Authentication
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Integration Layer
    camel_webhook_url: str = "http://mulesoft-backend:4797/api/sap/webhook/sap-events"
    
    # SLA Configuration (in hours)
    sla_p1_hours: int = 4
    sla_p2_hours: int = 8
    sla_p3_hours: int = 24
    sla_p4_hours: int = 72
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
