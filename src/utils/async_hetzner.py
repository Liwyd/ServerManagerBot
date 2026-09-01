import asyncio
import logging
from typing import Optional

from hcloud import Client as HCloudClient
from hcloud.certificates.client import BoundCertificate
from hcloud.datacenters.client import BoundDatacenter
from hcloud.firewalls.client import BoundFirewall
from hcloud.floating_ips.client import BoundFloatingIP
from hcloud.images.client import BoundImage
from hcloud.load_balancers.client import BoundLoadBalancer
from hcloud.networks.client import BoundNetwork
from hcloud.placement_groups.client import BoundPlacementGroup
from hcloud.primary_ips.client import BoundPrimaryIP
from hcloud.server_types.client import BoundServerType
from hcloud.servers.client import BoundServer
from hcloud.ssh_keys.client import BoundSSHKey
from hcloud.volumes.client import BoundVolume

logger = logging.getLogger(__name__)


class AsyncHetznerClient:
    """Async wrapper around the synchronous hcloud SDK.

    Delegates all calls to asyncio.to_thread() to avoid blocking the
    asyncio event loop. The hcloud SDK's built-in retry logic for
    rate_limit_exceeded is preserved — no additional request volume
    is introduced.
    """

    def __init__(self, token: str):
        self._client = HCloudClient(token=token)

    @property
    def raw(self) -> HCloudClient:
        return self._client

    # ── Servers ──────────────────────────────────────────────

    async def get_servers(self, **kwargs) -> list[BoundServer]:
        return await asyncio.to_thread(self._client.servers.get_all, **kwargs)

    async def get_server_by_id(self, server_id: int) -> Optional[BoundServer]:
        return await asyncio.to_thread(self._client.servers.get_by_id, server_id)

    async def get_server_by_name(self, name: str) -> Optional[BoundServer]:
        return await asyncio.to_thread(self._client.servers.get_by_name, name)

    async def create_server(self, **kwargs):
        return await asyncio.to_thread(self._client.servers.create, **kwargs)

    async def update_server(self, server, **kwargs):
        return await asyncio.to_thread(self._client.servers.update, server, **kwargs)

    async def delete_server(self, server):
        return await asyncio.to_thread(self._client.servers.delete, server)

    async def power_on_server(self, server):
        return await asyncio.to_thread(self._client.servers.power_on, server)

    async def power_off_server(self, server):
        return await asyncio.to_thread(self._client.servers.power_off, server)

    async def reboot_server(self, server):
        return await asyncio.to_thread(self._client.servers.reboot, server)

    async def reset_server(self, server):
        return await asyncio.to_thread(self._client.servers.reset, server)

    async def shutdown_server(self, server):
        return await asyncio.to_thread(self._client.servers.shutdown, server)

    async def reset_server_password(self, server):
        return await asyncio.to_thread(self._client.servers.reset_password, server)

    async def change_server_type(self, server, **kwargs):
        return await asyncio.to_thread(self._client.servers.change_type, server, **kwargs)

    async def rebuild_server(self, server, **kwargs):
        return await asyncio.to_thread(self._client.servers.rebuild, server, **kwargs)

    async def create_server_image(self, server, **kwargs):
        return await asyncio.to_thread(self._client.servers.create_image, server, **kwargs)

    async def enable_server_rescue(self, server, **kwargs):
        return await asyncio.to_thread(self._client.servers.enable_rescue, server, **kwargs)

    async def disable_server_rescue(self, server):
        return await asyncio.to_thread(self._client.servers.disable_rescue, server)

    async def enable_server_backup(self, server):
        return await asyncio.to_thread(self._client.servers.enable_backup, server)

    async def disable_server_backup(self, server):
        return await asyncio.to_thread(self._client.servers.disable_backup, server)

    async def attach_iso(self, server, iso):
        return await asyncio.to_thread(self._client.servers.attach_iso, server, iso)

    async def detach_iso(self, server):
        return await asyncio.to_thread(self._client.servers.detach_iso, server)

    async def change_server_dns_ptr(self, server, ip, dns_ptr):
        return await asyncio.to_thread(self._client.servers.change_dns_ptr, server, ip, dns_ptr)

    async def change_server_protection(self, server, **kwargs):
        return await asyncio.to_thread(self._client.servers.change_protection, server, **kwargs)

    async def request_server_console(self, server):
        return await asyncio.to_thread(self._client.servers.request_console, server)

    async def attach_server_to_network(self, server, network, **kwargs):
        return await asyncio.to_thread(self._client.servers.attach_to_network, server, network, **kwargs)

    async def detach_server_from_network(self, server, network):
        return await asyncio.to_thread(self._client.servers.detach_from_network, server, network)

    async def add_server_to_placement_group(self, server, placement_group):
        return await asyncio.to_thread(self._client.servers.add_to_placement_group, server, placement_group)

    async def remove_server_from_placement_group(self, server):
        return await asyncio.to_thread(self._client.servers.remove_from_placement_group, server)

    # ── Images ───────────────────────────────────────────────

    async def get_images(self, **kwargs) -> list[BoundImage]:
        return await asyncio.to_thread(self._client.images.get_all, **kwargs)

    async def get_image_by_id(self, image_id: int) -> Optional[BoundImage]:
        return await asyncio.to_thread(self._client.images.get_by_id, image_id)

    async def get_image_by_name(self, name: str) -> Optional[BoundImage]:
        return await asyncio.to_thread(self._client.images.get_by_name, name)

    async def update_image(self, image, **kwargs):
        return await asyncio.to_thread(self._client.images.update, image, **kwargs)

    async def delete_image(self, image):
        return await asyncio.to_thread(self._client.images.delete, image)

    # ── Datacenters ──────────────────────────────────────────

    async def get_datacenters(self, **kwargs) -> list[BoundDatacenter]:
        return await asyncio.to_thread(self._client.datacenters.get_all, **kwargs)

    async def get_datacenter_by_id(self, datacenter_id: int) -> Optional[BoundDatacenter]:
        return await asyncio.to_thread(self._client.datacenters.get_by_id, datacenter_id)

    # ── Server Types ─────────────────────────────────────────

    async def get_server_types(self, **kwargs) -> list[BoundServerType]:
        return await asyncio.to_thread(self._client.server_types.get_all, **kwargs)

    async def get_server_type_by_id(self, server_type_id: int) -> Optional[BoundServerType]:
        return await asyncio.to_thread(self._client.server_types.get_by_id, server_type_id)

    # ── Primary IPs ──────────────────────────────────────────

    async def get_primary_ips(self, **kwargs) -> list[BoundPrimaryIP]:
        return await asyncio.to_thread(self._client.primary_ips.get_all, **kwargs)

    async def get_primary_ip_by_id(self, primary_ip_id: int) -> Optional[BoundPrimaryIP]:
        return await asyncio.to_thread(self._client.primary_ips.get_by_id, primary_ip_id)

    async def create_primary_ip(self, **kwargs):
        return await asyncio.to_thread(self._client.primary_ips.create, **kwargs)

    async def update_primary_ip(self, primary_ip, **kwargs):
        return await asyncio.to_thread(self._client.primary_ips.update, primary_ip, **kwargs)

    async def delete_primary_ip(self, primary_ip):
        return await asyncio.to_thread(self._client.primary_ips.delete, primary_ip)

    async def assign_primary_ip(self, primary_ip, **kwargs):
        return await asyncio.to_thread(self._client.primary_ips.assign, primary_ip, **kwargs)

    async def unassign_primary_ip(self, primary_ip):
        return await asyncio.to_thread(self._client.primary_ips.unassign, primary_ip)

    # ── Volumes ──────────────────────────────────────────────

    async def get_volumes(self, **kwargs) -> list[BoundVolume]:
        return await asyncio.to_thread(self._client.volumes.get_all, **kwargs)

    async def get_volume_by_id(self, volume_id: int) -> Optional[BoundVolume]:
        return await asyncio.to_thread(self._client.volumes.get_by_id, volume_id)

    async def create_volume(self, **kwargs):
        return await asyncio.to_thread(self._client.volumes.create, **kwargs)

    async def update_volume(self, volume, **kwargs):
        return await asyncio.to_thread(self._client.volumes.update, volume, **kwargs)

    async def delete_volume(self, volume):
        return await asyncio.to_thread(self._client.volumes.delete, volume)

    async def resize_volume(self, volume, size: int):
        return await asyncio.to_thread(self._client.volumes.resize, volume, size)

    async def attach_volume(self, volume, server, **kwargs):
        return await asyncio.to_thread(self._client.volumes.attach, volume, server, **kwargs)

    async def detach_volume(self, volume):
        return await asyncio.to_thread(self._client.volumes.detach, volume)

    # ── Floating IPs ─────────────────────────────────────────

    async def get_floating_ips(self, **kwargs) -> list[BoundFloatingIP]:
        return await asyncio.to_thread(self._client.floating_ips.get_all, **kwargs)

    async def get_floating_ip_by_id(self, floating_ip_id: int) -> Optional[BoundFloatingIP]:
        return await asyncio.to_thread(self._client.floating_ips.get_by_id, floating_ip_id)

    async def create_floating_ip(self, **kwargs):
        return await asyncio.to_thread(self._client.floating_ips.create, **kwargs)

    async def update_floating_ip(self, floating_ip, **kwargs):
        return await asyncio.to_thread(self._client.floating_ips.update, floating_ip, **kwargs)

    async def delete_floating_ip(self, floating_ip):
        return await asyncio.to_thread(self._client.floating_ips.delete, floating_ip)

    async def assign_floating_ip(self, floating_ip, server):
        return await asyncio.to_thread(self._client.floating_ips.assign, floating_ip, server)

    async def unassign_floating_ip(self, floating_ip):
        return await asyncio.to_thread(self._client.floating_ips.unassign, floating_ip)

    async def change_floating_ip_dns_ptr(self, floating_ip, ip, dns_ptr):
        return await asyncio.to_thread(self._client.floating_ips.change_dns_ptr, floating_ip, ip, dns_ptr)

    # ── Networks ─────────────────────────────────────────────

    async def get_networks(self, **kwargs) -> list[BoundNetwork]:
        return await asyncio.to_thread(self._client.networks.get_all, **kwargs)

    async def get_network_by_id(self, network_id: int) -> Optional[BoundNetwork]:
        return await asyncio.to_thread(self._client.networks.get_by_id, network_id)

    async def create_network(self, **kwargs):
        return await asyncio.to_thread(self._client.networks.create, **kwargs)

    async def update_network(self, network, **kwargs):
        return await asyncio.to_thread(self._client.networks.update, network, **kwargs)

    async def delete_network(self, network):
        return await asyncio.to_thread(self._client.networks.delete, network)

    async def add_subnet_to_network(self, network, subnet):
        return await asyncio.to_thread(self._client.networks.add_subnet, network, subnet)

    async def delete_subnet_from_network(self, network, subnet):
        return await asyncio.to_thread(self._client.networks.delete_subnet, network, subnet)

    async def add_route_to_network(self, network, route):
        return await asyncio.to_thread(self._client.networks.add_route, network, route)

    async def delete_route_from_network(self, network, route):
        return await asyncio.to_thread(self._client.networks.delete_route, network, route)

    # ── Firewalls ────────────────────────────────────────────

    async def get_firewalls(self, **kwargs) -> list[BoundFirewall]:
        return await asyncio.to_thread(self._client.firewalls.get_all, **kwargs)

    async def get_firewall_by_id(self, firewall_id: int) -> Optional[BoundFirewall]:
        return await asyncio.to_thread(self._client.firewalls.get_by_id, firewall_id)

    async def create_firewall(self, **kwargs):
        return await asyncio.to_thread(self._client.firewalls.create, **kwargs)

    async def update_firewall(self, firewall, **kwargs):
        return await asyncio.to_thread(self._client.firewalls.update, firewall, **kwargs)

    async def delete_firewall(self, firewall):
        return await asyncio.to_thread(self._client.firewalls.delete, firewall)

    async def set_firewall_rules(self, firewall, rules):
        return await asyncio.to_thread(self._client.firewalls.set_rules, firewall, rules)

    async def apply_firewall_to_resources(self, firewall, resources):
        return await asyncio.to_thread(self._client.firewalls.apply_to_resources, firewall, resources)

    async def remove_firewall_from_resources(self, firewall, resources):
        return await asyncio.to_thread(self._client.firewalls.remove_from_resources, firewall, resources)

    # ── Load Balancers ───────────────────────────────────────

    async def get_load_balancers(self, **kwargs) -> list[BoundLoadBalancer]:
        return await asyncio.to_thread(self._client.load_balancers.get_all, **kwargs)

    async def get_load_balancer_by_id(self, load_balancer_id: int) -> Optional[BoundLoadBalancer]:
        return await asyncio.to_thread(self._client.load_balancers.get_by_id, load_balancer_id)

    async def create_load_balancer(self, **kwargs):
        return await asyncio.to_thread(self._client.load_balancers.create, **kwargs)

    async def update_load_balancer(self, load_balancer, **kwargs):
        return await asyncio.to_thread(self._client.load_balancers.update, load_balancer, **kwargs)

    async def delete_load_balancer(self, load_balancer):
        return await asyncio.to_thread(self._client.load_balancers.delete, load_balancer)

    async def add_load_balancer_service(self, load_balancer, service):
        return await asyncio.to_thread(self._client.load_balancers.add_service, load_balancer, service)

    async def delete_load_balancer_service(self, load_balancer, service):
        return await asyncio.to_thread(self._client.load_balancers.delete_service, load_balancer, service)

    async def add_load_balancer_target(self, load_balancer, target):
        return await asyncio.to_thread(self._client.load_balancers.add_target, load_balancer, target)

    async def remove_load_balancer_target(self, load_balancer, target):
        return await asyncio.to_thread(self._client.load_balancers.remove_target, load_balancer, target)

    async def change_load_balancer_type(self, load_balancer, load_balancer_type):
        return await asyncio.to_thread(self._client.load_balancers.change_type, load_balancer, load_balancer_type)

    async def enable_load_balancer_public_interface(self, load_balancer):
        return await asyncio.to_thread(self._client.load_balancers.enable_public_interface, load_balancer)

    async def disable_load_balancer_public_interface(self, load_balancer):
        return await asyncio.to_thread(self._client.load_balancers.disable_public_interface, load_balancer)

    # ── SSH Keys ─────────────────────────────────────────────

    async def get_ssh_keys(self, **kwargs) -> list[BoundSSHKey]:
        return await asyncio.to_thread(self._client.ssh_keys.get_all, **kwargs)

    async def get_ssh_key_by_id(self, ssh_key_id: int) -> Optional[BoundSSHKey]:
        return await asyncio.to_thread(self._client.ssh_keys.get_by_id, ssh_key_id)

    async def create_ssh_key(self, **kwargs):
        return await asyncio.to_thread(self._client.ssh_keys.create, **kwargs)

    async def update_ssh_key(self, ssh_key, **kwargs):
        return await asyncio.to_thread(self._client.ssh_keys.update, ssh_key, **kwargs)

    async def delete_ssh_key(self, ssh_key):
        return await asyncio.to_thread(self._client.ssh_keys.delete, ssh_key)

    # ── Certificates ─────────────────────────────────────────

    async def get_certificates(self, **kwargs) -> list[BoundCertificate]:
        return await asyncio.to_thread(self._client.certificates.get_all, **kwargs)

    async def get_certificate_by_id(self, certificate_id: int) -> Optional[BoundCertificate]:
        return await asyncio.to_thread(self._client.certificates.get_by_id, certificate_id)

    async def create_certificate(self, **kwargs):
        return await asyncio.to_thread(self._client.certificates.create, **kwargs)

    async def create_managed_certificate(self, **kwargs):
        return await asyncio.to_thread(self._client.certificates.create_managed, **kwargs)

    async def update_certificate(self, certificate, **kwargs):
        return await asyncio.to_thread(self._client.certificates.update, certificate, **kwargs)

    async def delete_certificate(self, certificate):
        return await asyncio.to_thread(self._client.certificates.delete, certificate)

    # ── Placement Groups ─────────────────────────────────────

    async def get_placement_groups(self, **kwargs) -> list[BoundPlacementGroup]:
        return await asyncio.to_thread(self._client.placement_groups.get_all, **kwargs)

    async def get_placement_group_by_id(self, placement_group_id: int) -> Optional[BoundPlacementGroup]:
        return await asyncio.to_thread(self._client.placement_groups.get_by_id, placement_group_id)

    async def create_placement_group(self, **kwargs):
        return await asyncio.to_thread(self._client.placement_groups.create, **kwargs)

    async def update_placement_group(self, placement_group, **kwargs):
        return await asyncio.to_thread(self._client.placement_groups.update, placement_group, **kwargs)

    async def delete_placement_group(self, placement_group):
        return await asyncio.to_thread(self._client.placement_groups.delete, placement_group)

    # ── Locations ────────────────────────────────────────────

    async def get_locations(self, **kwargs):
        return await asyncio.to_thread(self._client.locations.get_all, **kwargs)

    async def get_location_by_id(self, location_id: int):
        return await asyncio.to_thread(self._client.locations.get_by_id, location_id)
