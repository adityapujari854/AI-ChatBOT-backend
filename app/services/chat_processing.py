# app/services/chat_processing.py

from pymongo import MongoClient
from datetime import datetime
from app.utils.translate import translate_text, detect_language
from app.utils.llm import query_llm, format_llm_response, stream_llm_response
from pydantic import BaseModel
from typing import List
import os
import asyncio

# Mongo URI from .env
MongoURI = os.getenv("MongoURI")
client = MongoClient(MongoURI)
db = client["chatbot_db"]
chat_history_collection = db["chat_history"]
chat_sessions_collection = db["chat_sessions"]

# Chat History Document Schema
class ChatHistory(BaseModel):
    session_id: str
    user_id: str
    user_prompt: str
    translated_prompt: str
    llm_response: str
    final_response: str
    language: str
    timestamp: datetime

# Chat Session Metadata Schema
class ChatSession(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime

# Save chat + optionally create session
def save_chat_history(session_id: str, user_id: str, user_message: str, translated_prompt: str, llm_response: str, final_response: str, language: str) -> None:
    try:
        chat_entry = ChatHistory(
            session_id=session_id,
            user_id=user_id,
            user_prompt=user_message,
            translated_prompt=translated_prompt,
            llm_response=llm_response,
            final_response=final_response,
            language=language,
            timestamp=datetime.utcnow()
        )
        chat_history_collection.insert_one(chat_entry.dict())

        if not chat_sessions_collection.find_one({"id": session_id}):
            session_doc = ChatSession(
                id=session_id,
                user_id=user_id,
                title=user_message.strip()[:50] or "Untitled Chat",
                created_at=datetime.utcnow()
            )
            chat_sessions_collection.insert_one(session_doc.dict())

        print(f"[DB] Chat saved for session: {session_id}")
    except Exception as e:
        print(f"[ERROR - save_chat_history]: {e}")
        raise

# Get last 10 messages for a session
def get_chat_history_by_session(session_id: str) -> List[dict]:
    try:
        messages = chat_history_collection.find({"session_id": session_id}).sort("timestamp", -1).limit(10)
        return [
            {
                "user": msg.get("user_prompt", ""),
                "ai": msg.get("final_response", "")
            }
            for msg in messages
        ]
    except Exception as e:
        print(f"[ERROR - get_chat_history_by_session]: {e}")
        raise

# Get all chat sessions for a user
def get_user_chat_sessions(user_id: str) -> List[dict]:
    try:
        sessions = chat_sessions_collection.find({"user_id": user_id}).sort("created_at", -1)
        return [
            {
                "id": session.get("id"),
                "title": session.get("title", "Untitled"),
                "created_at": session.get("created_at").isoformat() if session.get("created_at") else ""
            }
            for session in sessions
        ]
    except Exception as e:
        print(f"[ERROR - get_user_chat_sessions]: {e}")
        raise

# Non-streaming chat processing
def process_chat(request: dict) -> dict:
    try:
        prompt = request.get("prompt")
        language = request.get("language", "en")
        if not request.get("session_id"):
            raise ValueError("Session ID is required")

        detected_language = detect_language(prompt)
        translated_prompt = prompt if detected_language == language else translate_text(prompt, "en")

        llm_output = query_llm(translated_prompt, model="openrouter-mistral", session_id=request["session_id"], language=language, format="raw")

        if not isinstance(llm_output, str):
            raise ValueError("LLM did not return a valid string response")

        raw_response = llm_output if language == "en" or detected_language == language else translate_text(llm_output, language)
        final_response = format_llm_response(raw_response, format="html")

        print("[FINAL HTML OUTPUT]", final_response)

        return {
            "translated_prompt": translated_prompt,
            "llm_response": raw_response,
            "final_response": final_response
        }

    except Exception as e:
        print(f"[ERROR - process_chat]: {e}")
        raise

# Streaming version with chunk filtering
async def stream_chat_response(request: dict):
    prompt = request.get("prompt", "")
    session_id = request.get("session_id", None)
    language = request.get("language", "en")

    detected_language = detect_language(prompt)
    translated_prompt = prompt if detected_language == language else translate_text(prompt, "en")

    async for chunk in stream_llm_response(translated_prompt, session_id=session_id, language=language):
        translated_chunk = chunk if language == "en" or detected_language == language else translate_text(chunk, target_lang=language)
        if translated_chunk.strip():
            yield translated_chunk
