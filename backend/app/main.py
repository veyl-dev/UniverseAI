import json, os
from typing import Annotated
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import ChatMessage, Conversation, User
from .security import create_access_token, decode_subject, hash_password, verify_password
from .providers import get_provider, ProviderError
from . import agent

Base.metadata.create_all(bind=engine)
app = FastAPI(title="UniverseAI API", version="0.2.0")
origins = [v.strip() for v in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if v.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET","POST","PUT","DELETE"], allow_headers=["Authorization","Content-Type"])

class AuthInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
class ConversationInput(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=160)
    model: str = Field(default="qwen2.5:3b", min_length=1, max_length=160)
class MessageInput(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=30000)
class ChatInput(BaseModel):
    model: str = Field(default="qwen2.5:3b", min_length=1, max_length=160)
    messages: list[MessageInput] = Field(min_length=1, max_length=80)
    temperature: float = Field(default=0.7, ge=0, le=2)
    conversation_id: int | None = None
class AgentRead(BaseModel):
    path: str = Field(min_length=1, max_length=500)
class AgentWrite(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    content: str = Field(max_length=500000)
class AgentCheck(BaseModel):
    command: str = Field(min_length=1, max_length=200)

def current_user(authorization: Annotated[str | None, Header()] = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in required.")
    subject = decode_subject(authorization[7:])
    if not subject:
        raise HTTPException(401, "Session expired or invalid.")
    user = db.get(User, int(subject))
    if not user:
        raise HTTPException(401, "Account not found.")
    return user

@app.get("/health")
def health():
    return {"status":"ok","service":"universeai-api","version":"0.2.0"}

@app.post("/api/auth/register")
def register(body: AuthInput, db: Session = Depends(get_db)):
    email = str(body.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists.")
    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token":create_access_token(str(user.id)), "token_type":"bearer", "user":{"id":user.id,"email":user.email}}

@app.post("/api/auth/login")
def login(body: AuthInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    return {"access_token":create_access_token(str(user.id)), "token_type":"bearer", "user":{"id":user.id,"email":user.email}}

@app.get("/api/me")
def me(user: User = Depends(current_user)):
    return {"id":user.id,"email":user.email}

@app.get("/api/models")
async def models(user: User = Depends(current_user)):
    try:
        names = await get_provider("ollama").models()
        return {"models":[{"name":n} for n in names], "default":os.getenv("OLLAMA_DEFAULT_MODEL","qwen2.5:3b")}
    except Exception:
        raise HTTPException(503, "Ollama is unavailable. Start it and install a model.")

@app.get("/api/conversations")
def conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())).all()
    return [{"id":c.id,"title":c.title,"model":c.model,"updated_at":c.updated_at.isoformat()} for c in rows]

@app.post("/api/conversations")
def create_conversation(body: ConversationInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = Conversation(user_id=user.id, title=body.title, model=body.model)
    db.add(item); db.commit(); db.refresh(item)
    return {"id":item.id,"title":item.title,"model":item.model}

@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if not item: raise HTTPException(404, "Conversation not found.")
    return {"id":item.id,"title":item.title,"model":item.model,"messages":[{"role":m.role,"content":m.content} for m in item.messages]}

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if not item: raise HTTPException(404, "Conversation not found.")
    db.delete(item); db.commit()
    return {"deleted":True}

@app.post("/api/chat")
async def chat(body: ChatInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conversation = None
    if body.conversation_id is not None:
        conversation = db.scalar(select(Conversation).where(Conversation.id == body.conversation_id, Conversation.user_id == user.id))
        if not conversation: raise HTTPException(404, "Conversation not found.")
    else:
        first = next((m.content for m in body.messages if m.role == "user"), "New conversation")
        conversation = Conversation(user_id=user.id, title=first[:72], model=body.model)
        db.add(conversation); db.commit(); db.refresh(conversation)
    last_user = next((m for m in reversed(body.messages) if m.role == "user"), None)
    if last_user:
        db.add(ChatMessage(conversation_id=conversation.id, role="user", content=last_user.content))
    conversation.model = body.model
    db.commit()
    payload = [{"role":m.role,"content":m.content} for m in body.messages]
    async def events():
        answer = ""
        try:
            async for token in get_provider("ollama").stream(body.model, payload, body.temperature):
                answer += token
                yield "data: " + json.dumps({"token":token}, ensure_ascii=False) + "\\n\\n"
            if answer:
                db.add(ChatMessage(conversation_id=conversation.id, role="assistant", content=answer))
                db.commit()
            yield "data: " + json.dumps({"done":True,"conversation_id":conversation.id}) + "\\n\\n"
        except ProviderError as exc:
            yield "data: " + json.dumps({"error":str(exc)}) + "\n\n"
        except Exception:
            yield "data: " + json.dumps({"error":"Model provider connection failed."}) + "\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@app.post("/api/agent/files/read")
def agent_read(body: AgentRead, user: User = Depends(current_user)):
    try: return {"path":body.path,"content":agent.read_file(body.path)}
    except agent.AgentToolError as exc: raise HTTPException(400, str(exc))

@app.get("/api/agent/files")
def agent_files(path: str = ".", user: User = Depends(current_user)):
    try: return {"files":agent.list_files(path)}
    except agent.AgentToolError as exc: raise HTTPException(400, str(exc))

@app.put("/api/agent/files")
def agent_write(body: AgentWrite, user: User = Depends(current_user)):
    try: return agent.write_file(body.path, body.content)
    except agent.AgentToolError as exc: raise HTTPException(400, str(exc))

@app.post("/api/agent/check")
def agent_check(body: AgentCheck, user: User = Depends(current_user)):
    try: return agent.run_check(body.command)
    except agent.AgentToolError as exc: raise HTTPException(400, str(exc))
