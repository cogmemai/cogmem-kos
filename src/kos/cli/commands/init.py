"""Init command to create database tables and indices."""

import asyncio

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="Initialize database tables and search indices")
console = Console()


async def _init_postgres(force: bool = False) -> bool:
    """Initialize Postgres tables."""
    from kos.kernel.config.settings import get_settings
    from kos.providers.postgres import PostgresConnection

    settings = get_settings()
    conn = PostgresConnection(dsn=settings.postgres_dsn)

    try:
        if force:
            await conn.drop_tables()
        await conn.create_tables()
        return True
    except Exception as e:
        console.print(f"[red]Postgres error: {e}[/red]")
        return False
    finally:
        await conn.close()


async def _init_opensearch(force: bool = False) -> bool:
    """Initialize OpenSearch indices."""
    from kos.kernel.config.settings import get_settings
    from kos.providers.opensearch import OpenSearchClient

    settings = get_settings()
    client = OpenSearchClient(
        url=settings.opensearch_url,
        user=settings.opensearch_user,
        password=settings.opensearch_password,
        verify_certs=settings.opensearch_verify_certs,
    )

    try:
        await client.create_index(force=force)
        return True
    except Exception as e:
        console.print(f"[red]OpenSearch error: {e}[/red]")
        return False
    finally:
        await client.close()


async def _init_surrealdb(force: bool = False) -> bool:
    """Initialize SurrealDB schema for solo mode."""
    from kos.kernel.config.settings import get_settings
    from kos.providers.surrealdb import SurrealDBClient

    settings = get_settings()
    client = SurrealDBClient(
        url=settings.surrealdb_url,
        namespace=settings.surrealdb_namespace,
        database=settings.surrealdb_database,
        user=settings.surrealdb_user,
        password=settings.surrealdb_password,
    )

    try:
        await client.connect()
        await client.create_schema()
        return True
    except Exception as e:
        console.print(f"[red]SurrealDB error: {e}[/red]")
        return False
    finally:
        await client.close()


@app.callback(invoke_without_command=True)
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Drop existing tables/indices and recreate",
    ),
    mode: str = typer.Option(
        None,
        "--mode",
        "-m",
        help="Mode: 'enterprise' or 'solo' (auto-detected from KOS_MODE if not set)",
    ),
):
    """Initialize database tables and search indices.

    In enterprise mode: Creates tables in Postgres and indices in OpenSearch.
    In solo mode: Creates schema in SurrealDB.
    
    Use --force to drop and recreate existing structures.
    """
    from kos.kernel.config.settings import get_settings, KosMode

    settings = get_settings()
    
    if mode:
        current_mode = KosMode(mode)
    else:
        current_mode = settings.kos_mode

    console.print(f"[bold]Initializing cogmem-kos ({current_mode.value} mode)...[/bold]\n")

    if force:
        console.print("[yellow]Warning: --force will drop existing data![/yellow]\n")

    async def run_init():
        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if current_mode == KosMode.ENTERPRISE:
                task = progress.add_task("Initializing Postgres...", total=1)
                results["postgres"] = await _init_postgres(force=force)
                progress.update(task, completed=1)

                task = progress.add_task("Initializing OpenSearch...", total=1)
                results["opensearch"] = await _init_opensearch(force=force)
                progress.update(task, completed=1)
            else:
                task = progress.add_task("Initializing SurrealDB...", total=1)
                results["surrealdb"] = await _init_surrealdb(force=force)
                progress.update(task, completed=1)

        return results

    results = asyncio.run(run_init())

    console.print()
    for provider, success in results.items():
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"  {status} {provider.capitalize()}")

    if all(results.values()):
        console.print("\n[green]Initialization complete![/green]")
    else:
        console.print("\n[red]Initialization completed with errors.[/red]")
        raise typer.Exit(1)
