from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.FLOATING_IP, task=TaskType.MENU), IgnoreStateFilter())
async def floating_ips(callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict):
    floating_ips = await hetzner.get_floating_ips()
    update = await callback_query.message.edit(
        text=Dialogs.FLOATING_IPS_MENU, reply_markup=BotKB.floating_ips_menu(floating_ips=floating_ips)
    )
    return await UserMessage.clear(update, keep_current=True)
