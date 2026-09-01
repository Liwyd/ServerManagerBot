import asyncio

import click

from src.cli import (
    console, async_command, get_hetzner, print_table, print_panel,
    confirm_action,
)


@click.command("list")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def list_ssh_keys(client):
    """List all SSH keys."""
    hetzner = await get_hetzner(client)
    keys = await hetzner.get_ssh_keys()
    if not keys:
        console.print("[yellow]No SSH keys found.[/yellow]")
        return

    rows = []
    for k in keys:
        fingerprint = k.fingerprint[:20] + "..." if k.fingerprint and len(k.fingerprint) > 20 else k.fingerprint
        rows.append([str(k.id), k.name, fingerprint or "—"])
    print_table("SSH Keys", ["ID", "Name", "Fingerprint"], rows)


@click.command("get")
@click.argument("key_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_ssh_keys(key_id, client):
    """Get detailed SSH key info."""
    hetzner = await get_hetzner(client)
    key = await hetzner.get_ssh_key_by_id(key_id)
    if not key:
        console.print(f"[red]SSH key {key_id} not found[/red]")
        return

    content = (
        f"[bold]Name:[/bold] {key.name}\n"
        f"[bold]ID:[/bold] {key.id}\n"
        f"[bold]Fingerprint:[/bold] {key.fingerprint}\n"
        f"[bold]Public Key:[/bold]\n{key.public_key}\n"
    )
    print_panel(f"SSH Key {key.id}", content)


@click.command("create")
@click.option("--name", "-n", required=True)
@click.option("--key", "-k", "public_key", required=True, help="Public key content or path to .pub file")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_ssh_keys(name, public_key, client):
    """Add an SSH key."""
    import os
    if os.path.isfile(public_key):
        with open(public_key) as f:
            public_key = f.read().strip()

    hetzner = await get_hetzner(client)
    with console.status("[bold green]Adding SSH key..."):
        result = await hetzner.create_ssh_key(name=name, public_key=public_key)
    console.print(f"[green]SSH key added: {result.ssh_key.name} (ID: {result.ssh_key.id})[/green]")


@click.command("delete")
@click.argument("key_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_ssh_keys(key_id, client, yes):
    """Delete an SSH key."""
    hetzner = await get_hetzner(client)
    key = await hetzner.get_ssh_key_by_id(key_id)
    if not key:
        console.print(f"[red]SSH key {key_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete SSH key '{key.name}' ({key.id})?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting SSH key..."):
        await hetzner.delete_ssh_key(key)
    console.print(f"[green]SSH key {key.name} deleted.[/green]")


@click.command("rename")
@click.argument("key_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_ssh_keys(key_id, name, client):
    """Rename an SSH key."""
    hetzner = await get_hetzner(client)
    key = await hetzner.get_ssh_key_by_id(key_id)
    if not key:
        console.print(f"[red]SSH key {key_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_ssh_key(key, name=name)
    console.print(f"[green]SSH key renamed to {name}.[/green]")
