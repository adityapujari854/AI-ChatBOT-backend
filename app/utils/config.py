import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """General application configuration."""
    PROJECT_NAME: str = "AI Chat Backend"
    API_PREFIX: str = "/api/v1"  # API versioning

    # Debug mode
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"  # Simplified

    # CORS settings
    ALLOWED_ORIGINS: list =["*"]
    # ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # Backend URL
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Google Translate API Key
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")

    # Raise an error if the API key is not set
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in the environment. Please define it in your .env file.")

# Instantiate the configuration
config = Config()
