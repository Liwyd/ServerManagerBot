from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.PLACEMENT_GROUP, task=TaskType.INFO), IgnoreStateFilter())
async def placement_groups_info(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    hetzner: GetHetzner,
    _: ClearState,
    __: ShouldBeOwner,
):
    placement_group = await hetzner.get_placement_group_by_id(int(callback_data.target))
    if not placement_group:
        return await callback_query.message.edit(text=Dialogs.PLACEMENT_GROUPS_NOT_FOUND)
    update = await callback_query.message.edit(
        text=Dialogs.PLACEMENT_GROUPS_INFO.format(
            name=placement_group.name or "No Name",
            type=placement_group.type,
            created=placement_group.created.strftime("%Y-%m-%d"),
            created_day=(datetime.now(timezone.utc) - placement_group.created).days,
        ),
        reply_markup=BotKB.placement_groups_update(placement_group=placement_group),
    )
    return await UserMessage.clear(update, keep_current=True)
