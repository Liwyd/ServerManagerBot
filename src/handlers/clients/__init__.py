from eiogram import Router

from . import create, info, menu, update


def setup_clients_handlers():
    router = Router()
    router.include_router(menu.router)
    router.include_router(create.router)
    router.include_router(update.router)
    router.include_router(info.router)
    return router
