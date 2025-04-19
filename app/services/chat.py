from pymongo import MongoClient
from datetime import datetime
from app.utils.translate import translate_text
from app.utils.llm import query_llm, stream_llm_response
from pydantic import BaseModel
from typing import List
import os

# Mongo URI from .env
MongoURI: str = os.getenv("MongoURI")
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
    id: str  # session_id
    user_id: str
    title: str
    created_at: datetime

# Save chat + optionally create session
def save_chat_history(session_id: str, user_id: str, user_message: str, assistant_message: str, language: str) -> None:
    try:
        translated_prompt = translate_text(user_message, target_lang="en") if language != "en" else user_message
        llm_response = query_llm(translated_prompt)
        final_response = translate_text(llm_response, target_lang=language) if language != "en" else llm_response

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
def process_chat(request: dict) -> str:
    try:
        prompt = request.get("prompt")
        language = request.get("language", "en")

        if not request.get("session_id"):
            raise ValueError("Session ID is required")

        translated = translate_text(prompt, "en") if language != "en" else prompt
        llm_output = query_llm(translated, model="openrouter-mistral")
        final_output = translate_text(llm_output, language) if language != "en" else llm_output
        chunked_output = final_output.replace('. ', '.\n')
        return chunked_output
    except Exception as e:
        print(f"[ERROR - process_chat]: {e}")
        raise

# 🔥 Streaming version with chunk filtering
async def stream_chat_response(request: dict):
    prompt = request.get("prompt", "")
    session_id = request.get("session_id", None)
    language = request.get("language", "en")

    translated_prompt = translate_text(prompt, "en") if language != "en" else prompt

    async for chunk in stream_llm_response(translated_prompt, session_id=session_id):
        translated_chunk = translate_text(chunk, target_lang=language) if language != "en" else chunk
        if translated_chunk.strip():  # ⬅️ Only yield non-empty text
            yield translated_chunk
