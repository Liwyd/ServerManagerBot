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
async def list_networks(client):
    """List all networks."""
    hetzner = await get_hetzner(client)
    nets = await hetzner.get_networks()
    if not nets:
        console.print("[yellow]No networks found.[/yellow]")
        return

    rows = []
    for n in nets:
        subnets = len(n.subnets) if n.subnets else 0
        rows.append(
            [
                str(n.id),
                n.name,
                n.ip_range,
                str(subnets),
                n.created.strftime("%Y-%m-%d"),
            ]
        )
    print_table("Networks", ["ID", "Name", "IP Range", "Subnets", "Created"], rows)


@click.command("get")
@click.argument("network_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_networks(network_id, client):
    """Get detailed network info."""
    hetzner = await get_hetzner(client)
    net = await hetzner.get_network_by_id(network_id)
    if not net:
        console.print(f"[red]Network {network_id} not found[/red]")
        return

    subnets_str = ""
    if net.subnets:
        for s in net.subnets:
            subnets_str += f"  • {s.ip_range} (type={s.type}, zone={s.network_zone})\n"

    routes_str = ""
    if net.routes:
        for r in net.routes:
            routes_str += f"  • {r.destination} → {r.gateway}\n"

    content = (
        f"[bold]Name:[/bold] {net.name}\n"
        f"[bold]ID:[/bold] {net.id}\n"
        f"[bold]IP Range:[/bold] {net.ip_range}\n"
        f"[bold]Created:[/bold] {net.created.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"[bold]Subnets:[/bold]\n{subnets_str or '  —\n'}\n"
        f"[bold]Routes:[/bold]\n{routes_str or '  —\n'}"
    )
    print_panel(f"Network {net.id}", content)


@click.command("create")
@click.option("--name", "-n", required=True)
@click.option("--ip-range", "-r", required=True, help="IP range (e.g., 10.0.0.0/16)")
@click.option("--subnets", "-s", multiple=True, help="Subnets (type:ip_range:zone)")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_networks(name, ip_range, subnets, client):
    """Create a new network."""
    hetzner = await get_hetzner(client)
    kwargs = {"name": name, "ip_range": ip_range}
    if subnets:
        subnet_list = []
        for s in subnets:
            parts = s.split(":")
            if len(parts) != 3:
                console.print(f"[red]Invalid subnet format: {s}. Use type:ip_range:zone[/red]")
                return
            subnet_list.append({"type": parts[0], "ip_range": parts[1], "network_zone": parts[2]})
        kwargs["subnets"] = subnet_list

    with console.status("[bold green]Creating network..."):
        result = await hetzner.create_network(**kwargs)
    console.print(f"[green]Network created: {result.network.name} (ID: {result.network.id})[/green]")


@click.command("delete")
@click.argument("network_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_networks(network_id, client, yes):
    """Delete a network."""
    hetzner = await get_hetzner(client)
    net = await hetzner.get_network_by_id(network_id)
    if not net:
        console.print(f"[red]Network {network_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete network '{net.name}' ({net.id})?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting network..."):
        await hetzner.delete_network(net)
    console.print(f"[green]Network {net.name} deleted.[/green]")


@click.command("rename")
@click.argument("network_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_networks(network_id, name, client):
    """Rename a network."""
    hetzner = await get_hetzner(client)
    net = await hetzner.get_network_by_id(network_id)
    if not net:
        console.print(f"[red]Network {network_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_network(net, name=name)
    console.print(f"[green]Network renamed to {name}.[/green]")


@click.command("add-subnet")
@click.argument("network_id", type=int)
@click.option("--type", "-t", "subnet_type", required=True, help="Subnet type (cloud, vswitch)")
@click.option("--ip-range", "-r", required=True, help="Subnet IP range")
@click.option("--zone", "-z", required=True, help="Network zone")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def add_subnet_networks(network_id, subnet_type, ip_range, zone, client):
    """Add a subnet to a network."""
    hetzner = await get_hetzner(client)
    net = await hetzner.get_network_by_id(network_id)
    if not net:
        console.print(f"[red]Network {network_id} not found[/red]")
        return

    with console.status("[bold green]Adding subnet..."):
        await hetzner.add_subnet_to_network(net, {"type": subnet_type, "ip_range": ip_range, "network_zone": zone})
    console.print(f"[green]Subnet {ip_range} added to {net.name}.[/green]")


@click.command("remove-subnet")
@click.argument("network_id", type=int)
@click.argument("subnet_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def remove_subnet_networks(network_id, subnet_id, client, yes):
    """Remove a subnet from a network."""
    hetzner = await get_hetzner(client)
    net = await hetzner.get_network_by_id(network_id)
    if not net:
        console.print(f"[red]Network {network_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Remove subnet {subnet_id} from {net.name}?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold yellow]Removing subnet..."):
        await hetzner.delete_subnet_from_network(net, subnet_id)
    console.print(f"[green]Subnet {subnet_id} removed from {net.name}.[/green]")


@click.command("add-route")
@click.argument("network_id", type=int)
@click.option("--destination", "-d", required=True, help="Route destination (e.g., 10.100.1.0/24)")
@click.option("--gateway", "-g", required=True, help="Route gateway")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def add_route_networks(network_id, destination, gateway, client):
    """Add a route to a network."""
    hetzner = await get_hetzner(client)
    net = await hetzner.get_network_by_id(network_id)
    if not net:
        console.print(f"[red]Network {network_id} not found[/red]")
        return

    with console.status("[bold green]Adding route..."):
        await hetzner.add_route_to_network(net, {"destination": destination, "gateway": gateway})
    console.print(f"[green]Route {destination} → {gateway} added to {net.name}.[/green]")


@click.command("remove-route")
@click.argument("network_id", type=int)
@click.argument("route_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def remove_route_networks(network_id, route_id, client, yes):
    """Remove a route from a network."""
    hetzner = await get_hetzner(client)
    net = await hetzner.get_network_by_id(network_id)
    if not net:
        console.print(f"[red]Network {network_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Remove route {route_id} from {net.name}?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold yellow]Removing route..."):
        await hetzner.delete_route_from_network(net, route_id)
    console.print(f"[green]Route {route_id} removed from {net.name}.[/green]")
