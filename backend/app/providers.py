import os,json
from collections.abc import AsyncIterator
import httpx

class ProviderError(Exception): pass

class OllamaProvider:
    def __init__(self): self.base=os.getenv("OLLAMA_BASE_URL","http://ollama:11434").rstrip("/")
    async def models(self):
        async with httpx.AsyncClient(timeout=10) as client:
            r=await client.get(f"{self.base}/api/tags");r.raise_for_status()
            return [m.get("name","") for m in r.json().get("models",[])]
    async def stream(self,model:str,messages:list[dict],temperature:float=.7)->AsyncIterator[str]:
        payload={"model":model,"messages":messages,"stream":True,"options":{"temperature":temperature}}
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10,read=None,write=30,pool=10)) as client:
            async with client.stream("POST",f"{self.base}/api/chat",json=payload) as r:
                if r.status_code>=400: raise ProviderError("The local model provider rejected the request.")
                async for line in r.aiter_lines():
                    if not line: continue
                    try: item=json.loads(line)
                    except ValueError: continue
                    if item.get("error"): raise ProviderError("The model returned an error.")
                    token=item.get("message",{}).get("content","")
                    if token: yield token

class OpenAICompatibleProvider:
    """Works with OpenAI-compatible servers such as vLLM, LM Studio and hosted gateways."""
    def __init__(self):
        self.base=os.getenv("OPENAI_COMPAT_BASE_URL","").rstrip("/")
        self.key=os.getenv("OPENAI_COMPAT_API_KEY","")
    def headers(self):
        h={"Content-Type":"application/json"}
        if self.key: h["Authorization"]="Bearer "+self.key
        return h
    async def models(self):
        if not self.base: raise ProviderError("Set OPENAI_COMPAT_BASE_URL to enable this provider.")
        async with httpx.AsyncClient(timeout=10) as client:
            r=await client.get(self.base+"/models",headers=self.headers());r.raise_for_status()
            return [x.get("id","") for x in r.json().get("data",[]) if x.get("id")]
    async def stream(self,model:str,messages:list[dict],temperature:float=.7)->AsyncIterator[str]:
        if not self.base: raise ProviderError("Set OPENAI_COMPAT_BASE_URL to enable this provider.")
        payload={"model":model,"messages":messages,"stream":True,"temperature":temperature}
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10,read=None,write=30,pool=10)) as client:
            async with client.stream("POST",self.base+"/chat/completions",headers=self.headers(),json=payload) as r:
                if r.status_code>=400: raise ProviderError("The configured model provider rejected the request.")
                async for line in r.aiter_lines():
                    if not line.startswith("data: "): continue
                    data=line[6:]
                    if data=="[DONE]": return
                    try: item=json.loads(data)
                    except ValueError: continue
                    choices=item.get("choices",[])
                    if choices:
                        token=choices[0].get("delta",{}).get("content","")
                        if isinstance(token,str) and token: yield token

def get_provider(name:str="ollama"):
    if name=="ollama": return OllamaProvider()
    if name=="openai-compatible": return OpenAICompatibleProvider()
    raise ProviderError("Unknown model provider.")
