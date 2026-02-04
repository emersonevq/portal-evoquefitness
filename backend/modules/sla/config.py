from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Configurações da aplicação SLA"""
    
    # Database (herda do main backend)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost:3306/evoque"
    )
    
    # Horário comercial
    BUSINESS_HOUR_START: int = 8
    BUSINESS_HOUR_END: int = 18
    BUSINESS_DAYS: List[int] = [0, 1, 2, 3, 4]  # 0=Segunda, 4=Sexta
    
    # Scheduler
    SLA_RECALC_INTERVAL_MINUTES: int = 5
    SLA_CHECK_RISK_INTERVAL_MINUTES: int = 10
    
    # SLA Thresholds
    SLA_RISCO_PERCENTUAL: int = 80
    
    # Cache
    CACHE_TTL_MINUTES: int = 60
    
    # API
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
