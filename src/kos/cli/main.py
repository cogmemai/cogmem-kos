"""CLI entry point for cogmem-kos."""

import typer
from rich.console import Console

from kos.cli.commands import init, run_worker, dev_server, dev_server_solo

app = typer.Typer(
    name="kos",
    help="cogmem-kos: Framework-agnostic Knowledge Operating System kernel",
    no_args_is_help=True,
)

console = Console()

app.add_typer(init.app, name="init")
app.command(name="dev-server")(dev_server.dev_server)
app.command(name="dev-server-solo")(dev_server_solo.dev_server_solo)
app.command(name="run-worker")(run_worker.run_worker)


@app.callback()
def main():
    """cogmem-kos CLI."""
    pass


if __name__ == "__main__":
    app()
