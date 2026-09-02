import click

from src.cli import console, print_panel, Table


@click.group()
@click.version_option(version="1.0.0", prog_name="hserver")
def cli():
    """Hetzner Cloud CLI - Manage your Hetzner resources from terminal."""
    pass


@cli.command()
@click.option("--client", "-c", type=int, help="Client ID to use")
def status(client):
    """Show connection status and client info."""
    from src.cli import get_hetzner, get_client_token
    import asyncio

    async def _status():
        from src.db.core import AsyncSessionLocal
        from src.db import Client

        console.print("[bold]Hetzner Cloud CLI Status[/bold]\n")

        async with AsyncSessionLocal() as db:
            clients = await Client.get_all(db)

        if clients:
            table = Table(title="Registered Clients", show_header=True, header_style="bold cyan")
            table.add_column("ID", style="green")
            table.add_column("Remark")
            table.add_column("Token")
            for c in clients:
                token_display = c.secret[:8] + "..." + c.secret[-4:] if len(c.secret) > 12 else "****"
                table.add_row(str(c.id), c.remark, token_display)
            console.print(table)
        else:
            console.print("[yellow]No clients configured. Add one with: hserver clients add[/yellow]")

        try:
            hetzner = await get_hetzner(client)
            servers = await hetzner.get_servers()
            ips = await hetzner.get_primary_ips()
            volumes = await hetzner.get_volumes()
            networks = await hetzner.get_networks()
            ssh_keys = await hetzner.get_ssh_keys()

            console.print("\n[bold green]Connection: OK[/bold green]")
            print_panel(
                "Account Summary",
                f"Servers: [cyan]{len(servers)}[/cyan] | "
                f"Primary IPs: [cyan]{len(ips)}[/cyan] | "
                f"Volumes: [cyan]{len(volumes)}[/cyan] | "
                f"Networks: [cyan]{len(networks)}[/cyan] | "
                f"SSH Keys: [cyan]{len(ssh_keys)}[/cyan]",
                style="green",
            )
        except Exception as e:
            console.print(f"\n[bold red]Connection: FAILED[/bold red]")
            console.print(f"[red]{e}[/red]")

    asyncio.run(_status())


@cli.command()
def install():
    """Install ServerManagerBot."""
    import subprocess
    import sys

    script = "https://raw.githubusercontent.com/Liwyd/ServerManagerBot/master/install.sh"
    console.print("[bold green]Installing ServerManagerBot...[/bold green]")
    result = subprocess.run(["bash", "-c", f"curl -fsSL {script} | sudo bash"], check=False)
    if result.returncode != 0:
        console.print("[red]Installation failed.[/red]")
        sys.exit(1)


@cli.command()
def update():
    """Update ServerManagerBot."""
    import subprocess
    import sys

    install_dir = "/opt/servermanagerbot"
    if not os.path.isdir(install_dir):
        console.print("[red]No installation found. Run 'hserver install' first.[/red]")
        sys.exit(1)

    console.print("[bold green]Updating ServerManagerBot...[/bold green]")
    result = subprocess.run(["sudo", "bash", f"{install_dir}/install.sh", "--update"], check=False)
    if result.returncode != 0:
        console.print("[red]Update failed.[/red]")
        sys.exit(1)


@cli.command()
def uninstall():
    """Remove ServerManagerBot."""
    import subprocess
    import sys

    install_dir = "/opt/servermanagerbot"
    if not os.path.isdir(install_dir):
        console.print("[yellow]No installation found.[/yellow]")
        return

    if not click.confirm("[red]This will remove ServerManagerBot and all its data. Continue?[/red]", default=False):
        return

    console.print("[bold red]Removing ServerManagerBot...[/bold red]")
    result = subprocess.run(["sudo", "bash", f"{install_dir}/install.sh", "--delete"], check=False)
    if result.returncode != 0:
        console.print("[red]Uninstall failed.[/red]")
        sys.exit(1)


import os

from src.cli.commands.servers import (
    list_servers,
    get_servers,
    create_servers,
    delete_servers,
    power_on_servers,
    power_off_servers,
    reboot_servers,
    reset_servers,
    rebuild_servers,
    rename_servers,
    reset_password_servers,
    upgrade_servers,
    snapshots_servers,
    console_servers,
)
from src.cli.commands.volumes import (
    list_volumes,
    get_volumes,
    create_volumes,
    delete_volumes,
    resize_volumes,
    attach_volumes,
    detach_volumes,
    rename_volumes,
)
from src.cli.commands.floating_ips import (
    list_floating_ips,
    get_floating_ips,
    create_floating_ips,
    delete_floating_ips,
    assign_floating_ips,
    unassign_floating_ips,
    rename_floating_ips,
    set_dns_floating_ips,
)
from src.cli.commands.networks import (
    list_networks,
    get_networks,
    create_networks,
    delete_networks,
    rename_networks,
    add_subnet_networks,
    remove_subnet_networks,
    add_route_networks,
    remove_route_networks,
)
from src.cli.commands.firewalls import (
    list_firewalls,
    get_firewalls,
    create_firewalls,
    delete_firewalls,
    rename_firewalls,
    apply_firewalls,
    remove_firewalls,
)
from src.cli.commands.load_balancers import (
    list_load_balancers,
    get_load_balancers,
    create_load_balancers,
    delete_load_balancers,
    rename_load_balancers,
    add_target_load_balancers,
    remove_target_load_balancers,
)
from src.cli.commands.ssh_keys import (
    list_ssh_keys,
    get_ssh_keys,
    create_ssh_keys,
    delete_ssh_keys,
    rename_ssh_keys,
)
from src.cli.commands.certificates import (
    list_certificates,
    get_certificates,
    create_certificates,
    create_managed_certificates,
    delete_certificates,
    rename_certificates,
)
from src.cli.commands.placement_groups import (
    list_placement_groups,
    get_placement_groups,
    create_placement_groups,
    delete_placement_groups,
    rename_placement_groups,
)
from src.cli.commands.primary_ips import (
    list_primary_ips,
    get_primary_ips,
    create_primary_ips,
    delete_primary_ips,
    assign_primary_ips,
    unassign_primary_ips,
    rename_primary_ips,
    set_dns_primary_ips,
)
from src.cli.commands.snapshots import (
    list_snapshots,
    get_snapshots,
    delete_snapshots,
    rename_snapshots,
)
from src.cli.commands.clients import (
    list_clients,
    get_clients,
    add_clients,
    delete_clients,
    rename_clients,
    change_token_clients,
    test_clients,
)


@click.group()
def servers():
    pass


@click.group()
def volumes():
    pass


@click.group()
def floating_ips():
    pass


@click.group()
def networks():
    pass


@click.group()
def firewalls():
    pass


@click.group()
def load_balancers():
    pass


@click.group()
def ssh_keys():
    pass


@click.group()
def certificates():
    pass


@click.group()
def placement_groups():
    pass


@click.group()
def primary_ips():
    pass


@click.group()
def snapshots():
    pass


@click.group()
def clients():
    pass


cli.add_command(servers)
cli.add_command(volumes)
cli.add_command(floating_ips)
cli.add_command(networks)
cli.add_command(firewalls)
cli.add_command(load_balancers)
cli.add_command(ssh_keys)
cli.add_command(certificates)
cli.add_command(placement_groups)
cli.add_command(primary_ips)
cli.add_command(snapshots)
cli.add_command(clients)

servers.add_command(list_servers, "list")
servers.add_command(get_servers, "get")
servers.add_command(create_servers, "create")
servers.add_command(delete_servers, "delete")
servers.add_command(power_on_servers, "power-on")
servers.add_command(power_off_servers, "power-off")
servers.add_command(reboot_servers, "reboot")
servers.add_command(reset_servers, "reset")
servers.add_command(rebuild_servers, "rebuild")
servers.add_command(rename_servers, "rename")
servers.add_command(reset_password_servers, "reset-password")
servers.add_command(upgrade_servers, "upgrade")
servers.add_command(snapshots_servers, "snapshots")
servers.add_command(console_servers, "console")

volumes.add_command(list_volumes, "list")
volumes.add_command(get_volumes, "get")
volumes.add_command(create_volumes, "create")
volumes.add_command(delete_volumes, "delete")
volumes.add_command(resize_volumes, "resize")
volumes.add_command(attach_volumes, "attach")
volumes.add_command(detach_volumes, "detach")
volumes.add_command(rename_volumes, "rename")

floating_ips.add_command(list_floating_ips, "list")
floating_ips.add_command(get_floating_ips, "get")
floating_ips.add_command(create_floating_ips, "create")
floating_ips.add_command(delete_floating_ips, "delete")
floating_ips.add_command(assign_floating_ips, "assign")
floating_ips.add_command(unassign_floating_ips, "unassign")
floating_ips.add_command(rename_floating_ips, "rename")
floating_ips.add_command(set_dns_floating_ips, "set-dns")

networks.add_command(list_networks, "list")
networks.add_command(get_networks, "get")
networks.add_command(create_networks, "create")
networks.add_command(delete_networks, "delete")
networks.add_command(rename_networks, "rename")
networks.add_command(add_subnet_networks, "add-subnet")
networks.add_command(remove_subnet_networks, "remove-subnet")
networks.add_command(add_route_networks, "add-route")
networks.add_command(remove_route_networks, "remove-route")

firewalls.add_command(list_firewalls, "list")
firewalls.add_command(get_firewalls, "get")
firewalls.add_command(create_firewalls, "create")
firewalls.add_command(delete_firewalls, "delete")
firewalls.add_command(rename_firewalls, "rename")
firewalls.add_command(apply_firewalls, "apply")
firewalls.add_command(remove_firewalls, "remove")

load_balancers.add_command(list_load_balancers, "list")
load_balancers.add_command(get_load_balancers, "get")
load_balancers.add_command(create_load_balancers, "create")
load_balancers.add_command(delete_load_balancers, "delete")
load_balancers.add_command(rename_load_balancers, "rename")
load_balancers.add_command(add_target_load_balancers, "add-target")
load_balancers.add_command(remove_target_load_balancers, "remove-target")

ssh_keys.add_command(list_ssh_keys, "list")
ssh_keys.add_command(get_ssh_keys, "get")
ssh_keys.add_command(create_ssh_keys, "create")
ssh_keys.add_command(delete_ssh_keys, "delete")
ssh_keys.add_command(rename_ssh_keys, "rename")

certificates.add_command(list_certificates, "list")
certificates.add_command(get_certificates, "get")
certificates.add_command(create_certificates, "create")
certificates.add_command(create_managed_certificates, "create-managed")
certificates.add_command(delete_certificates, "delete")
certificates.add_command(rename_certificates, "rename")

placement_groups.add_command(list_placement_groups, "list")
placement_groups.add_command(get_placement_groups, "get")
placement_groups.add_command(create_placement_groups, "create")
placement_groups.add_command(delete_placement_groups, "delete")
placement_groups.add_command(rename_placement_groups, "rename")

primary_ips.add_command(list_primary_ips, "list")
primary_ips.add_command(get_primary_ips, "get")
primary_ips.add_command(create_primary_ips, "create")
primary_ips.add_command(delete_primary_ips, "delete")
primary_ips.add_command(assign_primary_ips, "assign")
primary_ips.add_command(unassign_primary_ips, "unassign")
primary_ips.add_command(rename_primary_ips, "rename")
primary_ips.add_command(set_dns_primary_ips, "set-dns")

snapshots.add_command(list_snapshots, "list")
snapshots.add_command(get_snapshots, "get")
snapshots.add_command(delete_snapshots, "delete")
snapshots.add_command(rename_snapshots, "rename")

clients.add_command(list_clients, "list")
clients.add_command(get_clients, "get")
clients.add_command(add_clients, "add")
clients.add_command(delete_clients, "delete")
clients.add_command(rename_clients, "rename")
clients.add_command(change_token_clients, "change-token")
clients.add_command(test_clients, "test")


def main():
    cli()
