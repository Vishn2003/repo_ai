import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class Config:
    # API key configuration
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    # Model configuration
    DEFAULT_MODEL = "models/gemini-3.1-flash-lite"
    TEMPERATURE = 0.1
    
    # Execution parameters
    SLEEP_TIME = 12.0  # seconds sleep between calls to respect 5 RPM limit
    MAX_RETRIES = 3
    
    # Dataset configurations
    DATASET_ROOT = os.environ.get("DATASET_ROOT", "dataset")
    
    @classmethod
    def get_api_key(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your environment or .env file.")
        return cls.GEMINI_API_KEY
