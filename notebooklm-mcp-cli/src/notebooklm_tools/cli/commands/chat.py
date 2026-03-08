"""Chat configuration CLI commands."""

from typing import Optional

import typer
from rich.console import Console

from notebooklm_tools.core.alias import get_alias_manager
from notebooklm_tools.core.exceptions import NLMError
from notebooklm_tools.cli.utils import get_client
from notebooklm_tools.services import chat as chat_service, ServiceError

console = Console()
app = typer.Typer(
    help="Configure chat settings",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@app.command("configure")
def configure_chat(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    goal: str = typer.Option(
        "default", "--goal", "-g",
        help="Chat goal: default, learning_guide, or custom",
    ),
    prompt: Optional[str] = typer.Option(
        None, "--prompt",
        help="Custom prompt (required when goal=custom, max 10000 chars)",
    ),
    response_length: str = typer.Option(
        "default", "--response-length", "-r",
        help="Response length: default, longer, or shorter",
    ),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """
    Configure how AI responds in notebook chat.
    
    Goals:
    - default: Standard helpful responses
    - learning_guide: Educational, step-by-step explanations
    - custom: Use your own prompt to guide the AI
    """
    try:
        notebook_id = get_alias_manager().resolve(notebook_id)
        with get_client(profile) as client:
            result = chat_service.configure_chat(
                client, notebook_id,
                goal=goal,
                custom_prompt=prompt,
                response_length=response_length,
            )
        
        console.print("[green]✓[/green] Chat configuration updated")
        console.print(f"  Goal: {result['goal']}")
        if prompt:
            preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
            console.print(f"  Prompt: {preview}")
        console.print(f"  Response length: {result['response_length']}")

    except ServiceError as e:
        console.print(f"[red]Error:[/red] {e.user_message}")
        raise typer.Exit(1)
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)


@app.command("start")
def start_chat(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """
    Start interactive chat session with a notebook.
    
    Enter a REPL where you can have multi-turn conversations.
    Use /help for commands, /exit to quit.
    """
    from notebooklm_tools.cli.commands.repl import run_chat_repl
    run_chat_repl(notebook_id, profile)
