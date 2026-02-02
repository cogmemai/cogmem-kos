"""Run worker command to process events and jobs."""

import asyncio
import signal
from typing import Any

import typer
from rich.console import Console

console = Console()

_shutdown = False


def _handle_shutdown(signum: int, frame: Any) -> None:
    """Handle shutdown signals."""
    global _shutdown
    _shutdown = True
    console.print("\n[yellow]Shutting down worker...[/yellow]")


async def _run_worker_loop(
    poll_interval: float,
    batch_size: int,
) -> None:
    """Main worker loop."""
    from kos.kernel.config.settings import get_settings
    from kos.providers.postgres import PostgresConnection, PostgresOutboxStore

    settings = get_settings()
    conn = PostgresConnection(dsn=settings.postgres_dsn)
    outbox = PostgresOutboxStore(conn)

    console.print("[green]Worker started. Waiting for events...[/green]\n")

    try:
        while not _shutdown:
            events = await outbox.dequeue_events(limit=batch_size)

            if events:
                for event in events:
                    console.print(
                        f"[dim]Processing event {event.event_id[:8]}... "
                        f"type={event.event_type}[/dim]"
                    )

                    try:
                        await _process_event(event)
                        await outbox.mark_complete(event.event_id)
                        console.print(f"[green]  ✓ Completed[/green]")
                    except Exception as e:
                        await outbox.mark_failed(event.event_id, str(e))
                        console.print(f"[red]  ✗ Failed: {e}[/red]")
            else:
                await asyncio.sleep(poll_interval)
    finally:
        await conn.close()


async def _process_event(event: Any) -> None:
    """Process a single event.

    TODO: Route to appropriate agent based on event type.
    """
    from kos.core.events.event_types import EventType

    event_type = event.event_type

    if event_type == EventType.ITEM_UPSERTED.value:
        pass
    elif event_type == EventType.PASSAGES_CREATED.value:
        pass
    elif event_type == EventType.ENTITIES_EXTRACTED.value:
        pass
    else:
        console.print(f"[yellow]  Unknown event type: {event_type}[/yellow]")


def run_worker(
    poll_interval: float = typer.Option(
        1.0,
        "--poll-interval",
        "-i",
        help="Seconds between polling for events",
    ),
    batch_size: int = typer.Option(
        10,
        "--batch-size",
        "-b",
        help="Number of events to process per batch",
    ),
):
    """Start a worker to process events and jobs.

    The worker polls the outbox for events and routes them to agents.
    """
    console.print("[bold]Starting KOS worker...[/bold]\n")

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    try:
        asyncio.run(_run_worker_loop(poll_interval, batch_size))
    except KeyboardInterrupt:
        pass

    console.print("[green]Worker stopped.[/green]")
