import asyncio

import click

from src.cli import (
    console, async_command, get_hetzner, print_table, print_panel,
    confirm_action,
)


@click.command("list")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def list_volumes(client):
    """List all volumes."""
    hetzner = await get_hetzner(client)
    vols = await hetzner.get_volumes()
    if not vols:
        console.print("[yellow]No volumes found.[/yellow]")
        return

    rows = []
    for v in vols:
        server = v.server.name if v.server else "—"
        rows.append([
            str(v.id), v.name, f"{v.size}GB", v.status, server,
            v.location.city if v.location else "—",
            v.created.strftime("%Y-%m-%d"),
        ])
    print_table("Volumes", ["ID", "Name", "Size", "Status", "Server", "Location", "Created"], rows)


@click.command("get")
@click.argument("volume_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_volumes(volume_id, client):
    """Get detailed volume info."""
    hetzner = await get_hetzner(client)
    vol = await hetzner.get_volume_by_id(volume_id)
    if not vol:
        console.print(f"[red]Volume {volume_id} not found[/red]")
        return

    server = vol.server.name if vol.server else "—"
    content = (
        f"[bold]Name:[/bold] {vol.name}\n"
        f"[bold]ID:[/bold] {vol.id}\n"
        f"[bold]Size:[/bold] {vol.size}GB\n"
        f"[bold]Status:[/bold] {vol.status}\n"
        f"[bold]Server:[/bold] {server}\n"
        f"[bold]Location:[/bold] {vol.location.city if vol.location else '—'}\n"
        f"[bold]Created:[/bold] {vol.created.strftime('%Y-%m-%d %H:%M')}\n"
    )
    print_panel(f"Volume {vol.id}", content)


@click.command("create")
@click.option("--name", "-n", required=True)
@click.option("--size", "-s", required=True, type=int, help="Size in GB")
@click.option("--location", "-l", default=None)
@click.option("--format", "-f", "format_fs", default="ext4", help="Filesystem format")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_volumes(name, size, location, format_fs, client):
    """Create a new volume."""
    hetzner = await get_hetzner(client)
    kwargs = {"name": name, "size": size}
    if location:
        kwargs["location"] = location
    if format_fs:
        kwargs["format"] = format_fs

    with console.status("[bold green]Creating volume..."):
        result = await hetzner.create_volume(**kwargs)
    console.print(f"[green]Volume created: {result.volume.name} (ID: {result.volume.id})[/green]")


@click.command("delete")
@click.argument("volume_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_volumes(volume_id, client, yes):
    """Delete a volume."""
    hetzner = await get_hetzner(client)
    vol = await hetzner.get_volume_by_id(volume_id)
    if not vol:
        console.print(f"[red]Volume {volume_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete volume '{vol.name}' ({vol.id})?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting volume..."):
        await hetzner.delete_volume(vol)
    console.print(f"[green]Volume {vol.name} deleted.[/green]")


@click.command("resize")
@click.argument("volume_id", type=int)
@click.option("--size", "-s", required=True, type=int, help="New size in GB (must be larger)")
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def resize_volumes(volume_id, size, client, yes):
    """Resize a volume (can only grow)."""
    hetzner = await get_hetzner(client)
    vol = await hetzner.get_volume_by_id(volume_id)
    if not vol:
        console.print(f"[red]Volume {volume_id} not found[/red]")
        return

    if size <= vol.size:
        console.print(f"[red]New size ({size}GB) must be larger than current ({vol.size}GB)[/red]")
        return

    if not yes:
        if not confirm_action(f"Resize volume '{vol.name}' from {vol.size}GB to {size}GB?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold green]Resizing volume..."):
        await hetzner.resize_volume(vol, size)
    console.print(f"[green]Volume resized to {size}GB.[/green]")


@click.command("attach")
@click.argument("volume_id", type=int)
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def attach_volumes(volume_id, server_id, client):
    """Attach a volume to a server."""
    hetzner = await get_hetzner(client)
    vol = await hetzner.get_volume_by_id(volume_id)
    server = await hetzner.get_server_by_id(server_id)
    if not vol:
        console.print(f"[red]Volume {volume_id} not found[/red]")
        return
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    with console.status("[bold green]Attaching volume..."):
        await hetzner.attach_volume(vol, server)
    console.print(f"[green]Volume {vol.name} attached to {server.name}.[/green]")


@click.command("detach")
@click.argument("volume_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def detach_volumes(volume_id, client, yes):
    """Detach a volume from its server."""
    hetzner = await get_hetzner(client)
    vol = await hetzner.get_volume_by_id(volume_id)
    if not vol:
        console.print(f"[red]Volume {volume_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Detach volume '{vol.name}'?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold yellow]Detaching volume..."):
        await hetzner.detach_volume(vol)
    console.print(f"[green]Volume {vol.name} detached.[/green]")


@click.command("rename")
@click.argument("volume_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_volumes(volume_id, name, client):
    """Rename a volume."""
    hetzner = await get_hetzner(client)
    vol = await hetzner.get_volume_by_id(volume_id)
    if not vol:
        console.print(f"[red]Volume {volume_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_volume(vol, name=name)
    console.print(f"[green]Volume renamed to {name}.[/green]")
