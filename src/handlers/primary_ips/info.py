from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.PRIMARY_IP, task=TaskType.INFO), IgnoreStateFilter())
async def primary_ips_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    primary_ip = await hetzner.get_primary_ip_by_id(int(callback_data.target))
    if not primary_ip:
        return await callback_query.message.edit(text=Dialogs.PRIMARY_IPS_NOT_FOUND)
    assignee = "No"
    assignee_id = "None"
    if primary_ip.assignee_id:
        server = await hetzner.get_server_by_id(primary_ip.assignee_id)
        if server:
            assignee = server.name
        assignee_id = primary_ip.assignee_id
    update = await callback_query.message.edit(
        text=Dialogs.PRIMARY_IPS_INFO.format(
            name=primary_ip.name or "No Name",
            ip=primary_ip.ip,
            assignee=assignee,
            assignee_id=assignee_id,
            created=primary_ip.created.strftime("%Y-%m-%d"),
            created_day=(datetime.now(timezone.utc) - primary_ip.created).days,
        ),
        reply_markup=BotKB.primary_ips_update(primary_ip=primary_ip),
    )
    return await UserMessage.clear(update, keep_current=True)
