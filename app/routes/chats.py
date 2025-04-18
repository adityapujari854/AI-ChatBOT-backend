from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from app.services.chat import (
    process_chat,
    get_chat_history_by_session,
    save_chat_history,
    get_user_chat_sessions
)

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

        final_response = process_chat({
            "prompt": request.prompt,
            "language": request.language,
            "session_id": request.session_id
        })

        print(f"[LLM Response]: {final_response}")

        save_chat_history(
            session_id=request.session_id,
            user_id=request.user_id,
            user_message=request.prompt,
            assistant_message=final_response,
            language=request.language
        )

        return ChatResponse(response=final_response)

    except Exception as e:
        print(f"[ERROR /chat]: {str(e)}")
        raise HTTPException(status_code=500, detail="Something went wrong during chat.")


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
