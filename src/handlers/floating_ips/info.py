from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.FLOATING_IP, task=TaskType.INFO), IgnoreStateFilter())
async def floating_ips_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    floating_ip = await hetzner.get_floating_ip_by_id(int(callback_data.target))
    if not floating_ip:
        return await callback_query.message.edit(text=Dialogs.FLOATING_IPS_NOT_FOUND)
    server_name = "No"
    if floating_ip.server_id:
        server = await hetzner.get_server_by_id(floating_ip.server_id)
        if server:
            server_name = server.name
    update = await callback_query.message.edit(
        text=Dialogs.FLOATING_IPS_INFO.format(
            ip=floating_ip.ip,
            description=floating_ip.description or "No Description",
            type=floating_ip.type,
            server=server_name,
            created=floating_ip.created.strftime("%Y-%m-%d"),
            created_day=(datetime.now(timezone.utc) - floating_ip.created).days,
        ),
        reply_markup=BotKB.floating_ips_update(floating_ip=floating_ip),
    )
    return await UserMessage.clear(update, keep_current=True)
