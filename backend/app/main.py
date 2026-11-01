import json, os
from typing import AsyncIterator
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

OLLAMA = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5:3b")
ORIGINS = [v.strip() for v in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if v.strip()]
app = FastAPI(title="UniverseAI API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

class Message(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str = Field(min_length=1, max_length=20000)

class ChatRequest(BaseModel):
    model: str = Field(default=DEFAULT_MODEL, min_length=1, max_length=120)
    messages: list[Message] = Field(min_length=1, max_length=60)
    temperature: float = Field(default=0.7, ge=0, le=2)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "universeai-api"}

@app.get("/api/models")
async def models():
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(f"{OLLAMA}/api/tags")
            response.raise_for_status()
            payload = response.json()
        return {"models": [{"name": m.get("name", ""), "size": m.get("size", 0)}
                           for m in payload.get("models", [])], "default": DEFAULT_MODEL}
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=503, detail="Ollama unavailable. Start it and pull a model.")

@app.post("/api/chat")
async def chat(body: ChatRequest):
    payload = {"model": body.model, "messages": [m.model_dump() for m in body.messages],
               "stream": True, "options": {"temperature": body.temperature}}
    async def events() -> AsyncIterator[str]:
        try:
            timeout = httpx.Timeout(connect=10, read=None, write=30, pool=10)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", f"{OLLAMA}/api/chat", json=payload) as response:
                    if response.status_code >= 400:
                        yield "data: " + json.dumps({"error":"Ollama rejected request; check installed model."}) + "\n\n"
                        return
                    async for line in response.aiter_lines():
                        if not line: continue
                        try: item = json.loads(line)
                        except json.JSONDecodeError: continue
                        if item.get("error"):
                            yield "data: " + json.dumps({"error":"Model returned an error."}) + "\n\n"
                            return
                        token = item.get("message", {}).get("content", "")
                        if token: yield "data: " + json.dumps({"token":token}, ensure_ascii=False) + "\n\n"
                        if item.get("done"):
                            yield 'data: {"done":true}\n\n'
                            return
        except httpx.HTTPError:
            yield "data: " + json.dumps({"error":"Cannot connect to Ollama. Check model service."}) + "\n\n"
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
