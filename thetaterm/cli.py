import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import typer
from dotenv import load_dotenv
from rich.console import Console

from thetaterm.agent import SHELL, Agent, outside

# Per-user config only: a .env in the working directory could be a cloned repo's,
# and would get to pick the endpoint our API key is sent to.
CONFIG = (
    Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config") / "thetaterm" / ".env"
)
load_dotenv(CONFIG)

app = typer.Typer()
console = Console()

DEFAULT_MODEL = "gemma4:e4b"
DEFAULT_BASE_URL = "http://localhost:11434/v1"  # Ollama
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def process_query(agent: Agent, query: str, yes: bool) -> int:
    """Generate a command for the query, confirm it, run it. Returns its exit code."""
    with console.status("thinking…"):
        try:
            command = agent.generate(query)
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
            return 1

    console.print(f"[cyan]$ {command}[/cyan]")
    reason = outside(command)
    if reason:
        # never auto-run these, even with -y, and default to no
        console.print(f"[red]leaves the current directory: {reason}[/red]")
    if (reason or not yes) and not typer.confirm("Run it?", default=not reason):
        return 0
    return subprocess.run(command, shell=True, executable=SHELL, check=False).returncode


@app.command()
def tterm(
    query: Annotated[str | None, typer.Option("--query", "-q")] = None,
    model: Annotated[
        str, typer.Option("--model", "-m", envvar="THETATERM_MODEL")
    ] = DEFAULT_MODEL,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Run without asking")
    ] = False,
    think: Annotated[
        bool, typer.Option("--think", help="Let the model reason first: slower")
    ] = False,
):
    """
    Thetaterm supercharges your terminal with AI
    """
    base_url = os.getenv("THETATERM_BASE_URL") or DEFAULT_BASE_URL
    api_key = os.getenv("THETATERM_API_KEY")
    url = urlsplit(base_url)
    if api_key and url.scheme == "http" and url.hostname not in LOCAL_HOSTS:
        console.print(
            f"[yellow]warning: API key sent unencrypted to {base_url}[/yellow]"
        )
    agent = Agent(model, base_url, api_key, think)
    if query is not None:
        sys.exit(process_query(agent, query, yes))

    console.print(f"[bold cyan]Thetaterm[/bold cyan] · {model} · {agent.env}")
    console.print("[dim]Describe what you want. Ctrl-D to exit.[/dim]")
    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return
        if line:
            process_query(agent, line, yes)


if __name__ == "__main__":
    app()
