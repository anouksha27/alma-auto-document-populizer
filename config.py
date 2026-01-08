"""Configuration management for the document automation system."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
FORM_URL = os.getenv("FORM_URL", "")

# Optional configuration with defaults
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "false").lower() == "true"
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

def validate_config() -> bool:
    """Validate required configuration variables.
    
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails with specific message
    """
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is required but not set. "
            "Please add it to your .env file."
        )
    
    if not FORM_URL:
        raise ValueError(
            "FORM_URL is required but not set. "
            "Please add it to your .env file."
        )
    
    if not FORM_URL.startswith(("http://", "https://")):
        raise ValueError(
            f"FORM_URL must start with http:// or https://. "
            f"Got: {FORM_URL}"
        )
    
    if MAX_FILE_SIZE_MB <= 0:
        raise ValueError(
            f"MAX_FILE_SIZE_MB must be a positive integer. "
            f"Got: {MAX_FILE_SIZE_MB}"
        )
    
    return True

