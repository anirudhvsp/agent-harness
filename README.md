# agent-harness

A minimal but extensible AI agent CLI built on a supported API.

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and set your API_KEY

# 3. Run
python main.py                  # interactive REPL
python main.py "list files here" # single-shot
```

## Project structure

```
agent-harness/
├── main.py              # CLI entry point (Rich REPL + single-shot)
├── config/
│   └── settings.py      # env-based config (model, max tokens, etc.)
├── agent/
│   └── core.py          # Agent class — the think→act→observe loop
└── tools/
    └── registry.py      # Tool registry + built-in tools
```

## Adding a tool

Open `tools/registry.py` and add a decorated function:

```python
@register({
    "name": "my_tool",
    "description": "What this tool does — be specific, the model reads this.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
        },
        "required": ["query"],
    },
})
def my_tool(query: str) -> str:
    # Do the work, return a string
    return f"Result for: {query}"
```

That's it — the tool is automatically registered and available to the agent.

## REPL commands

| Command  | Effect                        |
|----------|-------------------------------|
| `/reset` | Clear conversation history    |
| `/tools` | List available tools          |
| `/exit`  | Quit                          |

## Extending

- **Memory**: persist `agent.history` to SQLite between sessions
- **Streaming**: swap `client.messages.create` for `client.messages.stream`
- **Approval**: prompt the user before `registry.call()` for destructive tools
- **More tools**: web search, code execution sandbox, vector DB lookup
