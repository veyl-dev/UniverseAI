import tempfile
from pathlib import Path
from app import agent

def test_workspace_path_is_confined(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(agent, "ROOT", Path(folder).resolve())
        assert agent.safe_path("src/main.py") == Path(folder).resolve() / "src/main.py"
        try:
            agent.safe_path("../outside.txt")
            assert False, "path traversal should be rejected"
        except agent.AgentToolError:
            pass

def test_file_roundtrip(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(agent, "ROOT", Path(folder).resolve())
        agent.write_file("hello.txt", "UniverseAI")
        assert agent.read_file("hello.txt") == "UniverseAI"
