from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Absolute path to your credentials JSON
DEFAULT_CREDENTIALS_PATH = r"C:\Users\adity\Documents\AI ChatBOT\backend\ai-chatbot-456710-14a3e3bded79.json"

# Set GOOGLE_APPLICATION_CREDENTIALS if not already set
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = DEFAULT_CREDENTIALS_PATH

# Local imports
from app.routes import chat
from app.utils.config import config

# Initialize the FastAPI app
app = FastAPI()

# CORS configuration to allow frontend requests from specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

# Include the router for the chat functionality
app.include_router(chat.router, prefix="/api", tags=["chat"])

# Default route for testing
@app.get("/")
def read_root():
    return {"msg": f"Welcome to {config.PROJECT_NAME}"}
