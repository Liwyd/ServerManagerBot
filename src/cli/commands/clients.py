import asyncio

import click

from src.cli import (
    console,
    async_command,
    print_table,
    print_panel,
    confirm_action,
)
from src.config import SQLALCHEMY_DATABASE_URL
from src.db.core import AsyncSessionLocal
from src.db import Client


@click.command("list")
@async_command
async def list_clients():
    """List all registered clients."""
    async with AsyncSessionLocal() as db:
        clients = await Client.get_all(db)

    if not clients:
        console.print("[yellow]No clients found.[/yellow]")
        return

    rows = []
    for c in clients:
        token_display = c.secret[:8] + "..." + c.secret[-4:] if len(c.secret) > 12 else "****"
        rows.append([str(c.id), c.remark, token_display, c.created.strftime("%Y-%m-%d")])
    print_table("Clients", ["ID", "Remark", "Token", "Created"], rows)


@click.command("get")
@click.argument("client_id", type=int)
@async_command
async def get_clients(client_id):
    """Get detailed client info."""
    async with AsyncSessionLocal() as db:
        client = await Client.get_by_id(db, client_id)

    if not client:
        console.print(f"[red]Client {client_id} not found[/red]")
        return

    content = (
        f"[bold]ID:[/bold] {client.id}\n"
        f"[bold]Remark:[/bold] {client.remark}\n"
        f"[bold]Token:[/bold] {client.secret[:8]}...{client.secret[-4:]}\n"
        f"[bold]Created:[/bold] {client.created.strftime('%Y-%m-%d %H:%M')}\n"
        f"[bold]Updated:[/bold] {client.updated_at.strftime('%Y-%m-%d %H:%M')}\n"
    )
    print_panel(f"Client {client.id}", content)


@click.command("add")
@click.option("--remark", "-r", required=True, help="Client name/remark")
@click.option("--token", "-t", required=True, help="Hetzner API token")
@async_command
async def add_clients(remark, token):
    """Add a new client."""
    async with AsyncSessionLocal() as db:
        existing = await Client.get_by_remark(db, remark)
        if existing:
            console.print(f"[red]Client with remark '{remark}' already exists.[/red]")
            return

        client = await Client.create(db, remark=remark, secret=token)
        await db.commit()
        console.print(f"[green]Client added: {client.remark} (ID: {client.id})[/green]")


@click.command("delete")
@click.argument("client_id", type=int)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_clients(client_id, yes):
    """Delete a client."""
    async with AsyncSessionLocal() as db:
        client = await Client.get_by_id(db, client_id)
        if not client:
            console.print(f"[red]Client {client_id} not found[/red]")
            return

        if not yes:
            if not confirm_action(f"Delete client '{client.remark}' ({client.id})?"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        await Client.remove(db, client.id)
        await db.commit()
        console.print(f"[green]Client {client.remark} deleted.[/green]")


@click.command("rename")
@click.argument("client_id", type=int)
@click.option("--name", "-n", required=True, help="New remark")
@async_command
async def rename_clients(client_id, name):
    """Rename a client."""
    async with AsyncSessionLocal() as db:
        client = await Client.get_by_id(db, client_id)
        if not client:
            console.print(f"[red]Client {client_id} not found[/red]")
            return

        await Client.update(db, client.id, remark=name)
        await db.commit()
        console.print(f"[green]Client renamed to {name}.[/green]")


@click.command("change-token")
@click.argument("client_id", type=int)
@click.option("--token", "-t", required=True, help="New Hetzner API token")
@async_command
async def change_token_clients(client_id, token):
    """Change a client's API token."""
    async with AsyncSessionLocal() as db:
        client = await Client.get_by_id(db, client_id)
        if not client:
            console.print(f"[red]Client {client_id} not found[/red]")
            return

        await Client.update(db, client.id, secret=token)
        await db.commit()
        console.print(f"[green]Token updated for {client.remark}.[/green]")


@click.command("test")
@click.argument("client_id", type=int)
@async_command
async def test_clients(client_id):
    """Test a client's Hetzner API connection."""
    from src.utils.async_hetzner import AsyncHetznerClient

    async with AsyncSessionLocal() as db:
        client = await Client.get_by_id(db, client_id)
        if not client:
            console.print(f"[red]Client {client_id} not found[/red]")
            return

    hetzner = AsyncHetznerClient(client.secret)
    try:
        servers = await hetzner.get_servers()
        ips = await hetzner.get_primary_ips()
        console.print(f"[green]Connection OK for {client.remark}[/green]")
        console.print(f"  Servers: {len(servers)} | Primary IPs: {len(ips)}")
    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")
