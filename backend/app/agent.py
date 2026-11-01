"""Constrained coding-agent tools. All paths stay inside the configured workspace."""
import os
from pathlib import Path
import subprocess

ROOT = Path(os.getenv("WORKSPACE_ROOT", "/workspace")).resolve()
MAX_FILE_BYTES = 512_000
ALLOWED_COMMANDS = {
    "python -m pytest", "python -m compileall", "python -m unittest",
    "npm test", "npm run build", "npm run lint", "npm install",
    "pnpm test", "pnpm build", "pnpm lint", "git status --short", "git diff --"
}

class AgentToolError(ValueError):
    pass

def safe_path(relative: str) -> Path:
    candidate = (ROOT / relative).resolve()
    if candidate != ROOT and ROOT not in candidate.parents:
        raise AgentToolError("Path escapes the configured project workspace.")
    return candidate

def read_file(path: str) -> str:
    target = safe_path(path)
    if not target.is_file():
        raise AgentToolError("File does not exist.")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise AgentToolError("File is too large for this tool.")
    return target.read_text(encoding="utf-8")

def write_file(path: str, content: str) -> dict:
    target = safe_path(path)
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise AgentToolError("File exceeds the size limit.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": path, "bytes_written": len(content.encode("utf-8"))}

def list_files(path: str = ".") -> list[str]:
    folder = safe_path(path)
    if not folder.is_dir():
        raise AgentToolError("Directory does not exist.")
    ignored = {".git", "node_modules", ".venv", "__pycache__", ".next"}
    output = []
    for item in folder.rglob("*"):
        if any(part in ignored for part in item.parts):
            continue
        if item.is_file():
            output.append(str(item.relative_to(ROOT)))
        if len(output) >= 500:
            break
    return output

def run_check(command: str, timeout: int = 120) -> dict:
    if not any(command == allowed or (allowed.endswith(" --") and command.startswith(allowed)) for allowed in ALLOWED_COMMANDS):
        raise AgentToolError("Command is not on the development-check allowlist.")
    # No shell: parse into argv and execute only inside the project workspace.
    import shlex
    argv = shlex.split(command)
    if not argv or any(x in {";", "&&", "||", "|", ">", "<", "$("} for x in argv):
        raise AgentToolError("Shell operators are not supported.")
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=min(max(timeout, 1), 180), check=False)
    return {"returncode": result.returncode, "stdout": result.stdout[-12000:], "stderr": result.stderr[-12000:]}
