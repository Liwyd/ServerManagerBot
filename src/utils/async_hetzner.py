import logging
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)

API_BASE = "https://api.hetzner.cloud/v1"


class HetznerAPIError(Exception):
    def __init__(self, status: int, error_type: str, message: str):
        self.status = status
        self.error_type = error_type
        self.message = message
        super().__init__(f"{error_type}: {message}")


class AttrDict(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            value = self[name]
        except KeyError:
            raise AttributeError(name)
        return _convert(value)

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


def _convert(obj: Any) -> Any:
    if isinstance(obj, dict):
        return AttrDict({k: _convert(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [_convert(item) for item in obj]
    return obj


def _id(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (int, str)):
        return obj
    if hasattr(obj, "id_or_name"):
        return obj.id_or_name
    if hasattr(obj, "id"):
        return obj.id
    if isinstance(obj, dict) and "id" in obj:
        return obj["id"]
    return obj


def _name(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "name"):
        return obj.name
    if isinstance(obj, dict) and "name" in obj:
        return obj["name"]
    return obj


class AsyncHetznerClient:
    def __init__(self, token: str):
        self._token = token

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = {"Authorization": f"Bearer {self._token}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            url = f"{API_BASE}{path}"
            logger.debug("Hetznner API %s %s", method, url)
            async with session.request(method, url, **kwargs) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    error = data.get("error", {})
                    raise HetznerAPIError(
                        status=resp.status,
                        error_type=error.get("code", "unknown"),
                        message=error.get("message", str(data)),
                    )
                return _convert(data)

    async def _get_all(self, path: str, key: str, params: dict | None = None) -> list:
        results: list = []
        page = 1
        while True:
            p = dict(params or {})
            p["page"] = page
            p["per_page"] = 50
            data = await self._request("GET", path, params=p)
            items = data.get(key, [])
            results.extend(items)
            pagination = data.get("meta", {}).get("pagination", {})
            if not pagination or not pagination.get("next_page"):
                break
            page += 1
        return results

    # ── Servers ──────────────────────────────────────────────

    async def get_servers(self) -> list:
        return await self._get_all("/servers", "servers")

    async def get_server_by_id(self, server_id: int) -> Any:
        try:
            data = await self._request("GET", f"/servers/{server_id}")
            return data.server
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def get_server_by_name(self, name: str) -> Any:
        try:
            data = await self._request("GET", "/servers", params={"name": name})
            servers = data.get("servers", [])
            return servers[0] if servers else None
        except HetznerAPIError:
            return None

    async def create_server(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "server_type": _id(kwargs["server_type"]),
            "image": _id(kwargs["image"]),
            "start_after_create": kwargs.get("start_after_create", True),
        }
        if "datacenter" in kwargs and kwargs["datacenter"] is not None:
            payload["datacenter"] = _id(kwargs["datacenter"])
        if "location" in kwargs and kwargs["location"] is not None:
            payload["location"] = _name(kwargs["location"])
        if "ssh_keys" in kwargs and kwargs["ssh_keys"] is not None:
            payload["ssh_keys"] = [_id(k) for k in kwargs["ssh_keys"]]
        if "volumes" in kwargs and kwargs["volumes"] is not None:
            payload["volumes"] = [_id(v) for v in kwargs["volumes"]]
        if "networks" in kwargs and kwargs["networks"] is not None:
            payload["networks"] = [_id(n) for n in kwargs["networks"]]
        if "firewalls" in kwargs and kwargs["firewalls"] is not None:
            payload["firewalls"] = [{"firewall": _id(f)} for f in kwargs["firewalls"]]
        if "user_data" in kwargs:
            payload["user_data"] = kwargs["user_data"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        if "automount" in kwargs:
            payload["automount"] = kwargs["automount"]
        if "placement_group" in kwargs and kwargs["placement_group"] is not None:
            payload["placement_group"] = _id(kwargs["placement_group"])
        return await self._request("POST", "/servers", json=payload)

    async def update_server(self, server: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/servers/{_id(server)}", json=payload)

    async def delete_server(self, server: Any) -> Any:
        return await self._request("DELETE", f"/servers/{_id(server)}")

    async def _server_action(self, server: Any, action: str, payload: dict | None = None) -> Any:
        return await self._request("POST", f"/servers/{_id(server)}/actions/{action}", json=payload)

    async def power_on_server(self, server: Any) -> Any:
        return await self._server_action(server, "poweron")

    async def power_off_server(self, server: Any) -> Any:
        return await self._server_action(server, "poweroff")

    async def reboot_server(self, server: Any) -> Any:
        return await self._server_action(server, "reboot")

    async def reset_server(self, server: Any) -> Any:
        return await self._server_action(server, "reset")

    async def shutdown_server(self, server: Any) -> Any:
        return await self._server_action(server, "shutdown")

    async def reset_server_password(self, server: Any) -> Any:
        return await self._server_action(server, "reset_password")

    async def change_server_type(self, server: Any, **kwargs: Any) -> Any:
        payload = {
            "server_type": _id(kwargs["server_type"]),
            "upgrade_disk": kwargs.get("upgrade_disk", False),
        }
        return await self._server_action(server, "change_type", payload=payload)

    async def rebuild_server(self, server: Any, **kwargs: Any) -> Any:
        return await self._server_action(server, "rebuild", payload={"image": _id(kwargs["image"])})

    async def create_server_image(self, server: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "type" in kwargs:
            payload["type"] = kwargs["type"]
        if "description" in kwargs:
            payload["description"] = kwargs["description"]
        if "image_color" in kwargs:
            payload["image_color"] = kwargs["image_color"]
        return await self._server_action(server, "create_image", payload=payload)

    async def enable_server_rescue(self, server: Any, **kwargs: Any) -> Any:
        return await self._server_action(server, "enable_rescue", payload=kwargs)

    async def disable_server_rescue(self, server: Any) -> Any:
        return await self._server_action(server, "disable_rescue")

    async def enable_server_backup(self, server: Any) -> Any:
        return await self._server_action(server, "enable_backup")

    async def disable_server_backup(self, server: Any) -> Any:
        return await self._server_action(server, "disable_backup")

    async def attach_iso(self, server: Any, iso: Any) -> Any:
        return await self._server_action(server, "attach_iso", payload={"iso": _id(iso)})

    async def detach_iso(self, server: Any) -> Any:
        return await self._server_action(server, "detach_iso")

    async def change_server_dns_ptr(self, server: Any, ip: str, dns_ptr: str) -> Any:
        return await self._server_action(server, "change_dns_ptr", payload={"ip": ip, "dns_ptr": dns_ptr})

    async def change_server_protection(self, server: Any, **kwargs: Any) -> Any:
        return await self._server_action(server, "change_protection", payload=kwargs)

    async def request_server_console(self, server: Any) -> Any:
        return await self._server_action(server, "request_console")

    async def attach_server_to_network(self, server: Any, network: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {"network": _id(network)}
        if "ip" in kwargs:
            payload["ip"] = kwargs["ip"]
        if "alias_ips" in kwargs:
            payload["alias_ips"] = kwargs["alias_ips"]
        return await self._server_action(server, "attach_to_network", payload=payload)

    async def detach_server_from_network(self, server: Any, network: Any) -> Any:
        return await self._server_action(server, "detach_from_network", payload={"network": _id(network)})

    async def add_server_to_placement_group(self, server: Any, placement_group: Any) -> Any:
        return await self._server_action(server, "add_to_placement_group", payload={"placement_group": _id(placement_group)})

    async def remove_server_from_placement_group(self, server: Any) -> Any:
        return await self._server_action(server, "remove_from_placement_group")

    # ── Images ───────────────────────────────────────────────

    async def get_images(self, **kwargs: Any) -> list:
        params: dict[str, Any] = {}
        if "type" in kwargs:
            t = kwargs["type"]
            params["type"] = ",".join(t) if isinstance(t, list) else t
        if "architecture" in kwargs:
            params["architecture"] = kwargs["architecture"]
        return await self._get_all("/images", "images", params=params)

    async def get_image_by_id(self, image_id: int) -> Any:
        try:
            data = await self._request("GET", f"/images/{image_id}")
            return data.image
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def get_image_by_name(self, name: str) -> Any:
        try:
            data = await self._request("GET", "/images", params={"name": name})
            images = data.get("images", [])
            return images[0] if images else None
        except HetznerAPIError:
            return None

    async def update_image(self, image: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "description" in kwargs:
            payload["description"] = kwargs["description"]
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/images/{_id(image)}", json=payload)

    async def delete_image(self, image: Any) -> Any:
        return await self._request("DELETE", f"/images/{_id(image)}")

    # ── Datacenters ──────────────────────────────────────────

    async def get_datacenters(self) -> list:
        return await self._get_all("/datacenters", "datacenters")

    async def get_datacenter_by_id(self, datacenter_id: int) -> Any:
        try:
            data = await self._request("GET", f"/datacenters/{datacenter_id}")
            return data.datacenter
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    # ── Server Types ─────────────────────────────────────────

    async def get_server_types(self) -> list:
        return await self._get_all("/server_types", "server_types")

    async def get_server_type_by_id(self, server_type_id: int) -> Any:
        try:
            data = await self._request("GET", f"/server_types/{server_type_id}")
            return data.server_type
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    # ── Primary IPs ──────────────────────────────────────────

    async def get_primary_ips(self) -> list:
        return await self._get_all("/primary_ips", "primary_ips")

    async def get_primary_ip_by_id(self, primary_ip_id: int) -> Any:
        try:
            data = await self._request("GET", f"/primary_ips/{primary_ip_id}")
            return data.primary_ip
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_primary_ip(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "type": kwargs["type"],
            "assignee_type": kwargs.get("assignee_type", "server"),
            "auto_delete": kwargs.get("auto_delete", False),
        }
        if "datacenter" in kwargs and kwargs["datacenter"] is not None:
            payload["datacenter"] = (
                _name(kwargs["datacenter"]) if isinstance(kwargs["datacenter"], str) else _id(kwargs["datacenter"])
            )
        if "assignee_id" in kwargs:
            payload["assignee_id"] = kwargs["assignee_id"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("POST", "/primary_ips", json=payload)

    async def update_primary_ip(self, primary_ip: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        if "auto_delete" in kwargs:
            payload["auto_delete"] = kwargs["auto_delete"]
        return await self._request("PUT", f"/primary_ips/{_id(primary_ip)}", json=payload)

    async def delete_primary_ip(self, primary_ip: Any) -> Any:
        return await self._request("DELETE", f"/primary_ips/{_id(primary_ip)}")

    async def assign_primary_ip(self, primary_ip: Any, **kwargs: Any) -> Any:
        return await self._request(
            "POST",
            f"/primary_ips/{_id(primary_ip)}/actions/assign",
            json={"assignee_id": kwargs["assignee_id"], "assignee_type": kwargs.get("assignee_type", "server")},
        )

    async def unassign_primary_ip(self, primary_ip: Any) -> Any:
        return await self._request("POST", f"/primary_ips/{_id(primary_ip)}/actions/unassign")

    async def change_primary_ip_dns_ptr(self, primary_ip: Any, ip: str, dns_ptr: str) -> Any:
        return await self._request(
            "POST",
            f"/primary_ips/{_id(primary_ip)}/actions/change_dns_ptr",
            json={"ip": ip, "dns_ptr": dns_ptr},
        )

    # ── Volumes ──────────────────────────────────────────────

    async def get_volumes(self) -> list:
        return await self._get_all("/volumes", "volumes")

    async def get_volume_by_id(self, volume_id: int) -> Any:
        try:
            data = await self._request("GET", f"/volumes/{volume_id}")
            return data.volume
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_volume(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "size": kwargs["size"],
        }
        if "location" in kwargs and kwargs["location"] is not None:
            payload["location"] = _name(kwargs["location"])
        if "server" in kwargs and kwargs["server"] is not None:
            payload["server"] = _id(kwargs["server"])
        if "format" in kwargs:
            payload["format"] = kwargs["format"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        if "automount" in kwargs:
            payload["automount"] = kwargs["automount"]
        return await self._request("POST", "/volumes", json=payload)

    async def update_volume(self, volume: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/volumes/{_id(volume)}", json=payload)

    async def delete_volume(self, volume: Any) -> Any:
        return await self._request("DELETE", f"/volumes/{_id(volume)}")

    async def resize_volume(self, volume: Any, size: int) -> Any:
        return await self._request("POST", f"/volumes/{_id(volume)}/actions/resize", json={"size": size})

    async def attach_volume(self, volume: Any, server: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {"server": _id(server)}
        if "automount" in kwargs:
            payload["automount"] = kwargs["automount"]
        return await self._request("POST", f"/volumes/{_id(volume)}/actions/attach", json=payload)

    async def detach_volume(self, volume: Any) -> Any:
        return await self._request("POST", f"/volumes/{_id(volume)}/actions/detach")

    # ── Floating IPs ─────────────────────────────────────────

    async def get_floating_ips(self) -> list:
        return await self._get_all("/floating_ips", "floating_ips")

    async def get_floating_ip_by_id(self, floating_ip_id: int) -> Any:
        try:
            data = await self._request("GET", f"/floating_ips/{floating_ip_id}")
            return data.floating_ip
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_floating_ip(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {"type": kwargs["type"]}
        if "description" in kwargs:
            payload["description"] = kwargs["description"]
        if "home_location" in kwargs and kwargs["home_location"] is not None:
            payload["home_location"] = _name(kwargs["home_location"])
        if "server" in kwargs and kwargs["server"] is not None:
            payload["server"] = _id(kwargs["server"])
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("POST", "/floating_ips", json=payload)

    async def update_floating_ip(self, floating_ip: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "description" in kwargs:
            payload["description"] = kwargs["description"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/floating_ips/{_id(floating_ip)}", json=payload)

    async def delete_floating_ip(self, floating_ip: Any) -> Any:
        return await self._request("DELETE", f"/floating_ips/{_id(floating_ip)}")

    async def assign_floating_ip(self, floating_ip: Any, server: Any) -> Any:
        return await self._request("POST", f"/floating_ips/{_id(floating_ip)}/actions/assign", json={"server": _id(server)})

    async def unassign_floating_ip(self, floating_ip: Any) -> Any:
        return await self._request("POST", f"/floating_ips/{_id(floating_ip)}/actions/unassign")

    async def change_floating_ip_dns_ptr(self, floating_ip: Any, ip: str, dns_ptr: str) -> Any:
        return await self._request(
            "POST",
            f"/floating_ips/{_id(floating_ip)}/actions/change_dns_ptr",
            json={"ip": ip, "dns_ptr": dns_ptr},
        )

    # ── Networks ─────────────────────────────────────────────

    async def get_networks(self) -> list:
        return await self._get_all("/networks", "networks")

    async def get_network_by_id(self, network_id: int) -> Any:
        try:
            data = await self._request("GET", f"/networks/{network_id}")
            return data.network
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_network(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "ip_range": kwargs["ip_range"],
        }
        if "subnets" in kwargs:
            payload["subnets"] = kwargs["subnets"]
        if "routes" in kwargs:
            payload["routes"] = kwargs["routes"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("POST", "/networks", json=payload)

    async def update_network(self, network: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/networks/{_id(network)}", json=payload)

    async def delete_network(self, network: Any) -> Any:
        return await self._request("DELETE", f"/networks/{_id(network)}")

    async def add_subnet_to_network(self, network: Any, subnet: Any) -> Any:
        if isinstance(subnet, dict):
            payload = subnet
        else:
            payload = {"type": subnet.type, "ip_range": subnet.ip_range, "network_zone": subnet.network_zone}
        return await self._request("POST", f"/networks/{_id(network)}/actions/add_subnet", json=payload)

    async def delete_subnet_from_network(self, network: Any, subnet: Any) -> Any:
        subnet_id = subnet if isinstance(subnet, (int, str)) else (subnet.id if hasattr(subnet, "id") else subnet)
        return await self._request("POST", f"/networks/{_id(network)}/actions/delete_subnet", json={"subnet": subnet_id})

    async def add_route_to_network(self, network: Any, route: Any) -> Any:
        if isinstance(route, dict):
            payload = route
        else:
            payload = {"destination": route.destination, "gateway": route.gateway}
        return await self._request("POST", f"/networks/{_id(network)}/actions/add_route", json=payload)

    async def delete_route_from_network(self, network: Any, route: Any) -> Any:
        route_id = route if isinstance(route, (int, str)) else (route.id if hasattr(route, "id") else route)
        return await self._request("POST", f"/networks/{_id(network)}/actions/delete_route", json={"route": route_id})

    # ── Firewalls ────────────────────────────────────────────

    async def get_firewalls(self) -> list:
        return await self._get_all("/firewalls", "firewalls")

    async def get_firewall_by_id(self, firewall_id: int) -> Any:
        try:
            data = await self._request("GET", f"/firewalls/{firewall_id}")
            return data.firewall
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_firewall(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {"name": kwargs["name"]}
        if "rules" in kwargs:
            payload["rules"] = kwargs["rules"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        if "apply_to" in kwargs:
            payload["apply_to"] = kwargs["apply_to"]
        return await self._request("POST", "/firewalls", json=payload)

    async def update_firewall(self, firewall: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/firewalls/{_id(firewall)}", json=payload)

    async def delete_firewall(self, firewall: Any) -> Any:
        return await self._request("DELETE", f"/firewalls/{_id(firewall)}")

    async def set_firewall_rules(self, firewall: Any, rules: list) -> Any:
        return await self._request("POST", f"/firewalls/{_id(firewall)}/actions/set_rules", json={"rules": rules})

    async def apply_firewall_to_resources(self, firewall: Any, resources: list) -> Any:
        formatted = []
        for r in resources:
            if isinstance(r, dict):
                formatted.append(r)
            else:
                formatted.append({"type": r.type, "server": {"id": r.server.id}})
        return await self._request(
            "POST", f"/firewalls/{_id(firewall)}/actions/apply_to_resources", json={"resources": formatted}
        )

    async def remove_firewall_from_resources(self, firewall: Any, resources: list) -> Any:
        formatted = []
        for r in resources:
            if isinstance(r, dict):
                formatted.append(r)
            else:
                formatted.append({"type": r.type, "server": {"id": r.server.id}})
        return await self._request(
            "POST", f"/firewalls/{_id(firewall)}/actions/remove_from_resources", json={"resources": formatted}
        )

    # ── Load Balancers ───────────────────────────────────────

    async def get_load_balancers(self) -> list:
        return await self._get_all("/load_balancers", "load_balancers")

    async def get_load_balancer_by_id(self, load_balancer_id: int) -> Any:
        try:
            data = await self._request("GET", f"/load_balancers/{load_balancer_id}")
            return data.load_balancer
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_load_balancer(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "load_balancer_type": _name(kwargs.get("load_balancer_type") or kwargs.get("lb_type")),
        }
        if "location" in kwargs:
            payload["location"] = kwargs["location"]
        if "algorithm" in kwargs:
            payload["algorithm"] = kwargs["algorithm"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        if "target" in kwargs:
            payload["target"] = kwargs["target"]
        if "service" in kwargs:
            payload["service"] = kwargs["service"]
        return await self._request("POST", "/load_balancers", json=payload)

    async def update_load_balancer(self, load_balancer: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/load_balancers/{_id(load_balancer)}", json=payload)

    async def delete_load_balancer(self, load_balancer: Any) -> Any:
        return await self._request("DELETE", f"/load_balancers/{_id(load_balancer)}")

    async def add_load_balancer_target(self, load_balancer: Any, target: Any) -> Any:
        if isinstance(target, dict):
            payload = target
        else:
            t: dict[str, Any] = {"type": target.type}
            if target.type == "server" and target.server:
                t["server"] = {"id": target.server.id}
            payload = {"target": t}
        return await self._request("POST", f"/load_balancers/{_id(load_balancer)}/actions/add_target", json=payload)

    async def remove_load_balancer_target(self, load_balancer: Any, target: Any) -> Any:
        if isinstance(target, dict):
            payload = target
        else:
            t: dict[str, Any] = {"type": target.type}
            if target.type == "server" and target.server:
                t["server"] = {"id": target.server.id}
            payload = {"target": t}
        return await self._request("POST", f"/load_balancers/{_id(load_balancer)}/actions/remove_target", json=payload)

    async def add_load_balancer_service(self, load_balancer: Any, service: Any) -> Any:
        return await self._request("POST", f"/load_balancers/{_id(load_balancer)}/actions/add_service", json=service)

    async def delete_load_balancer_service(self, load_balancer: Any, service: Any) -> Any:
        return await self._request("POST", f"/load_balancers/{_id(load_balancer)}/actions/delete_service", json=service)

    async def change_load_balancer_type(self, load_balancer: Any, load_balancer_type: Any) -> Any:
        return await self._request(
            "POST",
            f"/load_balancers/{_id(load_balancer)}/actions/change_type",
            json={"load_balancer_type": _name(load_balancer_type)},
        )

    async def enable_load_balancer_public_interface(self, load_balancer: Any) -> Any:
        return await self._request("POST", f"/load_balancers/{_id(load_balancer)}/actions/enable_public_interface")

    async def disable_load_balancer_public_interface(self, load_balancer: Any) -> Any:
        return await self._request("POST", f"/load_balancers/{_id(load_balancer)}/actions/disable_public_interface")

    async def get_load_balancer_types(self) -> list:
        return await self._get_all("/load_balancer_types", "load_balancer_types")

    # ── SSH Keys ─────────────────────────────────────────────

    async def get_ssh_keys(self) -> list:
        return await self._get_all("/ssh_keys", "ssh_keys")

    async def get_ssh_key_by_id(self, ssh_key_id: int) -> Any:
        try:
            data = await self._request("GET", f"/ssh_keys/{ssh_key_id}")
            return data.ssh_key
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_ssh_key(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "public_key": kwargs["public_key"],
        }
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("POST", "/ssh_keys", json=payload)

    async def update_ssh_key(self, ssh_key: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/ssh_keys/{_id(ssh_key)}", json=payload)

    async def delete_ssh_key(self, ssh_key: Any) -> Any:
        return await self._request("DELETE", f"/ssh_keys/{_id(ssh_key)}")

    # ── Certificates ─────────────────────────────────────────

    async def get_certificates(self) -> list:
        return await self._get_all("/certificates", "certificates")

    async def get_certificate_by_id(self, certificate_id: int) -> Any:
        try:
            data = await self._request("GET", f"/certificates/{certificate_id}")
            return data.certificate
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_certificate(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "certificate": kwargs["certificate"],
            "private_key": kwargs["private_key"],
        }
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("POST", "/certificates", json=payload)

    async def create_managed_certificate(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "type": "managed",
        }
        if "domain_names" in kwargs:
            payload["domain_names"] = kwargs["domain_names"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("POST", "/certificates", json=payload)

    async def update_certificate(self, certificate: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/certificates/{_id(certificate)}", json=payload)

    async def delete_certificate(self, certificate: Any) -> Any:
        return await self._request("DELETE", f"/certificates/{_id(certificate)}")

    # ── Placement Groups ─────────────────────────────────────

    async def get_placement_groups(self) -> list:
        return await self._get_all("/placement_groups", "placement_groups")

    async def get_placement_group_by_id(self, placement_group_id: int) -> Any:
        try:
            data = await self._request("GET", f"/placement_groups/{placement_group_id}")
            return data.placement_group
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise

    async def create_placement_group(self, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {
            "name": kwargs["name"],
            "type": kwargs["type"],
        }
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("POST", "/placement_groups", json=payload)

    async def update_placement_group(self, placement_group: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "labels" in kwargs:
            payload["labels"] = kwargs["labels"]
        return await self._request("PUT", f"/placement_groups/{_id(placement_group)}", json=payload)

    async def delete_placement_group(self, placement_group: Any) -> Any:
        return await self._request("DELETE", f"/placement_groups/{_id(placement_group)}")

    # ── Locations ────────────────────────────────────────────

    async def get_locations(self) -> list:
        return await self._get_all("/locations", "locations")

    async def get_location_by_id(self, location_id: int) -> Any:
        try:
            data = await self._request("GET", f"/locations/{location_id}")
            return data.location
        except HetznerAPIError as e:
            if e.status == 404:
                return None
            raise
