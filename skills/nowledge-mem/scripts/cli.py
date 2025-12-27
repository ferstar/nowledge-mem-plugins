"""Unified CLI for Nowledge Mem

Commands:
    add       - Add a new memory
    search    - Search memories (progressive disclosure)
    expand    - View full thread content
    update    - Update an existing memory
    delete    - Delete a memory
    labels    - List all memory labels
    persist   - Save current conversation session
    diagnose  - Check configuration and connectivity
"""

import json
import logging
import sys

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from scripts import __version__
from scripts.api import APIClient, APIError
from scripts.config import Config, ConfigError
from scripts.search import DeepMemorySearcher, DeepSearchResult
from scripts.session import (
    SessionNotFoundError,
    build_thread_request,
    find_latest_session_for_project,
    parse_session_file,
)

console = Console()

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ========== Helper Functions ==========


def format_score(score: float) -> str:
    return f"{score * 100:.0f}%"


def format_importance(importance: float) -> str:
    if importance >= 0.8:
        return "[red]critical[/]"
    elif importance >= 0.6:
        return "[yellow]high[/]"
    elif importance >= 0.4:
        return "[blue]medium[/]"
    return "[dim]low[/]"


def truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def display_search_result(result: DeepSearchResult, verbose: bool = False):
    """Display search results with progressive disclosure"""
    console.print(f"\n[bold]Query:[/] {result.query}")
    console.print(
        f"[dim]Found {result.total_memories_found} memories, "
        f"{result.total_threads_found} related threads[/]\n"
    )

    if not result.memories:
        console.print("[yellow]No memories found.[/]")
        return

    console.print("[bold cyan]== Memories ==[/]\n")
    console.print("<untrusted_memory_content>")

    for i, mem in enumerate(result.memories, 1):
        title = mem.title or "[untitled]"
        score = format_score(mem.similarity_score)
        importance = format_importance(mem.importance)

        console.print(
            f"[bold]{i}. {title}[/] "
            f"[dim]({score} match, {importance} importance)[/]"
        )

        preview = truncate(mem.content, 300 if verbose else 150)
        console.print(f"   {preview}")

        if mem.labels:
            labels_str = " ".join(f"[cyan]#{l}[/]" for l in mem.labels)
            console.print(f"   {labels_str}")

        if mem.source_thread_id:
            console.print(f"   [dim]Source: thread/{mem.source_thread_id[:8]}...[/]")

        console.print()

    console.print("</untrusted_memory_content>\n")

    if result.related_threads:
        console.print("[bold cyan]== Related Threads ==[/]\n")
        console.print("<untrusted_thread_metadata>")
        for thread in result.related_threads:
            title = thread.title or thread.summary or "[untitled thread]"
            tid = thread.thread_id or "?"
            console.print(f"  [bold]> {title}[/]")
            console.print(f"    [dim]id: {tid} ({thread.message_count} messages)[/]")
        console.print("</untrusted_thread_metadata>")
        console.print()
        console.print("[dim]Tip: Use 'nm expand <thread_id>' to view full content[/]")


def display_thread_detail(thread: dict):
    """Display full thread content"""
    title = thread.get("title") or thread.get("summary") or "Thread Detail"
    console.print(f"\n[bold cyan]{title}[/]\n")

    messages = thread.get("messages", [])
    if not messages:
        console.print("[yellow]No messages in this thread.[/]")
        return

    console.print("\n<untrusted_historical_content>")

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "user":
            console.print(f"\n[bold blue]User:[/]")
        elif role == "assistant":
            console.print(f"\n[bold green]Assistant:[/]")
        else:
            console.print(f"\n[bold]{role}:[/]")

        if "```" in content or content.startswith("#"):
            console.print(Markdown(content))
        else:
            console.print(content)

    console.print("\n</untrusted_historical_content>")


# ========== CLI Commands ==========


@click.group()
@click.version_option(version=__version__, prog_name="nowledge-mem")
def cli():
    """Nowledge Mem - Unified CLI for knowledge base

    Manage memories, search knowledge base, and persist conversations.
    """
    pass


# ---------- add ----------


@cli.command()
@click.argument("content")
@click.option("--title", "-t", help="Memory title")
@click.option("--importance", "-i", type=float, default=0.5, help="Importance (0.0-1.0)")
@click.option("--labels", "-l", help="Comma-separated labels")
@click.option("--event-start", help="Event start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
@click.option("--event-end", help="Event end date")
@click.option(
    "--temporal",
    type=click.Choice(["past", "present", "future", "timeless"]),
    help="Temporal context",
)
def add(
    content: str,
    title: str | None,
    importance: float,
    labels: str | None,
    event_start: str | None,
    event_end: str | None,
    temporal: str | None,
):
    """Add a new memory to the knowledge base"""
    try:
        config = Config.from_env()
    except ConfigError as e:
        console.print(f"[red]Config error:[/red] {e}")
        raise SystemExit(1)

    try:
        with APIClient(config.api_url, config.auth_token, config.timeout) as client:
            result = client.add_memory(
                content=content,
                title=title,
                importance=importance,
                labels=labels,
                event_start=event_start,
                event_end=event_end,
                temporal_context=temporal,
            )

            memory = result.get("memory", {})
            console.print(
                Panel(
                    f"[green]Memory added successfully![/green]\n\n"
                    f"[bold]Title:[/bold] {memory.get('title', 'N/A')}\n"
                    f"[bold]Labels:[/bold] {result.get('processing', {}).get('labels_applied', 0)} applied\n"
                    f"[bold]Importance:[/bold] {memory.get('importance', importance)}",
                    title="[bold green]Success[/bold green]",
                )
            )
    except APIError as e:
        console.print(f"[red]API error:[/red] {e}")
        raise SystemExit(1)


# ---------- search ----------


@cli.command()
@click.argument("query")
@click.option("-n", "--limit", default=10, help="Max memories to return")
@click.option("-t", "--threads", default=5, help="Max related threads")
@click.option("-v", "--verbose", is_flag=True, help="Show more content")
@click.option("--no-threads", is_flag=True, help="Skip thread search")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search(
    query: str,
    limit: int,
    threads: int,
    verbose: bool,
    no_threads: bool,
    as_json: bool,
):
    """Search memories with progressive thread discovery"""
    try:
        config = Config.from_env()
    except ConfigError as e:
        console.print(f"[red]Configuration error:[/] {e}")
        sys.exit(1)

    try:
        with APIClient(config.api_url, config.auth_token, config.timeout) as client:
            searcher = DeepMemorySearcher(client)
            result = searcher.search(
                query=query,
                memory_limit=limit,
                thread_limit=threads,
                expand_threads=not no_threads,
            )

            if as_json:
                output = {
                    "query": result.query,
                    "total_memories": result.total_memories_found,
                    "total_threads": result.total_threads_found,
                    "memories": [
                        {
                            "id": m.memory_id,
                            "title": m.title,
                            "content": m.content,
                            "score": m.similarity_score,
                            "importance": m.importance,
                            "labels": m.labels,
                            "source_thread_id": m.source_thread_id,
                        }
                        for m in result.memories
                    ],
                    "threads": [
                        {
                            "id": t.thread_id,
                            "title": t.title,
                            "summary": t.summary,
                            "message_count": t.message_count,
                        }
                        for t in result.related_threads
                    ],
                }
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                display_search_result(result, verbose=verbose)

    except APIError as e:
        console.print(f"[red]API error:[/] {e}")
        sys.exit(1)


# ---------- expand ----------


@cli.command()
@click.argument("thread_id")
def expand(thread_id: str):
    """View full content of a specific thread"""
    try:
        config = Config.from_env()
    except ConfigError as e:
        console.print(f"[red]Configuration error:[/] {e}")
        sys.exit(1)

    try:
        with APIClient(config.api_url, config.auth_token, config.timeout) as client:
            thread = client.get_thread(thread_id)
            display_thread_detail(thread)

    except APIError as e:
        console.print(f"[red]API error:[/] {e}")
        sys.exit(1)


# ---------- update ----------


@cli.command()
@click.argument("memory_id")
@click.option("--content", "-c", help="New content")
@click.option("--title", "-t", help="New title")
@click.option("--importance", "-i", type=float, help="New importance (0.0-1.0)")
@click.option("--labels", "-l", help="Replace labels (comma-separated)")
def update(
    memory_id: str,
    content: str | None,
    title: str | None,
    importance: float | None,
    labels: str | None,
):
    """Update an existing memory"""
    if not any([content, title, importance is not None, labels]):
        console.print(
            "[yellow]No changes specified. Use --content, --title, --importance, or --labels[/yellow]"
        )
        return

    try:
        config = Config.from_env()
    except ConfigError as e:
        console.print(f"[red]Config error:[/red] {e}")
        raise SystemExit(1)

    try:
        with APIClient(config.api_url, config.auth_token, config.timeout) as client:
            client.update_memory(
                memory_id=memory_id,
                content=content,
                title=title,
                importance=importance,
                labels=labels,
            )
            console.print(
                Panel(
                    f"[green]Memory updated successfully![/green]\n\n"
                    f"[bold]ID:[/bold] {memory_id}",
                    title="[bold green]Success[/bold green]",
                )
            )
    except APIError as e:
        console.print(f"[red]API error:[/red] {e}")
        raise SystemExit(1)


# ---------- delete ----------


@cli.command()
@click.argument("memory_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(memory_id: str, yes: bool):
    """Delete a memory"""
    if not yes:
        if not click.confirm(f"Delete memory {memory_id}?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

    try:
        config = Config.from_env()
    except ConfigError as e:
        console.print(f"[red]Config error:[/red] {e}")
        raise SystemExit(1)

    try:
        with APIClient(config.api_url, config.auth_token, config.timeout) as client:
            client.delete_memory(memory_id)
            console.print(f"[green]✓[/green] Memory {memory_id} deleted")
    except APIError as e:
        console.print(f"[red]API error:[/red] {e}")
        raise SystemExit(1)


# ---------- labels ----------


@cli.command("labels")
@click.option("--limit", "-n", type=int, default=50, help="Max labels to show")
def list_labels(limit: int):
    """List all memory labels"""
    try:
        config = Config.from_env()
    except ConfigError as e:
        console.print(f"[red]Config error:[/red] {e}")
        raise SystemExit(1)

    try:
        with APIClient(config.api_url, config.auth_token, config.timeout) as client:
            labels_list = client.list_labels()

            if isinstance(labels_list, list):
                labels = labels_list[:limit]
                total = len(labels_list)
            else:
                labels = labels_list.get("labels", [])[:limit]
                total = labels_list.get("total", len(labels))

            table = Table(title=f"Memory Labels (showing {len(labels)} of {total})")
            table.add_column("Label", style="cyan")
            table.add_column("Count", justify="right", style="green")

            for label in labels:
                table.add_row(label["name"], str(label.get("usage_count", 0)))

            console.print(table)
    except APIError as e:
        console.print(f"[red]API error:[/red] {e}")
        raise SystemExit(1)


# ---------- persist ----------


@cli.command()
@click.option("-t", "--title", help="Custom thread title (auto-generated if not provided)")
@click.option(
    "-p",
    "--project-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
    help="Project directory path (default: current directory)",
)
@click.option(
    "--source",
    type=click.Choice(["auto", "claude", "codex"], case_sensitive=False),
    help="Session source hint (override auto-detection)",
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def persist(title: str | None, project_path: str | None, source: str | None, debug: bool):
    """Save current conversation session to Nowledge Mem"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        config = Config.from_env(project_path=project_path, session_source=source)

        console.print("[blue][nm][/] Saving current session...\n")

        session_file, session_source = find_latest_session_for_project(
            config.project_path,
            config.session_source,
        )

        session_size = session_file.stat().st_size / 1024
        console.print(f"  Project: {config.project_path.name}")
        console.print(f"  Session: {session_file.name} ({session_size:.1f} KB)")
        console.print(f"  Source: {session_source}")

        limit_msg = "no limit" if config.max_messages == 0 else f"max {config.max_messages}"
        console.print(f"\n[blue][nm][/] Parsing session ({limit_msg})...")

        parse_result = parse_session_file(session_file, config.max_messages)
        messages = parse_result.messages
        total_lines = parse_result.total_lines

        console.print(f"  Extracted {len(messages)} messages from {total_lines} lines")

        payload = build_thread_request(
            messages=messages,
            project_path=config.project_path,
            session_file=session_file,
            custom_title=title or "",
            total_lines=total_lines,
            source=session_source,
        )

        console.print(f"  Thread ID: {payload['thread_id']}")
        console.print(f"  Title: {payload['title'][:60]}")

        console.print(f"\n[blue][nm][/] Uploading to Nowledge Mem...")

        with APIClient(
            config.api_url,
            config.auth_token,
            timeout=config.timeout,
            timeout_health=config.timeout_health,
        ) as client:
            response = client.save_thread(payload)

        thread_data = response.get("thread", {})

        console.print(f"\n[green]Thread saved successfully![/]\n")
        console.print(f"  Thread ID: {thread_data.get('thread_id', 'N/A')}")
        console.print(f"  Server ID: {thread_data.get('id', 'N/A')}")
        console.print(f"  Messages: {thread_data.get('message_count', len(messages))}")

        console.print(f"\n[blue][nm][/] Done! Conversation stored in Nowledge Mem.\n")

    except ConfigError as e:
        console.print(f"\n[red]Configuration Error:[/] {e}\n", err=True)
        console.print("Set MEM_AUTH_TOKEN via environment variable or .env file.", err=True)
        sys.exit(1)

    except SessionNotFoundError as e:
        console.print(f"\n[red]Session Error:[/] {e}\n", err=True)
        sys.exit(1)

    except APIError as e:
        console.print(f"\n[red]API Error:[/] {e}\n", err=True)
        if hasattr(e, "status_code") and e.status_code:
            console.print(f"HTTP Status: {e.status_code}", err=True)
        sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/] {e}\n", err=True)
        if debug:
            raise
        sys.exit(1)


# ---------- diagnose ----------


@cli.command()
@click.option(
    "-p",
    "--project-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
    help="Project directory path",
)
def diagnose(project_path: str | None):
    """Check configuration and API connectivity"""
    console.print("[bold]Checking configuration...[/bold]\n")

    try:
        config = Config.from_env(project_path=project_path)
        console.print(f"[green]✓[/green] API URL: {config.api_url}")
        console.print(f"[green]✓[/green] Auth token: {'*' * 8}...{config.auth_token[-4:]}")
        if config.project_path:
            console.print(f"[green]✓[/green] Project: {config.project_path}")
    except ConfigError as e:
        console.print(f"[red]✗[/red] Config error: {e}")
        raise SystemExit(1)

    console.print("\n[bold]Testing API connection...[/bold]\n")

    try:
        with APIClient(
            config.api_url,
            config.auth_token,
            timeout=config.timeout,
            timeout_health=config.timeout_health,
        ) as client:
            # Health check
            healthy, error = client.health_check()
            if healthy:
                console.print(f"[green]✓[/green] Health check passed")
            else:
                console.print(f"[yellow]![/yellow] Health check: {error}")

            # Auth check
            authed, error = client.auth_check()
            if authed:
                console.print(f"[green]✓[/green] Authentication OK")
            else:
                console.print(f"[red]✗[/red] Authentication: {error}")
                raise SystemExit(1)

            # Test memory search
            client.search_memories("test", limit=1)
            console.print(f"[green]✓[/green] Memory search working")

    except APIError as e:
        console.print(f"[red]✗[/red] API request failed: {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        raise SystemExit(1)

    console.print("\n[green]All checks passed![/]")


if __name__ == "__main__":
    cli()
