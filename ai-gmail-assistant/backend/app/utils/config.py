from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/auth/callback"
    
    # Ollama
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3"
    
    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "sqlite:///./gmail_assistant.db"
    
    # Application
    app_name: str = "AI Gmail Assistant"
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Follow-up intervals in days
    follow_up_intervals: str = "2,5,7"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_follow_up_days(self) -> List[int]:
        """Parse follow-up intervals from string to list of integers."""
        try:
            return [int(x.strip()) for x in self.follow_up_intervals.split(",")]
        except ValueError:
            return [2, 5, 7]


settings = Settings()
