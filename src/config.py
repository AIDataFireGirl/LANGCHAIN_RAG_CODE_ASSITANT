"""
Configuration module for RAG Code Assistant
Handles environment variables, security settings, and application configuration
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseSettings, validator

# Load environment variables
load_dotenv()

class SecurityConfig:
    """Security configuration and guard rails"""
    
    # Maximum tokens for API calls to prevent abuse
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))
    
    # Rate limiting settings
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    
    # File size limits to prevent memory issues
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # Allowed file extensions for security
    SUPPORTED_EXTENSIONS = os.getenv("SUPPORTED_EXTENSIONS", 
        ".py,.js,.ts,.java,.cpp,.c,.h,.hpp,.cs,.go,.rs,.php,.rb,.swift,.kt,.scala,.dart,.r,.m,.pl,.sh,.sql,.html,.css,.xml,.json,.yaml,.yml,.md,.txt").split(",")
    
    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """Validate if file extension is allowed for security"""
        return any(filename.endswith(ext) for ext in cls.SUPPORTED_EXTENSIONS)
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """Validate file size for security"""
        return file_size <= cls.MAX_FILE_SIZE

class OpenAIConfig:
    """OpenAI API configuration"""
    
    API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(cls.API_KEY)

class DatabaseConfig:
    """Vector database configuration"""
    
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    COLLECTION_NAME = "codebase_embeddings"
    
    @classmethod
    def ensure_directory_exists(cls):
        """Ensure the database directory exists"""
        os.makedirs(cls.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

class AppConfig:
    """Application configuration"""
    
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # Security settings
    SECURITY = SecurityConfig()
    
    # API settings
    OPENAI = OpenAIConfig()
    
    # Database settings
    DATABASE = DatabaseConfig()
    
    @classmethod
    def validate_configuration(cls) -> bool:
        """Validate all configuration settings"""
        if not cls.OPENAI.is_configured():
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
        
        cls.DATABASE.ensure_directory_exists()
        return True

# Global configuration instance
config = AppConfig() 