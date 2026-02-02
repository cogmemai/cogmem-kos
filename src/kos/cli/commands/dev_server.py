"""Dev server command to run the API server."""

import typer
from rich.console import Console

console = Console()


def dev_server(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Enable auto-reload"),
):
    """Start the development API server.

    Runs the FastAPI application with uvicorn.
    """
    console.print(f"[bold]Starting KOS API server on {host}:{port}...[/bold]\n")

    try:
        import uvicorn

        uvicorn.run(
            "kos.kernel.api.http.main:app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        console.print("[red]Error: uvicorn not installed.[/red]")
        console.print("Install with: pip install cogmem-kos[api]")
        raise typer.Exit(1)
