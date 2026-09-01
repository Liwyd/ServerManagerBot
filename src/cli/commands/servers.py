import asyncio

import click

from src.cli import (
    console, async_command, get_hetzner, print_table, print_panel,
    confirm_action,
)


@click.command("list")
@click.option("--client", "-c", type=int, default=None, help="Client ID")
@click.option("--format", "-f", "fmt", type=click.Choice(["table", "ids"]), default="table")
@async_command
async def list_servers(client, fmt):
    """List all servers."""
    hetzner = await get_hetzner(client)
    servers = await hetzner.get_servers()
    if not servers:
        console.print("[yellow]No servers found.[/yellow]")
        return

    if fmt == "ids":
        for s in servers:
            console.print(f"{s.id}")
        return

    rows = []
    for s in servers:
        ip = s.public_net.ipv4.ip if s.public_net.ipv4 else "—"
        rows.append([
            str(s.id),
            s.name,
            s.status,
            ip,
            s.server_type.name,
            s.datacenter.location.city if s.datacenter else "—",
            s.created.strftime("%Y-%m-%d"),
        ])
    print_table("Servers", ["ID", "Name", "Status", "IPv4", "Type", "Location", "Created"], rows, expand=True)


@click.command("get")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_servers(server_id, client):
    """Get detailed server info."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    ip4 = server.public_net.ipv4.ip if server.public_net.ipv4 else "—"
    ip6 = server.public_net.ipv6.ip if server.public_net.ipv6 else "—"
    dc = server.datacenter.location.city if server.datacenter else "—"
    ingoing = round((server.ingoing_traffic or 0) / 1024**3, 3)
    outgoing = round((server.outgoing_traffic or 0) / 1024**3, 3)

    content = (
        f"[bold]Name:[/bold] {server.name}\n"
        f"[bold]ID:[/bold] {server.id}\n"
        f"[bold]Status:[/bold] {server.status}\n"
        f"[bold]Type:[/bold] {server.server_type.name} ({server.server_type.cores} cores, {server.server_type.memory}GB RAM, {server.server_type.disk}GB disk)\n"
        f"[bold]IPv4:[/bold] {ip4}\n"
        f"[bold]IPv6:[/bold] {ip6}\n"
        f"[bold]Image:[/bold] {server.image.name or server.image.description}\n"
        f"[bold]Datacenter:[/bold] {dc}\n"
        f"[bold]Created:[/bold] {server.created.strftime('%Y-%m-%d %H:%M')}\n"
        f"[bold]Traffic:[/bold] ↓{ingoing}GB ↑{outgoing}GB\n"
    )
    print_panel(f"Server {server.id}", content)


@click.command("create")
@click.option("--name", "-n", required=True, help="Server name")
@click.option("--type", "-t", "server_type", required=True, help="Server type (e.g., cx22)")
@click.option("--image", "-i", required=True, help="Image name or ID")
@click.option("--location", "-l", default=None, help="Location (e.g., fsn1)")
@click.option("--ssh-key", "-k", multiple=True, help="SSH key names or IDs")
@click.option("--client", "-c", type=int, default=None)
@click.option("--start-after-create/--no-start", default=True)
@async_command
async def create_servers(name, server_type, image, location, ssh_key, client, start_after_create):
    """Create a new server."""
    hetzner = await get_hetzner(client)

    kwargs = {
        "name": name,
        "server_type": server_type,
        "image": image,
        "start_after_create": start_after_create,
    }
    if location:
        kwargs["location"] = location
    if ssh_key:
        kwargs["ssh_keys"] = list(ssh_key)

    with console.status("[bold green]Creating server..."):
        result = await hetzner.create_server(**kwargs)

    console.print(f"[green]Server created: {result.server.name} (ID: {result.server.id})[/green]")


@click.command("delete")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@async_command
async def delete_servers(server_id, client, yes):
    """Delete a server."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete server '{server.name}' ({server.id})? This cannot be undone."):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting server..."):
        await hetzner.delete_server(server)
    console.print(f"[green]Server {server.name} deleted.[/green]")


@click.command("power-on")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def power_on_servers(server_id, client):
    """Power on a server."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return
    with console.status("[bold green]Powering on..."):
        await hetzner.power_on_server(server)
    console.print(f"[green]Server {server.name} powered on.[/green]")


@click.command("power-off")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def power_off_servers(server_id, client):
    """Power off a server."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return
    with console.status("[bold yellow]Powering off..."):
        await hetzner.power_off_server(server)
    console.print(f"[green]Server {server.name} powered off.[/green]")


@click.command("reboot")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def reboot_servers(server_id, client):
    """Reboot a server."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return
    with console.status("[bold yellow]Rebooting..."):
        await hetzner.reboot_server(server)
    console.print(f"[green]Server {server.name} rebooted.[/green]")


@click.command("reset")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def reset_servers(server_id, client):
    """Reset a server (power cycle)."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return
    with console.status("[bold yellow]Resetting..."):
        await hetzner.reset_server(server)
    console.print(f"[green]Server {server.name} reset.[/green]")


@click.command("rebuild")
@click.argument("server_id", type=int)
@click.option("--image", "-i", required=True, help="Image to rebuild with")
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@async_command
async def rebuild_servers(server_id, image, client, yes):
    """Rebuild a server with a new image."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Rebuild server '{server.name}' with image '{image}'? All data will be lost."):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold yellow]Rebuilding..."):
        await hetzner.rebuild_server(server, image=image)
    console.print(f"[green]Server {server.name} rebuilt with {image}.[/green]")


@click.command("rename")
@click.argument("server_id", type=int)
@click.option("--name", "-n", required=True, help="New name")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_servers(server_id, name, client):
    """Rename a server."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_server(server, name=name)
    console.print(f"[green]Server renamed to {name}.[/green]")


@click.command("reset-password")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def reset_password_servers(server_id, client):
    """Reset root password for a server."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return
    with console.status("[bold yellow]Resetting password..."):
        result = await hetzner.reset_server_password(server)
    console.print(f"[green]New password: {result.root_password}[/green]")


@click.command("upgrade")
@click.argument("server_id", type=int)
@click.option("--type", "-t", "server_type", required=True, help="New server type")
@click.option("--upgrade-disk/--no-upgrade-disk", default=False)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def upgrade_servers(server_id, server_type, upgrade_disk, client, yes):
    """Upgrade server type."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Upgrade server '{server.name}' from {server.server_type.name} to {server_type}?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold green]Upgrading..."):
        await hetzner.change_server_type(server, server_type=server_type, upgrade_disk=upgrade_disk)
    console.print(f"[green]Server upgraded to {server_type}.[/green]")


@click.command("snapshots")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def snapshots_servers(server_id, client):
    """List snapshots for a server."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    images = await hetzner.get_images(type="snapshot")
    snapshots = [img for img in images if img.created_from and img.created_from.id == server.id]

    if not snapshots:
        console.print("[yellow]No snapshots found for this server.[/yellow]")
        return

    rows = []
    for s in snapshots:
        rows.append([str(s.id), s.name or "—", s.status, s.created.strftime("%Y-%m-%d")])
    print_table(f"Snapshots for {server.name}", ["ID", "Name", "Status", "Created"], rows)


@click.command("console")
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def console_servers(server_id, client):
    """Request VNC console for a server."""
    hetzner = await get_hetzner(client)
    server = await hetzner.get_server_by_id(server_id)
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return
    with console.status("[bold green]Requesting console..."):
        result = await hetzner.request_server_console(server)
    print_panel("VNC Console", f"[bold]{result.wss_url}[/bold]")
