import os
from collections.abc import AsyncIterator
import httpx

class ProviderError(Exception):
    pass

class OllamaProvider:
    def __init__(self):
        self.base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
    async def models(self):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.base}/api/tags")
            response.raise_for_status()
            return [m.get("name", "") for m in response.json().get("models", [])]
    async def stream(self, model: str, messages: list[dict], temperature: float = 0.7) -> AsyncIterator[str]:
        payload = {"model": model, "messages": messages, "stream": True, "options": {"temperature": temperature}}
        timeout = httpx.Timeout(connect=10, read=None, write=30, pool=10)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", f"{self.base}/api/chat", json=payload) as response:
                if response.status_code >= 400:
                    raise ProviderError("The local model provider rejected the request.")
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        item = __import__("json").loads(line)
                    except ValueError:
                        continue
                    if item.get("error"):
                        raise ProviderError("The model returned an error.")
                    token = item.get("message", {}).get("content", "")
                    if token:
                        yield token

def get_provider(name: str = "ollama"):
    if name != "ollama":
        raise ProviderError("This provider is not configured. Ollama is available in this release.")
    return OllamaProvider()
