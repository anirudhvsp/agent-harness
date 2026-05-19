#!/usr/bin/env python3
"""
agent-harness — a minimal AI agent CLI
Usage:
    python main.py                  # interactive REPL
    python main.py "your prompt"    # single-shot mode
"""
import sys
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich import print as rprint

from agent.core import Agent

app = typer.Typer(add_completion=False)
console = Console()


def print_banner():
    console.print(Panel(
        "[bold]AI Agent Harness[/bold]\n"
        "[dim]Type your message, or:[/dim]\n"
        "  [cyan]/reset[/cyan]  — clear conversation\n"
        "  [cyan]/tools[/cyan]  — list available tools\n"
        "  [cyan]/exit[/cyan]   — quit",
        title="[bold cyan]agent[/bold cyan]",
        border_style="cyan",
    ))


def run_turn(agent: Agent, user_input: str):
    collected_text = []

    def on_text(chunk: str):
        collected_text.append(chunk)

    def on_tool(name: str, inputs: dict):
        args = ", ".join(f"{k}={repr(v)[:60]}" for k, v in inputs.items())
        console.print(f"\n  [yellow]⚙ tool[/yellow] [bold]{name}[/bold]({args})")

    def on_result(name: str, result: str):
        preview = result[:200].replace("\n", " ")
        console.print(f"  [dim]↳ {preview}{'…' if len(result) > 200 else ''}[/dim]")

    with console.status("[cyan]thinking…[/cyan]", spinner="dots"):
        agent.run(user_input, on_text=on_text, on_tool=on_tool, on_result=on_result)

    full_text = "".join(collected_text).strip()
    if full_text:
        console.print()
        console.print(Panel(
            Markdown(full_text),
            title="[bold green]agent[/bold green]",
            border_style="green",
        ))


def list_tools(agent: Agent):
    from tools import registry
    schemas = registry.get_schemas()
    console.print("\n[bold]Available tools:[/bold]")
    for s in schemas:
        console.print(f"  [cyan]{s['name']}[/cyan] — {s['description']}")
    console.print()


@app.command()
def main(prompt: str = typer.Argument(None, help="Single-shot prompt (omit for REPL mode)")):
    agent = Agent()

    if prompt:
        # ── Single-shot mode ──────────────────────────────────────────────
        run_turn(agent, prompt)
        return

    # ── Interactive REPL ──────────────────────────────────────────────────
    print_banner()

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]you[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye![/dim]")
            break

        if not user_input:
            continue

        if user_input == "/exit":
            console.print("[dim]Bye![/dim]")
            break
        elif user_input == "/reset":
            agent.reset()
            console.print("[dim]Conversation cleared.[/dim]")
            continue
        elif user_input == "/tools":
            list_tools(agent)
            continue

        run_turn(agent, user_input)


if __name__ == "__main__":
    app()
