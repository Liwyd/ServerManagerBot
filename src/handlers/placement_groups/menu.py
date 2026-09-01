from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.PLACEMENT_GROUP, task=TaskType.MENU), IgnoreStateFilter())
async def placement_groups(
    callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict
):
    placement_groups = await hetzner.get_placement_groups()
    update = await callback_query.message.edit(
        text=Dialogs.PLACEMENT_GROUPS_MENU,
        reply_markup=BotKB.placement_groups_menu(placement_groups=placement_groups),
    )
    return await UserMessage.clear(update, keep_current=True)
