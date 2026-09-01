from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.NETWORK, task=TaskType.INFO), IgnoreStateFilter())
async def networks_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    network = await hetzner.get_network_by_id(int(callback_data.target))
    if not network:
        return await callback_query.message.edit(text=Dialogs.NETWORKS_NOT_FOUND)

    if network.subnets:
        subnets = "\n".join(f" • <code>{s.ip_range}</code> ({s.type}/{s.network_zone})" for s in network.subnets)
    else:
        subnets = " • None"

    if network.routes:
        routes = "\n".join(f" • <code>{r.destination}</code> -> <code>{r.gateway}</code>" for r in network.routes)
    else:
        routes = " • None"

    update = await callback_query.message.edit(
        text=Dialogs.NETWORKS_INFO.format(
            name=network.name or "No Name",
            ip_range=network.ip_range,
            subnets=subnets,
            routes=routes,
            created=network.created.strftime("%Y-%m-%d"),
            created_day=(datetime.now(timezone.utc) - network.created).days,
        ),
        reply_markup=BotKB.networks_update(network=network),
    )
    return await UserMessage.clear(update, keep_current=True)
