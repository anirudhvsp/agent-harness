import json
from openai import OpenAI
from config import settings
from tools import registry
from memory import database

client = OpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
)


def _schemas_to_openai() -> list[dict]:
    """Convert Anthropic-style tool schemas → OpenAI function format."""
    return [
        {
            "type": "function",
            "function": {
                "name": s["name"],
                "description": s["description"],
                "parameters": s["input_schema"],
            },
        }
        for s in registry.get_schemas()
    ]


class Agent:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = database.get_messages(session_id)
        self.facts = database.get_facts()

    def reset(self):
        self.history = []
        database.clear_messages(self.session_id)

    def run(self, user_message: str, on_text=None, on_tool=None, on_result=None):
        """
        Run one user turn through the agent loop.

        Callbacks (all optional):
          on_text(text: str)         — final text from the model
          on_tool(name, inputs)      — about to execute a tool
          on_result(name, result)    — tool returned a result
        """
        if "remember:" in user_message.lower():
            fact = user_message.split("remember:")[1].strip()
            database.add_fact(fact)
            self.facts.append(fact)
            if on_text:
                on_text(f"I will remember that: {fact}")
            return

        user_turn = {"role": "user", "content": user_message}
        self.history.append(user_turn)
        database.add_message(self.session_id, user_turn)

        facts_prompt = ""
        if self.facts:
            facts_prompt = "Remember these important points:\n" + "\n".join(f"- {f}" for f in self.facts)


        for _ in range(settings.MAX_ITERS):
            response = client.chat.completions.create(
                model=settings.MODEL,
                max_tokens=settings.MAX_TOKENS,
                messages=[
                    {"role": "system", "content": settings.SYSTEM_PROMPT + "\n" + facts_prompt},
                    *self.history,
                ],
                tools=_schemas_to_openai(),
                tool_choice="auto",
            )

            msg = response.choices[0].message
            finish = response.choices[0].finish_reason

            # Append assistant turn to history (OpenAI format)
            assistant_turn = msg.model_dump(exclude_unset=True)
            self.history.append(assistant_turn)
            database.add_message(self.session_id, assistant_turn)

            # ── Final answer ───────────────────────────────────────────────
            if finish == "stop" or not msg.tool_calls:
                if on_text and msg.content:
                    on_text(msg.content)
                break

            # ── Tool calls ─────────────────────────────────────────────────
            if finish == "tool_calls" or msg.tool_calls:
                for tc in msg.tool_calls:
                    name   = tc.function.name
                    inputs = json.loads(tc.function.arguments or "{}")

                    if on_tool:
                        on_tool(name, inputs)

                    result = registry.call(name, inputs)

                    if on_result:
                        on_result(name, str(result))

                    tool_turn = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": str(result),
                    }
                    self.history.append(tool_turn)
                    database.add_message(self.session_id, tool_turn)
                # continue loop with tool results in history

        else:
            if on_text:
                on_text(f"\n[Catalyst-AI stopped after {settings.MAX_ITERS} iterations]")