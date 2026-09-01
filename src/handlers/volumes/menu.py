from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.VOLUME, task=TaskType.MENU), IgnoreStateFilter())
async def volumes(callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict):
    volumes = await hetzner.get_volumes()
    update = await callback_query.message.edit(text=Dialogs.VOLUMES_MENU, reply_markup=BotKB.volumes_menu(volumes=volumes))
    return await UserMessage.clear(update, keep_current=True)
