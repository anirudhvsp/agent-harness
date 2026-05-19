import subprocess
import os
from typing import Any

# ── Registry ──────────────────────────────────────────────────────────────────
# Each entry: {"schema": <Anthropic tool schema>, "fn": <callable>}
_REGISTRY: dict[str, dict] = {}


def register(schema: dict):
    """Decorator that registers a function as a tool."""
    def decorator(fn):
        _REGISTRY[schema["name"]] = {"schema": schema, "fn": fn}
        return fn
    return decorator


def get_schemas() -> list[dict]:
    return [entry["schema"] for entry in _REGISTRY.values()]


def call(name: str, inputs: dict) -> Any:
    if name not in _REGISTRY:
        return f"Error: unknown tool '{name}'"
    try:
        return _REGISTRY[name]["fn"](**inputs)
    except Exception as e:
        return f"Error running tool '{name}': {e}"


# ── Built-in tools ─────────────────────────────────────────────────────────────

@register({
    "name": "run_shell",
    "description": "Run a shell command and return stdout + stderr. Use for file ops, grep, git, etc.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to run"},
        },
        "required": ["command"],
    },
})
def run_shell(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    out = result.stdout.strip()
    err = result.stderr.strip()
    if result.returncode != 0:
        return f"[exit {result.returncode}]\n{err or out}"
    return out or "(no output)"


@register({
    "name": "read_file",
    "description": "Read the contents of a file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative file path"},
        },
        "required": ["path"],
    },
})
def read_file(path: str) -> str:
    try:
        with open(os.path.expanduser(path)) as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


@register({
    "name": "write_file",
    "description": "Write content to a file (overwrites if exists).",
    "input_schema": {
        "type": "object",
        "properties": {
            "path":    {"type": "string", "description": "File path to write to"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    },
})
def write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(os.path.expanduser(path))), exist_ok=True)
        with open(os.path.expanduser(path), "w") as f:
            f.write(content)
        return f"Written {len(content)} chars to {path}"
    except Exception as e:
        return f"Error: {e}"
