import tempfile
from pathlib import Path
from app import agent

def test_workspace_path_is_confined(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(agent,"ROOT",Path(folder).resolve())
        assert agent.safe_path("src/main.py")==Path(folder).resolve()/"src/main.py"
        try:
            agent.safe_path("../outside.txt")
            assert False,"path traversal should be rejected"
        except agent.AgentToolError:
            pass

def test_file_roundtrip(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(agent,"ROOT",Path(folder).resolve())
        agent.write_file("hello.txt","UniverseAI")
        assert agent.read_file("hello.txt")=="UniverseAI"

def test_user_workspaces_are_separate(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder).resolve()
        monkeypatch.setattr(agent,"ROOT",root)
        one=agent.user_root(1)
        two=agent.user_root(2)
        agent.write_file("private.txt","account one",one)
        assert agent.read_file("private.txt",one)=="account one"
        try:
            agent.read_file("private.txt",two)
            assert False,"account two must not read account one's files"
        except agent.AgentToolError:
            pass

def test_command_allowlist_rejects_shell_injection():
    try:
        agent.run_check("python -m pytest && echo unsafe")
        assert False,"shell operators must be rejected"
    except agent.AgentToolError:
        pass
