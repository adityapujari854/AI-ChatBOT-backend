# app/services/chat.py

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import asyncio

# Import the necessary functions from the new chat_processing module to avoid circular imports
from app.services.chat_processing import process_chat, get_chat_history_by_session, save_chat_history, get_user_chat_sessions
from app.services.chat_processing import stream_chat_response

router = APIRouter()

# Request structure for chat input
class ChatRequest(BaseModel):
    prompt: str
    language: str = "en"
    session_id: str
    user_id: str

# Response structure for chat output
class ChatResponse(BaseModel):
    response: str

# History response
class HistoryResponse(BaseModel):
    history: List[dict]

# Session list structure
class ChatSessionSummary(BaseModel):
    id: str
    title: str
    created_at: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handles user input:
    - Translates if needed.
    - Sends to LLM.
    - Saves in DB with session/user context.
    """
    try:
        print(f"[User Input in {request.language} | Session: {request.session_id} | User: {request.user_id}]: {request.prompt}")

        # Process chat and get all necessary outputs from LLM
        result = process_chat({
            "prompt": request.prompt,
            "language": request.language,
            "session_id": request.session_id
        })

        print(f"[LLM Response]: {result['final_response']}")

        # Save chat using already available data
        save_chat_history(
            session_id=request.session_id,
            user_id=request.user_id,
            user_message=request.prompt,
            translated_prompt=result["translated_prompt"],
            llm_response=result["llm_response"],
            final_response=result["final_response"],
            language=request.language
        )

        return ChatResponse(response=result["final_response"])

    except Exception as e:
        print(f"[ERROR /chat]: {str(e)}")
        raise HTTPException(status_code=500, detail="Something went wrong during chat.")


@router.post("/chat/stream")
async def chat_stream(request: Request):
    """
    Streaming chat response endpoint.
    Compatible with frontend streaming (e.g., EventSource or fetch streaming).
    """
    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        session_id = body.get("session_id")
        language = body.get("language", "en")

        if not session_id:
            raise ValueError("Session ID is required")

        print(f"[Stream Start | Session: {session_id} | Lang: {language}]: {prompt}")

        # Async generator to stream data
        async def event_generator():
            try:
                async for chunk in stream_chat_response({
                    "prompt": prompt,
                    "language": language,
                    "session_id": session_id
                }):
                    if chunk.strip():  # Ensure empty chunks aren't streamed
                        yield chunk
            except asyncio.CancelledError:
                # Gracefully handle when the stream is cancelled
                print(f"[STREAM CANCELLED]: Session {session_id}")
                return

        # Return StreamingResponse for frontend to consume the chunks
        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        print(f"[ERROR /chat/stream]: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in streaming response.")


@router.get("/history", response_model=HistoryResponse)
async def get_history(session_id: str = Query(..., description="Chat session ID")):
    try:
        history = get_chat_history_by_session(session_id)
        return {"history": history}
    except Exception as e:
        print(f"[ERROR /history]: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching chat history.")


@router.get("/sessions", response_model=List[ChatSessionSummary])
async def list_sessions(user_id: str = Query(..., description="User ID to filter sessions")):
    try:
        sessions = get_user_chat_sessions(user_id)
        return sessions
    except Exception as e:
        print(f"[ERROR /sessions]: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to fetch chat sessions.")
