from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.FIREWALL, task=TaskType.MENU), IgnoreStateFilter())
async def firewalls(callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict):
    firewalls = await hetzner.get_firewalls()
    update = await callback_query.message.edit(
        text=Dialogs.FIREWALLS_MENU, reply_markup=BotKB.firewalls_menu(firewalls=firewalls)
    )
    return await UserMessage.clear(update, keep_current=True)
