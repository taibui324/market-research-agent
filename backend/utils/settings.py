"""
Configuration settings for the AI Challenge Market Research application.
"""
import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration class for xAI API settings using Pydantic Settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Required settings
    AIG_API_KEY: str = Field(
        ..., 
        description="xAI API key"
    )
    
    # Optional settings with defaults
    AIG_BASE_URL: str = Field(
        default="https://api.aig.deca-dev.com/v1",
        description="xAI API base URL"
    )
    
    AIG_ORGANIZATION_ID: str = Field(
        default="01haxd218s50f6yy4jf2f92fzf",
        description="Organization ID"
    )
    
    AIG_PROFILE_ID: str = Field(
        default="x-ai:grok-4-0709",
        description="AIG Profile ID"
    )
    
    AIG_MODEL_ID: str = Field(
        default="x-ai:grok-4-0709",
        description="Model ID to use"
    )
    
    AIG_SERVICE_ID: str = Field(
        default="ai-challenge",
        description="Service ID for API requests"
    )

    TIMEOUT: int = Field(
        default=30,
        description="Timeout for API requests"
    )
    
    MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retries for API requests"
    )
    
    def get_xai_settings(self) -> dict:
        """Get configuration for xAI client"""
        return {
            "api_key": self.AIG_API_KEY,
            "base_url": self.AIG_BASE_URL,
            "default_headers": {
                "x-api-key": self.AIG_API_KEY,
                "x-aig-organization-id": self.AIG_ORGANIZATION_ID,
                "x-aig-profile": self.AIG_PROFILE_ID,
                "x-service-id": self.AIG_SERVICE_ID
            },
            "timeout": self.TIMEOUT,
            "max_retries": self.MAX_RETRIES
        }
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        # This method can be implemented later if needed
        pass

def get_settings() -> Settings:
    """Get a new settings instance"""
    return Settings()
