import asyncio

import click

from src.cli import (
    console,
    async_command,
    get_hetzner,
    print_table,
    print_panel,
    confirm_action,
)


@click.command("list")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def list_snapshots(client):
    """List all snapshots."""
    hetzner = await get_hetzner(client)
    images = await hetzner.get_images(type="snapshot")
    if not images:
        console.print("[yellow]No snapshots found.[/yellow]")
        return

    rows = []
    for s in images:
        created_from = s.created_from.name if s.created_from else "—"
        rows.append(
            [
                str(s.id),
                s.name or "—",
                s.status,
                created_from,
                s.created.strftime("%Y-%m-%d"),
            ]
        )
    print_table("Snapshots", ["ID", "Name", "Status", "Created From", "Created"], rows)


@click.command("get")
@click.argument("snapshot_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_snapshots(snapshot_id, client):
    """Get detailed snapshot info."""
    hetzner = await get_hetzner(client)
    snap = await hetzner.get_image_by_id(snapshot_id)
    if not snap:
        console.print(f"[red]Snapshot {snapshot_id} not found[/red]")
        return

    created_from = snap.created_from.name if snap.created_from else "—"
    content = (
        f"[bold]Name:[/bold] {snap.name or '—'}\n"
        f"[bold]ID:[/bold] {snap.id}\n"
        f"[bold]Status:[/bold] {snap.status}\n"
        f"[bold]Created From:[/bold] {created_from}\n"
        f"[bold]Description:[/bold] {snap.description or '—'}\n"
        f"[bold]Size:[/bold] {snap.image_size or '—'}GB\n"
        f"[bold]Created:[/bold] {snap.created.strftime('%Y-%m-%d %H:%M')}\n"
    )
    print_panel(f"Snapshot {snap.id}", content)


@click.command("delete")
@click.argument("snapshot_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_snapshots(snapshot_id, client, yes):
    """Delete a snapshot."""
    hetzner = await get_hetzner(client)
    snap = await hetzner.get_image_by_id(snapshot_id)
    if not snap:
        console.print(f"[red]Snapshot {snapshot_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete snapshot '{snap.name}' ({snap.id})? This cannot be undone."):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting snapshot..."):
        await hetzner.delete_image(snap)
    console.print(f"[green]Snapshot {snap.name or snap.id} deleted.[/green]")


@click.command("rename")
@click.argument("snapshot_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_snapshots(snapshot_id, name, client):
    """Rename a snapshot."""
    hetzner = await get_hetzner(client)
    snap = await hetzner.get_image_by_id(snapshot_id)
    if not snap:
        console.print(f"[red]Snapshot {snapshot_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_image(snap, name=name)
    console.print(f"[green]Snapshot renamed to {name}.[/green]")
