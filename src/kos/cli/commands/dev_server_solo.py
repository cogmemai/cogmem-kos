"""Dev server command for solo mode with embedded SurrealDB."""

import os

import typer
from rich.console import Console

console = Console()


def dev_server_solo(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Enable auto-reload"),
    db_path: str = typer.Option(
        "./cogmem.db", "--db-path", "-d", help="Path to SurrealDB file (use 'memory' for in-memory)"
    ),
):
    """Start the development API server with embedded SurrealDB (solo mode).

    Uses the SurrealDB Python SDK's embedded mode - no external server needed.
    Data is stored in a local file (or in-memory if --db-path memory).
    """
    if db_path == "memory":
        surreal_url = "mem://"
        storage_desc = "in-memory (data lost on restart)"
    else:
        surreal_url = f"surrealkv:{db_path}"
        storage_desc = f"surrealkv:{db_path}"

    os.environ["KOS_MODE"] = "solo"
    os.environ["SURREALDB_URL"] = surreal_url
    os.environ.setdefault("SURREALDB_NAMESPACE", "cogmem")
    os.environ.setdefault("SURREALDB_DATABASE", "kos")

    console.print("[bold cyan]Starting KOS Solo Mode (Embedded)[/bold cyan]\n")
    console.print(f"  SurrealDB: {storage_desc}")
    console.print(f"  API Server: {host}:{port}")
    console.print()

    try:
        from surrealdb import Surreal
        console.print("[green]✓ SurrealDB SDK available[/green]")
    except ImportError:
        console.print("[red]Error: surrealdb not installed.[/red]")
        console.print('Install with: pip install "cogmem-kos[solo]"')
        raise typer.Exit(1)

    try:
        import uvicorn

        console.print("[dim]Starting API server...[/dim]")
        console.print("[green]✓ API server starting[/green]\n")

        uvicorn.run(
            "kos.kernel.api.http.main:app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        console.print("[red]Error: uvicorn not installed.[/red]")
        console.print('Install with: pip install "cogmem-kos[api]"')
        raise typer.Exit(1)
