from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Ensure Google Application Credentials path is loaded
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not GOOGLE_CREDENTIALS_PATH:
    raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS not set in .env file")

# Local imports
from app.routes import chats
from app.utils.config import config

# Initialize the FastAPI app
app = FastAPI()

# CORS configuration to allow frontend requests from specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",  # Allow all origins, change as needed for production
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

# Include the router for the chat functionality
app.include_router(chats.router, prefix="/api", tags=["chat"])

# Default route for testing
@app.get("/")
def read_root():
    return {"msg": f"Welcome to {config.PROJECT_NAME}"}
