from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.SNAPSHOT, task=TaskType.MENU), IgnoreStateFilter())
async def snapshots_menu(
    callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict
):
    snapshots = await hetzner.get_images(type="snapshot")
    update = await callback_query.message.edit(
        text=Dialogs.SNAPSHOTS_MENU, reply_markup=BotKB.snapshots_menu(snapshots=snapshots)
    )
    return await UserMessage.clear(update, keep_current=True)
