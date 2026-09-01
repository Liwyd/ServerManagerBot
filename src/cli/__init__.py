import asyncio
import os
import sys
from functools import wraps

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.config import SQLALCHEMY_DATABASE_URL
from src.db.core import AsyncSessionLocal
from src.db import Client
from src.utils.async_hetzner import AsyncHetznerClient

console = Console()


def async_command(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        asyncio.run(f(*args, **kwargs))
    return wrapper


async def get_client_token(client_id: int | None = None) -> str:
    """Get Hetzner API token from client or env."""
    async with AsyncSessionLocal() as db:
        if client_id:
            client = await Client.get_by_id(db, client_id)
            if not client:
                console.print(f"[red]Client {client_id} not found[/red]")
                sys.exit(1)
            return client.secret

        # Try first client
        clients = await Client.get_all(db)
        if clients:
            return clients[0].secret

    token = os.environ.get("HETZNER_API_TOKEN", "")
    if not token:
        console.print("[red]No Hetzner API token found. Add a client or set HETZNER_API_TOKEN.[/red]")
        sys.exit(1)
    return token


async def get_hetzner(client_id: int | None = None) -> AsyncHetznerClient:
    """Get async Hetzner client."""
    token = await get_client_token(client_id)
    return AsyncHetznerClient(token)


def print_table(title: str, columns: list[str], rows: list[list[str]], expand: bool = False):
    """Print a rich table."""
    table = Table(title=title, show_header=True, header_style="bold cyan", expand=expand)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def print_panel(title: str, content: str, style: str = "blue"):
    """Print a rich panel."""
    panel = Panel(content, title=title, border_style=style, padding=(1, 2))
    console.print(panel)


def confirm_action(message: str) -> bool:
    """Confirm a dangerous action."""
    return click.confirm(f"[yellow]{message}[/yellow]", default=False)
