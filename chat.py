import os
import requests
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read MongoDB config from environment
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "chatdb")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "messages")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is not set in the .env file.")

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
messages_col = db[MONGODB_COLLECTION]

# Insert an empty document for testing connection (optional)
sender = "system"
messages = []
result = messages_col.insert_one({
    "messages": [
        {"sender": sender, "messages": messages}
    ]
})
print(f"Inserted test document with ID: {result.inserted_id}")

# Initialize FastAPI app
app = FastAPI()

# Mount static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Enable CORS (for frontend calls)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class ChatIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    session_id: Optional[str] = None
    username: Optional[str] = "user"

class Message(BaseModel):
    session_id: str
    role: str
    text: str
    created_at: datetime

class ChatOut(BaseModel):
    session_id: str
    reply: str
    history: List[Message]

# --- Utility Functions ---
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _assistant_reply(user_text: str) -> str:
    try:
        response = requests.post(
            "https://0e7f12ff15e8.ngrok-free.app/generate",  # update with actual URL
            json={"prompt": user_text},
            timeout=180
        )
        response.raise_for_status()
        return response.json().get("response", "No reply from LLM.")
    except Exception as e:
        print("🔴 Error contacting LLM API:", e)
        return "Sorry, the model is not responding right now."


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat", response_class=HTMLResponse)
async def chat_ui(request: Request, message: str = Form(...)):
    response = _assistant_reply(message)
    return templates.TemplateResponse("index.html", {"request": request, "response": response})

@app.post("/api/chat", response_model=ChatOut)
def chat_api(payload: ChatIn):
    try:
        session_id = payload.session_id or str(uuid4())

        user_doc = {
            "session_id": session_id,
            "role": "user",
            "text": payload.text,
            "username": payload.username or "user",
            "created_at": _now_utc(),
        }
        messages_col.insert_one(user_doc)

        reply_text = _assistant_reply(payload.text)

        assistant_doc = {
            "session_id": session_id,
            "role": "assistant",
            "text": reply_text,
            "created_at": _now_utc(),
        }
        messages_col.insert_one(assistant_doc)

        history_cursor = messages_col.find({"session_id": session_id}).sort("created_at", 1).limit(50)
        history = [
            Message(
                session_id=doc["session_id"],
                role=doc["role"],
                text=doc["text"],
                created_at=doc["created_at"],
            )
            for doc in history_cursor
        ]

        return ChatOut(session_id=session_id, reply=reply_text, history=history)

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/api/history", response_model=List[Message])
def get_history(session_id: str):
    try:
        history_cursor = messages_col.find({"session_id": session_id}).sort("created_at", 1).limit(200)
        return [
            Message(
                session_id=doc["session_id"],
                role=doc["role"],
                text=doc["text"],
                created_at=doc["created_at"],
            )
            for doc in history_cursor
        ]
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/api/health")
def health():
    return {"ok": True, "time": _now_utc().isoformat()}
