from typing import List

from eiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from eiogram.utils.inline_builder import InlineKeyboardBuilder
from hcloud.certificates.client import BoundCertificate
from hcloud.datacenters import Datacenter
from hcloud.floating_ips.client import BoundFloatingIP
from hcloud.images import Image
from hcloud.load_balancers.client import BoundLoadBalancer
from hcloud.locations.client import BoundLocation
from hcloud.networks.client import BoundNetwork
from hcloud.placement_groups.client import BoundPlacementGroup
from hcloud.primary_ips import PrimaryIP
from hcloud.server_types import ServerType
from hcloud.servers import Server
from hcloud.ssh_keys import SSHKey
from hcloud.volumes.client import BoundVolume

from src.db import Client
from src.lang import Buttons

from .callback import AreaType, BotCB, StepType, TaskType


class BotKB:
    @classmethod
    def _back(cls, *, kb: InlineKeyboardBuilder, area: AreaType = AreaType.HOME, target: str | int = 0) -> InlineKeyboardMarkup:
        return kb.row(
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(
                    area=area,
                    task=TaskType.INFO if target != 0 else TaskType.MENU,
                    target=target,
                ).pack(),
            ),
            size=1,
        )

    @classmethod
    def home(cls, *, clients: List[Client], is_owner: bool = False) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for client in clients:
            kb.add(
                text=client.kb_remark,
                callback_data=BotCB(area=AreaType.CLIENT, task=TaskType.MENU, target=client.id).pack(),
            )
        kb.adjust(2)
        if is_owner:
            kb.row(
                InlineKeyboardButton(
                    text=Buttons.CLIENTS_CREATE, callback_data=BotCB(area=AreaType.CLIENT, task=TaskType.CREATE).pack()
                ),
                size=1,
            )
        kb.row(InlineKeyboardButton(text=Buttons.OWNER, url="https://t.me/ServerManagerBot"), size=1)
        return kb.as_markup()

    @classmethod
    def clients_menu(cls, id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()

        kb.add(
            text=Buttons.SERVERS,
            callback_data=BotCB(area=AreaType.SERVER, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.SNAPSHOTS,
            callback_data=BotCB(area=AreaType.SNAPSHOT, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.PRIMARY_IPS,
            callback_data=BotCB(area=AreaType.PRIMARY_IP, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.FLOATING_IPS,
            callback_data=BotCB(area=AreaType.FLOATING_IP, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.VOLUMES,
            callback_data=BotCB(area=AreaType.VOLUME, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.NETWORKS,
            callback_data=BotCB(area=AreaType.NETWORK, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.FIREWALLS,
            callback_data=BotCB(area=AreaType.FIREWALL, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.LOAD_BALANCERS,
            callback_data=BotCB(area=AreaType.LOAD_BALANCER, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.SSH_KEYS,
            callback_data=BotCB(area=AreaType.SSH_KEY, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.CERTIFICATES,
            callback_data=BotCB(area=AreaType.CERTIFICATE, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.PLACEMENT_GROUPS,
            callback_data=BotCB(area=AreaType.PLACEMENT_GROUP, task=TaskType.MENU, target=id).pack(),
        )
        kb.add(
            text=Buttons.CLIENTS_SETTING,
            callback_data=BotCB(area=AreaType.CLIENT, task=TaskType.INFO, target=id).pack(),
        )
        kb.adjust(2, 2, 2, 2, 2, 2)

        cls._back(kb=kb)

        return kb.as_markup()

    @classmethod
    def clients_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        kb.add(
            text=Buttons.BACK,
            callback_data=BotCB(area=AreaType.CLIENT, task=TaskType.MENU, target=id).pack(),
        )
        return kb.as_markup()

    @classmethod
    def clients_update(cls, id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        kb.add(
            text=Buttons.CLIENTS_CHANGE_REMARK,
            callback_data=BotCB(
                area=AreaType.CLIENT,
                task=TaskType.UPDATE,
                target=id,
                step=StepType.CHANGE_REMARK,
            ).pack(),
        )
        kb.add(
            text=Buttons.CLIENTS_CHANGE_SECRET,
            callback_data=BotCB(
                area=AreaType.CLIENT,
                task=TaskType.UPDATE,
                target=id,
                step=StepType.CHANGE_SECRET,
            ).pack(),
        )
        kb.add(
            text=Buttons.CLIENTS_REMOVE,
            callback_data=BotCB(
                area=AreaType.CLIENT,
                task=TaskType.UPDATE,
                target=id,
                step=StepType.REMOVE_CLIENT,
            ).pack(),
        )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.CLIENT, target=id)
        return kb.as_markup()

    # ── Certificates ─────────────────────────────────────────

    @classmethod
    def certificates_menu(cls, certificates: list) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for certificate in certificates:
            kb.add(
                text=f"{certificate.name} [{certificate.type}]",
                callback_data=BotCB(
                    area=AreaType.CERTIFICATE,
                    task=TaskType.INFO,
                    target=certificate.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.CERTIFICATES_CREATE,
                callback_data=BotCB(area=AreaType.CERTIFICATE, task=TaskType.CREATE, target="uploaded").pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.CERTIFICATES_CREATE_MANAGED,
                callback_data=BotCB(area=AreaType.CERTIFICATE, task=TaskType.CREATE, target="managed").pack(),
            ),
            size=2,
        )
        cls._back(kb=kb)
        return kb.as_markup()

    @classmethod
    def certificates_update(cls, certificate: BoundCertificate) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.CERTIFICATES_REMARK: StepType.CERTIFICATES_REMARK,
            Buttons.CERTIFICATES_DELETE: StepType.CERTIFICATES_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.CERTIFICATE,
                    task=TaskType.UPDATE,
                    step=step,
                    target=certificate.id,
                ).pack(),
            )
        kb.adjust(2)
        cls._back(kb=kb, area=AreaType.CERTIFICATE)
        return kb.as_markup()

    @classmethod
    def certificates_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.CERTIFICATE, target=id)
        return kb.as_markup()

    @classmethod
    def home_back(cls) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        kb.add(
            text=Buttons.BACK,
            callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
        )
        return kb.as_markup()

    @classmethod
    def approval(cls, area: AreaType, task: TaskType) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        kb.add(
            text=Buttons.YES,
            callback_data=BotCB(area=area, task=task, is_approve=True).pack(),
        )
        kb.add(
            text=Buttons.NO,
            callback_data=BotCB(area=area, task=task, is_approve=False).pack(),
        )
        cls._back(kb=kb, area=area)
        return kb.as_markup()

    @classmethod
    def servers_menu(cls, servers: List[Server]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        emoji = {"starting": "🟡", "stopping": "🔴", "running": "🟢", "off": "🔴"}
        for server in servers:
            kb.add(
                text=f"{emoji.get(server.status, '⚪️')} {server.name} [{server.status}]",
                callback_data=BotCB(area=AreaType.SERVER, task=TaskType.INFO, target=server.id).pack(),
            )
        kb.adjust(2)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.SERVERS_CREATE,
                callback_data=BotCB(area=AreaType.SERVER, task=TaskType.CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
            ),
            size=2,
        )
        return kb.as_markup()

    @classmethod
    def servers_update(cls, server: Server, is_owner: bool = False) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        update = {
            StepType.SERVERS_REMARK: Buttons.SERVERS_REMARK,
            StepType.SERVERS_POWER_OFF: Buttons.SERVERS_POWER_OFF,
            StepType.SERVERS_POWER_ON: Buttons.SERVERS_POWER_ON,
            StepType.SERVERS_REBOOT: Buttons.SERVERS_REBOOT,
            StepType.SERVERS_REBUILD: Buttons.SERVERS_REBUILD,
            StepType.SERVERS_RESET_PASSWORD: Buttons.SERVERS_RESET_PASSWORD,
            StepType.SERVERS_RESET: Buttons.SERVERS_RESET,
        }

        if is_owner:
            update.update(
                {
                    StepType.SERVERS_CREATE_SNAPSHOT: Buttons.SERVERS_CREATE_SNAPSHOT,
                    StepType.SERVERS_UPGRADE: Buttons.SERVERS_UPGRADE,
                    StepType.SERVERS_DEL_SNAPSHOT: Buttons.SERVERS_DEL_SNAPSHOT,
                    StepType.SERVERS_UNASSIGN_IPV4: Buttons.SERVERS_UNASSIGN_IPV4,
                    StepType.SERVERS_UNASSIGN_IPV6: Buttons.SERVERS_UNASSIGN_IPV6,
                    StepType.SERVERS_ASSIGN_IPV4: Buttons.SERVERS_ASSIGN_IPV4,
                    StepType.SERVERS_ASSIGN_IPV6: Buttons.SERVERS_ASSIGN_IPV6,
                    StepType.SERVERS_ACCESS_GRANT: Buttons.SERVERS_ACCESS_GRANT,
                    StepType.SERVERS_ACCESS_LIST: Buttons.SERVERS_ACCESS_LIST,
                    StepType.SERVERS_ACCESS_REVOKE: Buttons.SERVERS_ACCESS_REVOKE,
                    StepType.SERVERS_REMOVE: Buttons.SERVERS_REMOVE,
                }
            )

        for step, button in update.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.SERVER,
                    task=TaskType.UPDATE,
                    target=server.id,
                    step=step,
                ).pack(),
            )
        kb.adjust(2)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.SERVERS_REFRESH,
                callback_data=BotCB(area=AreaType.SERVER, task=TaskType.INFO, target=server.id).pack(),
            ),
            size=1,
        )
        cls._back(kb=kb, area=AreaType.SERVER)
        return kb.as_markup()

    @classmethod
    def servers_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.SERVER, target=id)
        return kb.as_markup()

    @classmethod
    def images_select(cls, images: List[Image], task: TaskType, target: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for image in images:
            kb.add(
                text=image.name or image.description,
                callback_data=BotCB(
                    area=AreaType.SERVER,
                    task=task,
                    target=image.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.SERVER, target=target)
        return kb.as_markup()

    @classmethod
    def datacenters_select(cls, datacenters: List[Datacenter]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for datacenter in datacenters:
            kb.add(
                text=f"{datacenter.location.city} [{datacenter.location.country}]",
                callback_data=BotCB(
                    area=AreaType.SERVER,
                    task=TaskType.CREATE,
                    target=datacenter.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.SERVER)
        return kb.as_markup()

    @classmethod
    def plans_select(cls, plans: List[ServerType]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for plan in plans:
            kb.add(
                text=f"{plan.name} [{plan.memory} RAM, {plan.cores} CPU, {float(plan.prices[0]['price_monthly']['net'])} EUR]",
                callback_data=BotCB(
                    area=AreaType.SERVER,
                    task=TaskType.CREATE,
                    target=plan.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.SERVER)
        return kb.as_markup()

    @classmethod
    def upgrade_plans_select(cls, plans: List[ServerType], server_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for plan in plans:
            kb.add(
                text=f"{plan.name} [{plan.memory} RAM, {plan.cores} CPU, {float(plan.prices[0]['price_monthly']['net'])} EUR]",
                callback_data=BotCB(
                    area=AreaType.SERVER,
                    task=TaskType.UPDATE,
                    target=plan.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.SERVER, target=server_id)
        return kb.as_markup()

    @classmethod
    def snapshots_menu(cls, snapshots: List[Image]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for snapshot in snapshots:
            kb.add(
                text=snapshot.name or snapshot.description,
                callback_data=BotCB(
                    area=AreaType.SNAPSHOT,
                    task=TaskType.INFO,
                    target=snapshot.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.SNAPSHOTS_CREATE,
                callback_data=BotCB(area=AreaType.SNAPSHOT, task=TaskType.CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
            ),
            size=2,
        )
        return kb.as_markup()

    @classmethod
    def snapshots_update(cls, snapshot: Image) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.SNAPSHOTS_REMARK: StepType.SNAPSHOTS_REMARK,
            Buttons.SNAPSHOTS_DELETE: StepType.SNAPSHOTS_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.SNAPSHOT,
                    task=TaskType.UPDATE,
                    step=step,
                    target=snapshot.id,
                ).pack(),
            )
        kb.adjust(2)
        cls._back(kb=kb, area=AreaType.SNAPSHOT)
        return kb.as_markup()

    @classmethod
    def snapshots_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.SNAPSHOT, target=id)
        return kb.as_markup()

    @classmethod
    def snapshots_select_server(
        cls, servers: List[Server], task: TaskType = TaskType.CREATE, target: int = 0
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for server in servers:
            kb.add(
                text=server.name,
                callback_data=BotCB(
                    area=AreaType.SNAPSHOT,
                    task=task,
                    target=server.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.SNAPSHOT, target=target)
        return kb.as_markup()

    @classmethod
    def primary_ips_menu(cls, primary_ips: List[PrimaryIP]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for primary_ip in primary_ips:
            kb.add(
                text=f"{primary_ip.name} [{primary_ip.ip}]",
                callback_data=BotCB(
                    area=AreaType.PRIMARY_IP,
                    task=TaskType.INFO,
                    target=primary_ip.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.PRIMARY_IPS_CREATE_IPV4,
                callback_data=BotCB(area=AreaType.PRIMARY_IP, task=TaskType.CREATE, target="ipv4").pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.PRIMARY_IPS_CREATE_IPV6,
                callback_data=BotCB(area=AreaType.PRIMARY_IP, task=TaskType.CREATE, target="ipv6").pack(),
            ),
            size=2,
        )
        cls._back(kb=kb)
        return kb.as_markup()

    @classmethod
    def primary_ips_update(cls, primary_ip: PrimaryIP) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.PRIMARY_IPS_REMARK: StepType.PRIMARY_IPS_REMARK,
            Buttons.PRIMARY_IPS_UNASSIGN: StepType.PRIMARY_IPS_UNASSIGN,
            Buttons.PRIMARY_IPS_ASSIGN: StepType.PRIMARY_IPS_ASSIGN,
            Buttons.PRIMARY_IPS_DELETE: StepType.PRIMARY_IPS_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.PRIMARY_IP,
                    task=TaskType.UPDATE,
                    step=step,
                    target=primary_ip.id,
                ).pack(),
            )
        kb.adjust(1, 2, 1)
        cls._back(kb=kb, area=AreaType.PRIMARY_IP)
        return kb.as_markup()

    @classmethod
    def primary_ips_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.PRIMARY_IP, target=id)
        return kb.as_markup()

    @classmethod
    def primary_ips_select_server(
        cls, servers: List[Server], task: TaskType = TaskType.UPDATE, target: int = 0
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for server in servers:
            kb.add(
                text=server.name,
                callback_data=BotCB(
                    area=AreaType.PRIMARY_IP,
                    task=task,
                    target=server.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.PRIMARY_IP, target=target)
        return kb.as_markup()

    @classmethod
    def primary_ips_select_datacenter(
        cls, datacenters: List[Datacenter], task: TaskType = TaskType.CREATE, target: int = 0
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for datacenter in datacenters:
            kb.add(
                text=f"{datacenter.location.city} [{datacenter.location.country}]",
                callback_data=BotCB(
                    area=AreaType.PRIMARY_IP,
                    task=task,
                    target=datacenter.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.PRIMARY_IP, target=target)
        return kb.as_markup()

    @classmethod
    def servers_primary_ips_select(cls, primary_ips: List[PrimaryIP]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for primary_ip in primary_ips:
            kb.add(
                text=f"{primary_ip.name} [{primary_ip.ip}]",
                callback_data=BotCB(
                    area=AreaType.SERVER,
                    task=TaskType.UPDATE,
                    target=primary_ip.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.SERVER)
        return kb.as_markup()

    # ── Floating IPs ──────────────────────────────────────────

    @classmethod
    def floating_ips_menu(cls, floating_ips: List[BoundFloatingIP]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for floating_ip in floating_ips:
            kb.add(
                text=f"{floating_ip.description or 'No Name'} [{floating_ip.ip}]",
                callback_data=BotCB(
                    area=AreaType.FLOATING_IP,
                    task=TaskType.INFO,
                    target=floating_ip.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.FLOATING_IPS_CREATE_IPV4,
                callback_data=BotCB(area=AreaType.FLOATING_IP, task=TaskType.CREATE, target="ipv4").pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.FLOATING_IPS_CREATE_IPV6,
                callback_data=BotCB(area=AreaType.FLOATING_IP, task=TaskType.CREATE, target="ipv6").pack(),
            ),
            size=2,
        )
        cls._back(kb=kb)
        return kb.as_markup()

    @classmethod
    def floating_ips_update(cls, floating_ip: BoundFloatingIP) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.FLOATING_IPS_REMARK: StepType.FLOATING_IPS_REMARK,
            Buttons.FLOATING_IPS_ASSIGN: StepType.FLOATING_IPS_ASSIGN,
            Buttons.FLOATING_IPS_UNASSIGN: StepType.FLOATING_IPS_UNASSIGN,
            Buttons.FLOATING_IPS_CHANGE_DNS: StepType.FLOATING_IPS_CHANGE_DNS,
            Buttons.FLOATING_IPS_DELETE: StepType.FLOATING_IPS_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.FLOATING_IP,
                    task=TaskType.UPDATE,
                    step=step,
                    target=floating_ip.id,
                ).pack(),
            )
        kb.adjust(1, 2, 2)
        cls._back(kb=kb, area=AreaType.FLOATING_IP)
        return kb.as_markup()

    @classmethod
    def floating_ips_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.FLOATING_IP, target=id)
        return kb.as_markup()

    @classmethod
    def floating_ips_select_location(cls, locations: list) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for location in locations:
            kb.add(
                text=f"{location.city} [{location.country}]",
                callback_data=BotCB(
                    area=AreaType.FLOATING_IP,
                    task=TaskType.CREATE,
                    target=location.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.FLOATING_IP)
        return kb.as_markup()

    @classmethod
    def floating_ips_select_server(
        cls, servers: List[Server], task: TaskType = TaskType.UPDATE, target: int = 0
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for server in servers:
            kb.add(
                text=server.name,
                callback_data=BotCB(
                    area=AreaType.FLOATING_IP,
                    task=task,
                    target=server.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.FLOATING_IP, target=target)
        return kb.as_markup()

    @classmethod
    def volumes_menu(cls, volumes: List[BoundVolume]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for volume in volumes:
            kb.add(
                text=f"{volume.name} [{volume.size}GB]",
                callback_data=BotCB(
                    area=AreaType.VOLUME,
                    task=TaskType.INFO,
                    target=volume.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.VOLUMES_CREATE,
                callback_data=BotCB(area=AreaType.VOLUME, task=TaskType.CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
            ),
            size=2,
        )
        return kb.as_markup()

    @classmethod
    def volumes_update(cls, volume: BoundVolume) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.VOLUMES_REMARK: StepType.VOLUMES_REMARK,
            Buttons.VOLUMES_RESIZE: StepType.VOLUMES_RESIZE,
        }
        if volume.server:
            updates[Buttons.VOLUMES_DETACH] = StepType.VOLUMES_DETACH
        else:
            updates[Buttons.VOLUMES_ATTACH] = StepType.VOLUMES_ATTACH
        updates[Buttons.VOLUMES_DELETE] = StepType.VOLUMES_DELETE
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.VOLUME,
                    task=TaskType.UPDATE,
                    step=step,
                    target=volume.id,
                ).pack(),
            )
        kb.adjust(1, 2, 1)
        cls._back(kb=kb, area=AreaType.VOLUME)
        return kb.as_markup()

    @classmethod
    def volumes_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.VOLUME, target=id)
        return kb.as_markup()

    @classmethod
    def volumes_select_location(cls, locations: List[BoundLocation], target: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for location in locations:
            kb.add(
                text=f"{location.city} [{location.country}]",
                callback_data=BotCB(
                    area=AreaType.VOLUME,
                    task=TaskType.CREATE,
                    target=location.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.VOLUME, target=target)
        return kb.as_markup()

    @classmethod
    def volumes_select_server(
        cls, servers: List[Server], task: TaskType = TaskType.UPDATE, target: int = 0
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for server in servers:
            kb.add(
                text=server.name,
                callback_data=BotCB(
                    area=AreaType.VOLUME,
                    task=task,
                    target=server.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.VOLUME, target=target)
        return kb.as_markup()

    # ── Placement Groups ───────────────────────────────────────

    @classmethod
    def placement_groups_menu(cls, placement_groups: List[BoundPlacementGroup]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for pg in placement_groups:
            kb.add(
                text=f"{pg.name} [{pg.type}]",
                callback_data=BotCB(
                    area=AreaType.PLACEMENT_GROUP,
                    task=TaskType.INFO,
                    target=pg.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.PLACEMENT_GROUPS_CREATE,
                callback_data=BotCB(area=AreaType.PLACEMENT_GROUP, task=TaskType.CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
            ),
            size=2,
        )
        return kb.as_markup()

    @classmethod
    def placement_groups_update(cls, placement_group: BoundPlacementGroup) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.PLACEMENT_GROUPS_REMARK: StepType.PLACEMENT_GROUPS_REMARK,
            Buttons.PLACEMENT_GROUPS_DELETE: StepType.PLACEMENT_GROUPS_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.PLACEMENT_GROUP,
                    task=TaskType.UPDATE,
                    step=step,
                    target=placement_group.id,
                ).pack(),
            )
        kb.adjust(2)
        cls._back(kb=kb, area=AreaType.PLACEMENT_GROUP)
        return kb.as_markup()

    @classmethod
    def placement_groups_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.PLACEMENT_GROUP, target=id)
        return kb.as_markup()

    # ── Firewalls ─────────────────────────────────────────────

    @classmethod
    def firewalls_menu(cls, firewalls: list) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for firewall in firewalls:
            kb.add(
                text=f"{firewall.name} [{len(firewall.rules) if firewall.rules else 0} rules]",
                callback_data=BotCB(
                    area=AreaType.FIREWALL,
                    task=TaskType.INFO,
                    target=firewall.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.FIREWALLS_CREATE,
                callback_data=BotCB(area=AreaType.FIREWALL, task=TaskType.CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
            ),
            size=2,
        )
        return kb.as_markup()

    @classmethod
    def firewalls_update(cls, firewall) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.FIREWALLS_REMARK: StepType.FIREWALLS_REMARK,
            Buttons.FIREWALLS_APPLY: StepType.FIREWALLS_APPLY,
            Buttons.FIREWALLS_REMOVE: StepType.FIREWALLS_REMOVE,
            Buttons.FIREWALLS_DELETE: StepType.FIREWALLS_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.FIREWALL,
                    task=TaskType.UPDATE,
                    step=step,
                    target=firewall.id,
                ).pack(),
            )
        kb.adjust(1, 2, 1)
        cls._back(kb=kb, area=AreaType.FIREWALL)
        return kb.as_markup()

    @classmethod
    def firewalls_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.FIREWALL, target=id)
        return kb.as_markup()

    @classmethod
    def firewalls_select_server(
        cls, servers: List[Server], step: StepType, task: TaskType = TaskType.UPDATE, target: int = 0
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for server in servers:
            kb.add(
                text=server.name,
                callback_data=BotCB(
                    area=AreaType.FIREWALL,
                    task=task,
                    step=step,
                    target=server.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.FIREWALL, target=target)
        return kb.as_markup()

    # ── SSH Keys ─────────────────────────────────────────────

    @classmethod
    def ssh_keys_menu(cls, ssh_keys: List[SSHKey]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for ssh_key in ssh_keys:
            kb.add(
                text=ssh_key.name,
                callback_data=BotCB(
                    area=AreaType.SSH_KEY,
                    task=TaskType.INFO,
                    target=ssh_key.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.SSH_KEYS_CREATE,
                callback_data=BotCB(area=AreaType.SSH_KEY, task=TaskType.CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
            ),
            size=2,
        )
        return kb.as_markup()

    @classmethod
    def ssh_keys_update(cls, ssh_key: SSHKey) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.SSH_KEYS_REMARK: StepType.SSH_KEYS_REMARK,
            Buttons.SSH_KEYS_DELETE: StepType.SSH_KEYS_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.SSH_KEY,
                    task=TaskType.UPDATE,
                    step=step,
                    target=ssh_key.id,
                ).pack(),
            )
        kb.adjust(2)
        cls._back(kb=kb, area=AreaType.SSH_KEY)
        return kb.as_markup()

    @classmethod
    def ssh_keys_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.SSH_KEY, target=id)
        return kb.as_markup()

    # ── Networks ─────────────────────────────────────────────

    @classmethod
    def networks_menu(cls, networks: list) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for network in networks:
            kb.add(
                text=f"{network.name} [{network.ip_range}]",
                callback_data=BotCB(
                    area=AreaType.NETWORK,
                    task=TaskType.INFO,
                    target=network.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.NETWORKS_CREATE,
                callback_data=BotCB(area=AreaType.NETWORK, task=TaskType.CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
            ),
            size=2,
        )
        return kb.as_markup()

    @classmethod
    def networks_update(cls, network: BoundNetwork) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.NETWORKS_REMARK: StepType.NETWORKS_REMARK,
            Buttons.NETWORKS_ADD_SUBNET: StepType.NETWORKS_ADD_SUBNET,
            Buttons.NETWORKS_DEL_SUBNET: StepType.NETWORKS_DEL_SUBNET,
            Buttons.NETWORKS_ADD_ROUTE: StepType.NETWORKS_ADD_ROUTE,
            Buttons.NETWORKS_DEL_ROUTE: StepType.NETWORKS_DEL_ROUTE,
            Buttons.NETWORKS_DELETE: StepType.NETWORKS_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.NETWORK,
                    task=TaskType.UPDATE,
                    step=step,
                    target=network.id,
                ).pack(),
            )
        kb.adjust(2, 2, 1, 1)
        cls._back(kb=kb, area=AreaType.NETWORK)
        return kb.as_markup()

    @classmethod
    def networks_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.NETWORK, target=id)
        return kb.as_markup()

    @classmethod
    def networks_select_subnet(cls, subnets: list, network_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for subnet in subnets:
            kb.add(
                text=f"{subnet.ip_range} ({subnet.type}/{subnet.network_zone})",
                callback_data=BotCB(
                    area=AreaType.NETWORK,
                    task=TaskType.UPDATE,
                    step=StepType.NETWORKS_DEL_SUBNET,
                    target=f"{subnet.ip_range}|{subnet.network_zone}",
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.NETWORK, target=network_id)
        return kb.as_markup()

    @classmethod
    def networks_select_route(cls, routes: list, network_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for route in routes:
            kb.add(
                text=f"{route.destination} -> {route.gateway}",
                callback_data=BotCB(
                    area=AreaType.NETWORK,
                    task=TaskType.UPDATE,
                    step=StepType.NETWORKS_DEL_ROUTE,
                    target=f"{route.destination}|{route.gateway}",
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.NETWORK, target=network_id)
        return kb.as_markup()

    @classmethod
    def networks_select_subnet_type(cls, network_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for subnet_type in ["cloud", "vswitch"]:
            kb.add(
                text=subnet_type,
                callback_data=BotCB(
                    area=AreaType.NETWORK,
                    task=TaskType.UPDATE,
                    step=StepType.NETWORKS_ADD_SUBNET,
                    target=network_id,
                ).pack(),
            )
        kb.adjust(2)
        cls._back(kb=kb, area=AreaType.NETWORK, target=network_id)
        return kb.as_markup()

    @classmethod
    def networks_select_network_zone(cls, network_id: int, subnet_ip_range: str, subnet_type: str) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for zone in ["eu-central", "us-east", "ap-south"]:
            kb.add(
                text=zone,
                callback_data=BotCB(
                    area=AreaType.NETWORK,
                    task=TaskType.UPDATE,
                    step=StepType.NETWORKS_ADD_SUBNET,
                    target=f"{subnet_ip_range}|{subnet_type}|{zone}",
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.NETWORK, target=network_id)
        return kb.as_markup()

    # ── Load Balancers ─────────────────────────────────────────

    @classmethod
    def load_balancers_menu(cls, load_balancers: List[BoundLoadBalancer]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for lb in load_balancers:
            kb.add(
                text=f"{lb.name} [{lb.load_balancer_type.name if lb.load_balancer_type else 'lb'}]",
                callback_data=BotCB(
                    area=AreaType.LOAD_BALANCER,
                    task=TaskType.INFO,
                    target=lb.id,
                ).pack(),
            )
        kb.adjust(1)
        kb.row(
            InlineKeyboardButton(
                text=Buttons.LOAD_BALANCERS_CREATE,
                callback_data=BotCB(area=AreaType.LOAD_BALANCER, task=TaskType.CREATE).pack(),
            ),
            InlineKeyboardButton(
                text=Buttons.BACK,
                callback_data=BotCB(area=AreaType.HOME, task=TaskType.MENU).pack(),
            ),
            size=2,
        )
        return kb.as_markup()

    @classmethod
    def load_balancers_update(cls, load_balancer: BoundLoadBalancer) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        updates = {
            Buttons.LOAD_BALANCERS_REMARK: StepType.LOAD_BALANCERS_REMARK,
            Buttons.LOAD_BALANCERS_ADD_TARGET: StepType.LOAD_BALANCERS_ADD_TARGET,
            Buttons.LOAD_BALANCERS_DEL_TARGET: StepType.LOAD_BALANCERS_DEL_TARGET,
            Buttons.LOAD_BALANCERS_DELETE: StepType.LOAD_BALANCERS_DELETE,
        }
        for button, step in updates.items():
            kb.add(
                text=button,
                callback_data=BotCB(
                    area=AreaType.LOAD_BALANCER,
                    task=TaskType.UPDATE,
                    step=step,
                    target=load_balancer.id,
                ).pack(),
            )
        kb.adjust(1, 2, 1)
        cls._back(kb=kb, area=AreaType.LOAD_BALANCER)
        return kb.as_markup()

    @classmethod
    def load_balancers_back(cls, id: int = 0) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        cls._back(kb=kb, area=AreaType.LOAD_BALANCER, target=id)
        return kb.as_markup()

    @classmethod
    def load_balancers_select_type(cls, lb_types: list) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for lb_type in lb_types:
            kb.add(
                text=f"{lb_type.name} [{lb_type.max_targets} targets]",
                callback_data=BotCB(
                    area=AreaType.LOAD_BALANCER,
                    task=TaskType.CREATE,
                    target=lb_type.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.LOAD_BALANCER)
        return kb.as_markup()

    @classmethod
    def load_balancers_select_location(cls, locations: list) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for location in locations:
            kb.add(
                text=f"{location.city} [{location.country}]",
                callback_data=BotCB(
                    area=AreaType.LOAD_BALANCER,
                    task=TaskType.CREATE,
                    target=location.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.LOAD_BALANCER)
        return kb.as_markup()

    @classmethod
    def load_balancers_select_server(
        cls, servers: List[Server], task: TaskType = TaskType.UPDATE, target: int = 0
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for server in servers:
            kb.add(
                text=server.name,
                callback_data=BotCB(
                    area=AreaType.LOAD_BALANCER,
                    task=task,
                    target=server.id,
                ).pack(),
            )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.LOAD_BALANCER, target=target)
        return kb.as_markup()

    @classmethod
    def load_balancers_select_target(cls, targets: list, lb_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        for target in targets:
            if target.type == "server" and target.server:
                kb.add(
                    text=target.server.name,
                    callback_data=BotCB(
                        area=AreaType.LOAD_BALANCER,
                        task=TaskType.UPDATE,
                        step=StepType.LOAD_BALANCERS_DEL_TARGET,
                        target=target.server.id,
                    ).pack(),
                )
        kb.adjust(1)
        cls._back(kb=kb, area=AreaType.LOAD_BALANCER, target=lb_id)
        return kb.as_markup()
