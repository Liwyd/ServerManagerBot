from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.FIREWALL, task=TaskType.INFO), IgnoreStateFilter())
async def firewalls_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    firewall = await hetzner.get_firewall_by_id(int(callback_data.target))
    if not firewall:
        return await callback_query.message.edit(text=Dialogs.FIREWALLS_NOT_FOUND)
    rules_count = len(firewall.rules) if firewall.rules else 0
    applied_to = len(firewall.applied_to) if firewall.applied_to else 0
    update = await callback_query.message.edit(
        text=Dialogs.FIREWALLS_INFO.format(
            name=firewall.name or "No Name",
            rules_count=rules_count,
            applied_to=applied_to,
            created=firewall.created.strftime("%Y-%m-%d"),
            created_day=(datetime.now(timezone.utc) - firewall.created).days,
        ),
        reply_markup=BotKB.firewalls_update(firewall=firewall),
    )
    return await UserMessage.clear(update, keep_current=True)
