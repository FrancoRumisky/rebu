"""
Core configuration module using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    """Application settings"""
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Rebu API"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
   # Database
    DATABASE_URL: Optional[str] = None  # <- para Neon/Render

    POSTGRES_USER: str = "rebu"
    POSTGRES_PASSWORD: str = "rebu_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "rebu_db"

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FCM_SERVER_KEY: Optional[str] = None
    
    # Matching Configuration
    MATCHING_RADIUS_KM: float = 10.0  # Initial search radius
    MATCHING_WAVE_1_RADIUS_KM: float = 3.0
    MATCHING_WAVE_2_RADIUS_KM: float = 5.0
    MATCHING_WAVE_3_RADIUS_KM: float = 10.0
    MATCHING_WAVE_DELAY_SECONDS: int = 30  # Delay between waves
    
    OFFER_EXPIRY_SECONDS: int = 60  # Driver has 60s to accept
    TRIP_REQUEST_EXPIRY_MINUTES: int = 15  # On-demand expires in 15 min
    
    # Scheduled Trips
    SCHEDULED_REMINDER_MINUTES: list[int] = [60, 15]  # T-60min and T-15min
    SCHEDULED_CONFIRM_WINDOW_MINUTES: int = 30  # Confirm 30min before
    
    # Commission Rates by Subscription
    COMMISSION_FREE: float = 0.15  # 15%
    COMMISSION_PRO: float = 0.10   # 10%
    COMMISSION_PREMIUM: float = 0.05  # 5%
    
    # Wallet
    WALLET_CREDIT_LIMIT_FREE: float = 500.0
    WALLET_CREDIT_LIMIT_PRO: float = 1000.0
    WALLET_CREDIT_LIMIT_PREMIUM: float = 2000.0
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Workers
    ENABLE_BACKGROUND_WORKERS: bool = True

    # Google Client ID
    GOOGLE_CLIENT_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
