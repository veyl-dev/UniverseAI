"""Workspace-confined coding tools with per-user project roots."""
import os,shlex,subprocess
from pathlib import Path
ROOT=Path(os.getenv("WORKSPACE_ROOT","/workspace")).resolve()
MAX_FILE_BYTES=512_000
ALLOWED_COMMANDS={"python -m pytest","python -m compileall","python -m unittest","npm test","npm run build","npm run lint","pnpm test","pnpm build","pnpm lint","git status --short","git diff --"}
class AgentToolError(ValueError): pass
def user_root(user_id:int)->Path:
    root=(ROOT/f"user-{user_id}").resolve()
    if ROOT not in root.parents: raise AgentToolError("Invalid workspace.")
    root.mkdir(parents=True,exist_ok=True)
    return root
def safe_path(relative:str,root:Path|None=None)->Path:
    base=(root or ROOT).resolve()
    target=(base/relative).resolve()
    if target!=base and base not in target.parents: raise AgentToolError("Path escapes the configured project workspace.")
    return target
def read_file(path:str,root:Path|None=None)->str:
    target=safe_path(path,root)
    if not target.is_file(): raise AgentToolError("File does not exist.")
    if target.stat().st_size>MAX_FILE_BYTES: raise AgentToolError("File exceeds the read limit.")
    return target.read_text(encoding="utf-8")
def write_file(path:str,content:str,root:Path|None=None)->dict:
    target=safe_path(path,root)
    if len(content.encode("utf-8"))>MAX_FILE_BYTES: raise AgentToolError("File exceeds the write limit.")
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding="utf-8")
    return {"path":path,"bytes_written":len(content.encode("utf-8"))}
def list_files(path:str=".",root:Path|None=None)->list[str]:
    base=(root or ROOT).resolve();folder=safe_path(path,base)
    if not folder.is_dir(): raise AgentToolError("Directory does not exist.")
    ignored={".git","node_modules",".venv","__pycache__",".next"}
    result=[]
    for item in folder.rglob("*"):
        if any(part in ignored for part in item.parts): continue
        if item.is_file():
            resolved=item.resolve()
            if base not in resolved.parents: continue
            result.append(str(resolved.relative_to(base)))
        if len(result)>=500: break
    return result
def run_check(command:str,timeout:int=120,root:Path|None=None)->dict:
    if not any(command==item or (item.endswith(" --") and command.startswith(item)) for item in ALLOWED_COMMANDS):
        raise AgentToolError("Command is not on the development-check allowlist.")
    argv=shlex.split(command)
    if not argv or any(x in {";","&&","||","|",">","<","$("} for x in argv): raise AgentToolError("Shell operators are not supported.")
    cwd=(root or ROOT).resolve()
    if not cwd.is_dir(): raise AgentToolError("Workspace does not exist.")
    result=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=min(max(timeout,1),180),check=False)
    return {"returncode":result.returncode,"stdout":result.stdout[-12000:],"stderr":result.stderr[-12000:]}
