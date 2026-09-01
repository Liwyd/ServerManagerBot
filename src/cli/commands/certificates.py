import asyncio

import click

from src.cli import (
    console, async_command, get_hetzner, print_table, print_panel,
    confirm_action,
)


@click.command("list")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def list_certificates(client):
    """List all certificates."""
    hetzner = await get_hetzner(client)
    certs = await hetzner.get_certificates()
    if not certs:
        console.print("[yellow]No certificates found.[/yellow]")
        return

    rows = []
    for c in certs:
        rows.append([
            str(c.id), c.name, c.type,
            c.created.strftime("%Y-%m-%d"),
            c.not_valid_after.strftime("%Y-%m-%d") if c.not_valid_after else "—",
        ])
    print_table("Certificates", ["ID", "Name", "Type", "Created", "Expires"], rows)


@click.command("get")
@click.argument("cert_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def get_certificates(cert_id, client):
    """Get detailed certificate info."""
    hetzner = await get_hetzner(client)
    cert = await hetzner.get_certificate_by_id(cert_id)
    if not cert:
        console.print(f"[red]Certificate {cert_id} not found[/red]")
        return

    content = (
        f"[bold]Name:[/bold] {cert.name}\n"
        f"[bold]ID:[/bold] {cert.id}\n"
        f"[bold]Type:[/bold] {cert.type}\n"
        f"[bold]Created:[/bold] {cert.created.strftime('%Y-%m-%d %H:%M')}\n"
        f"[bold]Expires:[/bold] {cert.not_valid_after.strftime('%Y-%m-%d') if cert.not_valid_after else '—'}\n"
    )
    print_panel(f"Certificate {cert.id}", content)


@click.command("create")
@click.option("--name", "-n", required=True)
@click.option("--cert-file", required=True, help="Path to certificate PEM file")
@click.option("--key-file", required=True, help="Path to private key PEM file")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_certificates(name, cert_file, key_file, client):
    """Upload a certificate."""
    import os
    if not os.path.isfile(cert_file):
        console.print(f"[red]Certificate file not found: {cert_file}[/red]")
        return
    if not os.path.isfile(key_file):
        console.print(f"[red]Key file not found: {key_file}[/red]")
        return

    with open(cert_file) as f:
        cert_pem = f.read()
    with open(key_file) as f:
        key_pem = f.read()

    hetzner = await get_hetzner(client)
    with console.status("[bold green]Uploading certificate..."):
        result = await hetzner.create_certificate(name=name, certificate=cert_pem, private_key=key_pem)
    console.print(f"[green]Certificate uploaded: {result.certificate.name} (ID: {result.certificate.id})[/green]")


@click.command("create-managed")
@click.option("--name", "-n", required=True)
@click.option("--domain", "-d", "domains", multiple=True, required=True, help="Domain names for the certificate")
@click.option("--client", "-c", type=int, default=None)
@async_command
async def create_managed_certificates(name, domains, client):
    """Create a managed certificate (Let's Encrypt)."""
    hetzner = await get_hetzner(client)
    with console.status("[bold green]Creating managed certificate..."):
        result = await hetzner.create_managed_certificate(name=name, domains=list(domains))
    console.print(f"[green]Managed certificate created: {result.certificate.name} (ID: {result.certificate.id})[/green]")


@click.command("delete")
@click.argument("cert_id", type=int)
@click.option("--client", "-c", type=int, default=None)
@click.option("--yes", "-y", is_flag=True)
@async_command
async def delete_certificates(cert_id, client, yes):
    """Delete a certificate."""
    hetzner = await get_hetzner(client)
    cert = await hetzner.get_certificate_by_id(cert_id)
    if not cert:
        console.print(f"[red]Certificate {cert_id} not found[/red]")
        return

    if not yes:
        if not confirm_action(f"Delete certificate '{cert.name}' ({cert.id})?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with console.status("[bold red]Deleting certificate..."):
        await hetzner.delete_certificate(cert)
    console.print(f"[green]Certificate {cert.name} deleted.[/green]")


@click.command("rename")
@click.argument("cert_id", type=int)
@click.option("--name", "-n", required=True)
@click.option("--client", "-c", type=int, default=None)
@async_command
async def rename_certificates(cert_id, name, client):
    """Rename a certificate."""
    hetzner = await get_hetzner(client)
    cert = await hetzner.get_certificate_by_id(cert_id)
    if not cert:
        console.print(f"[red]Certificate {cert_id} not found[/red]")
        return
    with console.status("[bold green]Renaming..."):
        await hetzner.update_certificate(cert, name=name)
    console.print(f"[green]Certificate renamed to {name}.[/green]")
