import asyncio

import click

from src.cli import (
    console, async_command, get_hetzner, print_table, print_panel,
    confirm_action,
)


@click.command("list")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def list_firewalls(client):
    """List all firewalls."""
    hetzner = await get_hetzner(client)
    fws = await hetzner.get_firewalls()
    if not fws:
        console.print("[yellow]No firewalls found.[/yellow]")
        return

    rows = []
    for fw in fws:
        rows.append([
            str(fw.id), fw.name, str(len(fw.rules)) if fw.rules else "0",
            fw.created.strftime("%Y-%m-%d"),
        ])
    print_table("Firewalls", ["ID", "Name", "Rules", "Created"], rows)


@click.command("get")
@click.argument("firewall_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_firewalls(firewall_id, client):
    """Get detailed firewall info."""
    hetzner = await get_hetzner(client)
    fw = await hetzner.get_firewall_by_id(firewall_id)
    if not fw:
        console.print(f"[red]Firewall {firewall_id} not found[/red]")
        return

    rules_str = ""
    if fw.rules:
        for r in fw.rules:
            direction = r.direction
            protocol = r.protocol
            port = r.port or "any"
            source = r.source_ips or "—"
            rules_str += f"  • {direction} | {protocol} | port {port} | src: {source}\n"

    applied = ""
    if fw.applied_to:
        for a in fw.applied_to:
            applied += f"  • {a.type}: {a.server.name if hasattr(a, 'server') and a.server else a.id}\n"

    content = (
        f"[bold]Name:[/bold] {fw.name}\n"
        f"[bold]ID:[/bold] {fw.id}\n"
        f"[bold]Created:[/bold] {fw.created.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"[bold]Rules:[/bold]\n{rules_str or '  —\n'}\n"
        f"[bold]Applied To:[/bold]\n{applied or '  —\n'}"
    )
    print_panel(f"Firewall {fw.id}", content)


@click.command("create")
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_firewalls(name, client):
    """Create a new firewall."""
    hetzner = await get_hetzner(client)
    with console.status("[bold green]Creating firewall..."):
        result = await hetzner.create_firewall(name=name)
    console.print(f"[green]Firewall created: {result.firewall.name} (ID: {result.firewall.id})[/green]")


@click.command("delete")
@click.argument("firewall_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_firewalls(firewall_id, client, yes):
    """Delete a firewall."""
    hetzner = await get_hetzner(client)
    fw = await hetzner.get_firewall_by_id(firewall_id)
    if not fw:
        console.print(f"[red]Firewall {firewall_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete firewall '{fw.name}' ({fw.id})?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting firewall..."):
        await hetzner.delete_firewall(fw)
    console.print(f"[green]Firewall {fw.name} deleted.[/green]")


@click.command("rename")
@click.argument("firewall_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_firewalls(firewall_id, name, client):
    """Rename a firewall."""
    hetzner = await get_hetzner(client)
    fw = await hetzner.get_firewall_by_id(firewall_id)
    if not fw:
        console.print(f"[red]Firewall {firewall_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_firewall(fw, name=name)
    console.print(f"[green]Firewall renamed to {name}.[/green]")


@click.command("apply")
@click.argument("firewall_id", type=int)
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def apply_firewalls(firewall_id, server_id, client):
    """Apply a firewall to a server."""
    hetzner = await get_hetzner(client)
    fw = await hetzner.get_firewall_by_id(firewall_id)
    server = await hetzner.get_server_by_id(server_id)
    if not fw:
        console.print(f"[red]Firewall {firewall_id} not found[/red]")
        return
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    with console.status("[bold green]Applying firewall..."):
        await hetzner.apply_firewall_to_resources(fw, [{"type": "server", "server": {"id": server_id}}])
    console.print(f"[green]Firewall {fw.name} applied to {server.name}.[/green]")


@click.command("remove")
@click.argument("firewall_id", type=int)
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def remove_firewalls(firewall_id, server_id, client, yes):
    """Remove a firewall from a server."""
    hetzner = await get_hetzner(client)
    fw = await hetzner.get_firewall_by_id(firewall_id)
    server = await hetzner.get_server_by_id(server_id)
    if not fw:
        console.print(f"[red]Firewall {firewall_id} not found[/red]")
        return
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Remove firewall '{fw.name}' from {server.name}?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold yellow]Removing firewall..."):
        await hetzner.remove_firewall_from_resources(fw, [{"type": "server", "server": {"id": server_id}}])
    console.print(f"[green]Firewall {fw.name} removed from {server.name}.[/green]")
