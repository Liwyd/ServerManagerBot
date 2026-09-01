import asyncio

import click

from src.cli import (
    console, async_command, get_hetzner, print_table, print_panel,
    confirm_action,
)


@click.command("list")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def list_floating_ips(client):
    """List all floating IPs."""
    hetzner = await get_hetzner(client)
    ips = await hetzner.get_floating_ips()
    if not ips:
        console.print("[yellow]No floating IPs found.[/yellow]")
        return

    rows = []
    for ip in ips:
        server = ip.server.name if ip.server else "—"
        rows.append([
            str(ip.id), ip.name or "—", ip.ip, ip.type, ip.blocked,
            server, ip.home_location.city if ip.home_location else "—",
        ])
    print_table("Floating IPs", ["ID", "Name", "IP", "Type", "Blocked", "Server", "Location"], rows)


@click.command("get")
@click.argument("ip_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_floating_ips(ip_id, client):
    """Get detailed floating IP info."""
    hetzner = await get_hetzner(client)
    ip = await hetzner.get_floating_ip_by_id(ip_id)
    if not ip:
        console.print(f"[red]Floating IP {ip_id} not found[/red]")
        return

    server = ip.server.name if ip.server else "—"
    content = (
        f"[bold]Name:[/bold] {ip.name or '—'}\n"
        f"[bold]ID:[/bold] {ip.id}\n"
        f"[bold]IP:[/bold] {ip.ip}\n"
        f"[bold]Type:[/bold] {ip.type}\n"
        f"[bold]Blocked:[/bold] {ip.blocked}\n"
        f"[bold]Server:[/bold] {server}\n"
        f"[bold]Location:[/bold] {ip.home_location.city if ip.home_location else '—'}\n"
    )
    print_panel(f"Floating IP {ip.id}", content)


@click.command("create")
@click.option("--name", "-n", default=None)
@click.option("--type", "-t", "ip_type", type=click.Choice(["ipv4", "ipv6"]), default="ipv4")
@click.option("--location", "-l", default=None)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_floating_ips(name, ip_type, location, client):
    """Create a new floating IP."""
    hetzner = await get_hetzner(client)
    kwargs = {"type": ip_type}
    if name:
        kwargs["name"] = name
    if location:
        kwargs["home_location"] = location

    with console.status("[bold green]Creating floating IP..."):
        result = await hetzner.create_floating_ip(**kwargs)
    console.print(f"[green]Floating IP created: {result.floating_ip.ip} (ID: {result.floating_ip.id})[/green]")


@click.command("delete")
@click.argument("ip_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_floating_ips(ip_id, client, yes):
    """Delete a floating IP."""
    hetzner = await get_hetzner(client)
    ip = await hetzner.get_floating_ip_by_id(ip_id)
    if not ip:
        console.print(f"[red]Floating IP {ip_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete floating IP '{ip.ip}' ({ip.id})?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting floating IP..."):
        await hetzner.delete_floating_ip(ip)
    console.print(f"[green]Floating IP {ip.ip} deleted.[/green]")


@click.command("assign")
@click.argument("ip_id", type=int)
@click.argument("server_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def assign_floating_ips(ip_id, server_id, client):
    """Assign a floating IP to a server."""
    hetzner = await get_hetzner(client)
    ip = await hetzner.get_floating_ip_by_id(ip_id)
    server = await hetzner.get_server_by_id(server_id)
    if not ip:
        console.print(f"[red]Floating IP {ip_id} not found[/red]")
        return
    if not server:
        console.print(f"[red]Server {server_id} not found[/red]")
        return

    with console.status("[bold green]Assigning floating IP..."):
        await hetzner.assign_floating_ip(ip, server)
    console.print(f"[green]Floating IP {ip.ip} assigned to {server.name}.[/green]")


@click.command("unassign")
@click.argument("ip_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def unassign_floating_ips(ip_id, client, yes):
    """Unassign a floating IP."""
    hetzner = await get_hetzner(client)
    ip = await hetzner.get_floating_ip_by_id(ip_id)
    if not ip:
        console.print(f"[red]Floating IP {ip_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Unassign floating IP '{ip.ip}'?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold yellow]Unassigning floating IP..."):
        await hetzner.unassign_floating_ip(ip)
    console.print(f"[green]Floating IP {ip.ip} unassigned.[/green]")


@click.command("rename")
@click.argument("ip_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_floating_ips(ip_id, name, client):
    """Rename a floating IP."""
    hetzner = await get_hetzner(client)
    ip = await hetzner.get_floating_ip_by_id(ip_id)
    if not ip:
        console.print(f"[red]Floating IP {ip_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_floating_ip(ip, name=name)
    console.print(f"[green]Floating IP renamed to {name}.[/green]")


@click.command("set-dns")
@click.argument("ip_id", type=int)
@click.option("--ip", "-i", "ip_address", required=True, help="IP address to set PTR for")
@click.option("--dns", "-d", required=True, help="Reverse DNS hostname")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def set_dns_floating_ips(ip_id, ip_address, dns, client):
    """Set reverse DNS for a floating IP."""
    hetzner = await get_hetzner(client)
    ip = await hetzner.get_floating_ip_by_id(ip_id)
    if not ip:
        console.print(f"[red]Floating IP {ip_id} not found[/red]")
        return
    with console.status("[bold green]Setting reverse DNS..."):
        await hetzner.change_floating_ip_dns_ptr(ip, ip_address, dns)
    console.print(f"[green]Reverse DNS set to {dns} for {ip_address}.[/green]")
