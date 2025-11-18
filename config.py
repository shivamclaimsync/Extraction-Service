"""Configuration settings for the extraction service."""

from typing import Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, computed_field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    All settings can be overridden via environment variables with the same name.
    """
    
    # Database configuration - can be set directly or constructed from individual vars
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection URL with asyncpg driver. "
                    "Example: postgresql+asyncpg://user:pass@localhost/dbname"
    )
    
    # Individual database connection variables (for constructing DATABASE_URL)
    pg_hospital_host: Optional[str] = Field(
        default=None,
        description="PostgreSQL host"
    )
    pg_hospital_port: Optional[str] = Field(
        default="5432",
        description="PostgreSQL port"
    )
    pg_hospital_database: Optional[str] = Field(
        default=None,
        description="PostgreSQL database name"
    )
    pg_hospital_user: Optional[str] = Field(
        default=None,
        description="PostgreSQL username"
    )
    pg_hospital_password: Optional[str] = Field(
        default=None,
        description="PostgreSQL password"
    )
    
    @computed_field
    @property
    def effective_database_url(self) -> str:
        """Get database URL, either from DATABASE_URL or constructed from individual vars."""
        if self.database_url:
            return self.database_url
        
        # Construct from individual variables
        if all([self.pg_hospital_host, self.pg_hospital_database, 
                self.pg_hospital_user, self.pg_hospital_password]):
            encoded_password = quote_plus(self.pg_hospital_password)
            return (
                f"postgresql+asyncpg://{self.pg_hospital_user}:{encoded_password}"
                f"@{self.pg_hospital_host}:{self.pg_hospital_port}/{self.pg_hospital_database}"
            )
        
        raise ValueError(
            "Either DATABASE_URL must be set, or all of PG_HOSPITAL_HOST, "
            "PG_HOSPITAL_DATABASE, PG_HOSPITAL_USER, and PG_HOSPITAL_PASSWORD must be set"
        )
    database_echo: bool = Field(
        default=False,
        description="Whether to log all SQL statements (useful for debugging)"
    )
    database_pool_size: int = Field(
        default=5,
        ge=1,
        description="Number of connections to maintain in the connection pool"
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        description="Maximum number of connections to create beyond pool_size"
    )
    
    # OpenAI/LLM configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for LLM calls"
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model name to use for extraction"
    )
    llm_timeout: int = Field(
        default=180,
        ge=30,
        description="Timeout for LLM calls in seconds"
    )
    
    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Path to log file (if None, logs to console only)"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()

