from eiogram import Router

from . import base, fallback  # noqa
from . import admins  # noqa
from .certificates import setup_certificates_handlers
from .clients import setup_clients_handlers
from .firewalls import setup_firewalls_handlers
from .load_balancers import setup_load_balancers_handlers
from .middlewares import Middleware
from .networks import setup_networks_handlers
from .placement_groups import setup_placement_groups_handlers
from .primary_ips import setup_primary_ips_handlers
from .servers import setup_servers_handlers
from .snapshots import setup_snapshots_handlers
from .ssh_keys import setup_ssh_keys_handlers
from .volumes import setup_volumes_handlers


def setup_handlers() -> Router:
    router = Router()
    router.middleware.register(Middleware())
    router.include_router(base.router)
    router.include_router(admins.router)
    router.include_router(setup_clients_handlers())
    router.include_router(setup_servers_handlers())
    router.include_router(setup_snapshots_handlers())
    router.include_router(setup_primary_ips_handlers())
    router.include_router(setup_certificates_handlers())
    router.include_router(setup_volumes_handlers())
    router.include_router(setup_placement_groups_handlers())
    router.include_router(setup_firewalls_handlers())
    router.include_router(setup_ssh_keys_handlers())
    router.include_router(setup_networks_handlers())
    router.include_router(setup_load_balancers_handlers())
    return router


__all__ = ["setup_handlers"]
