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
async def list_placement_groups(client):
    """List all placement groups."""
    hetzner = await get_hetzner(client)
    pgs = await hetzner.get_placement_groups()
    if not pgs:
        console.print("[yellow]No placement groups found.[/yellow]")
        return

    rows = []
    for pg in pgs:
        rows.append([str(pg.id), pg.name, pg.type])
    print_table("Placement Groups", ["ID", "Name", "Type"], rows)


@click.command("get")
@click.argument("pg_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_placement_groups(pg_id, client):
    """Get detailed placement group info."""
    hetzner = await get_hetzner(client)
    pg = await hetzner.get_placement_group_by_id(pg_id)
    if not pg:
        console.print(f"[red]Placement group {pg_id} not found[/red]")
        return

    content = f"[bold]Name:[/bold] {pg.name}\n[bold]ID:[/bold] {pg.id}\n[bold]Type:[/bold] {pg.type}\n"
    print_panel(f"Placement Group {pg.id}", content)


@click.command("create")
@click.option("--name", "-n", required=True)
@click.option("--type", "-t", "pg_type", type=click.Choice(["spread"]), default="spread")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_placement_groups(name, pg_type, client):
    """Create a placement group."""
    hetzner = await get_hetzner(client)
    with console.status("[bold green]Creating placement group..."):
        result = await hetzner.create_placement_group(name=name, type=pg_type)
    console.print(f"[green]Placement group created: {result.placement_group.name} (ID: {result.placement_group.id})[/green]")


@click.command("delete")
@click.argument("pg_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_placement_groups(pg_id, client, yes):
    """Delete a placement group."""
    hetzner = await get_hetzner(client)
    pg = await hetzner.get_placement_group_by_id(pg_id)
    if not pg:
        console.print(f"[red]Placement group {pg_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete placement group '{pg.name}' ({pg.id})?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting placement group..."):
        await hetzner.delete_placement_group(pg)
    console.print(f"[green]Placement group {pg.name} deleted.[/green]")


@click.command("rename")
@click.argument("pg_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_placement_groups(pg_id, name, client):
    """Rename a placement group."""
    hetzner = await get_hetzner(client)
    pg = await hetzner.get_placement_group_by_id(pg_id)
    if not pg:
        console.print(f"[red]Placement group {pg_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_placement_group(pg, name=name)
    console.print(f"[green]Placement group renamed to {name}.[/green]")
