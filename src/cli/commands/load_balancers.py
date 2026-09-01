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
async def list_load_balancers(client):
    """List all load balancers."""
    hetzner = await get_hetzner(client)
    lbs = await hetzner.get_load_balancers()
    if not lbs:
        console.print("[yellow]No load balancers found.[/yellow]")
        return

    rows = []
    for lb in lbs:
        rows.append(
            [
                str(lb.id),
                lb.name,
                lb.lb_type.name if lb.lb_type else "—",
                lb.public_net.ipv4.ip if lb.public_net and lb.public_net.ipv4 else "—",
                lb.location.city if lb.location else "—",
            ]
        )
    print_table("Load Balancers", ["ID", "Name", "Type", "IPv4", "Location"], rows)


@click.command("get")
@click.argument("lb_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_load_balancers(lb_id, client):
    """Get detailed load balancer info."""
    hetzner = await get_hetzner(client)
    lb = await hetzner.get_load_balancer_by_id(lb_id)
    if not lb:
        console.print(f"[red]Load balancer {lb_id} not found[/red]")
        return

    ip4 = lb.public_net.ipv4.ip if lb.public_net and lb.public_net.ipv4 else "—"
    content = (
        f"[bold]Name:[/bold] {lb.name}\n"
        f"[bold]ID:[/bold] {lb.id}\n"
        f"[bold]Type:[/bold] {lb.lb_type.name if lb.lb_type else '—'}\n"
        f"[bold]IPv4:[/bold] {ip4}\n"
        f"[bold]Location:[/bold] {lb.location.city if lb.location else '—'}\n"
        f"[bold]Created:[/bold] {lb.created.strftime('%Y-%m-%d %H:%M')}\n"
    )
    print_panel(f"Load Balancer {lb.id}", content)


@click.command("create")
@click.option("--name", "-n", required=True)
@click.option("--type", "-t", "lb_type", default="lb11", help="Load balancer type")
@click.option("--location", "-l", default=None)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_load_balancers(name, lb_type, location, client):
    """Create a new load balancer."""
    hetzner = await get_hetzner(client)
    kwargs = {"name": name, "lb_type": lb_type}
    if location:
        kwargs["location"] = location

    with console.status("[bold green]Creating load balancer..."):
        result = await hetzner.create_load_balancer(**kwargs)
    console.print(f"[green]Load balancer created: {result.load_balancer.name} (ID: {result.load_balancer.id})[/green]")


@click.command("delete")
@click.argument("lb_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_load_balancers(lb_id, client, yes):
    """Delete a load balancer."""
    hetzner = await get_hetzner(client)
    lb = await hetzner.get_load_balancer_by_id(lb_id)
    if not lb:
        console.print(f"[red]Load balancer {lb_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete load balancer '{lb.name}' ({lb.id})?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting load balancer..."):
        await hetzner.delete_load_balancer(lb)
    console.print(f"[green]Load balancer {lb.name} deleted.[/green]")


@click.command("rename")
@click.argument("lb_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_load_balancers(lb_id, name, client):
    """Rename a load balancer."""
    hetzner = await get_hetzner(client)
    lb = await hetzner.get_load_balancer_by_id(lb_id)
    if not lb:
        console.print(f"[red]Load balancer {lb_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_load_balancer(lb, name=name)
    console.print(f"[green]Load balancer renamed to {name}.[/green]")


@click.command("add-target")
@click.argument("lb_id", type=int)
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def add_target_load_balancers(lb_id, server_id, client):
    """Add a server as target to a load balancer."""
    hetzner = await get_hetzner(client)
    lb = await hetzner.get_load_balancer_by_id(lb_id)
    if not lb:
        console.print(f"[red]Load balancer {lb_id} not found[/red]")
        return

    with console.status("[bold green]Adding target..."):
        await hetzner.add_load_balancer_target(lb, {"type": "server", "server": {"id": server_id}})
    console.print(f"[green]Server {server_id} added as target to {lb.name}.[/green]")


@click.command("remove-target")
@click.argument("lb_id", type=int)
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def remove_target_load_balancers(lb_id, server_id, client, yes):
    """Remove a server target from a load balancer."""
    hetzner = await get_hetzner(client)
    lb = await hetzner.get_load_balancer_by_id(lb_id)
    if not lb:
        console.print(f"[red]Load balancer {lb_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Remove server {server_id} from {lb.name}?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold yellow]Removing target..."):
        await hetzner.remove_load_balancer_target(lb, {"type": "server", "server": {"id": server_id}})
    console.print(f"[green]Server {server_id} removed from {lb.name}.[/green]")
