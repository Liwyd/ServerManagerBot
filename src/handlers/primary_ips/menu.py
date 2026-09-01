from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.PRIMARY_IP, task=TaskType.MENU), IgnoreStateFilter())
async def primary_ips(callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict):
    primary_ips = await hetzner.get_primary_ips()
    update = await callback_query.message.edit(
        text=Dialogs.PRIMARY_IPS_MENU, reply_markup=BotKB.primary_ips_menu(primary_ips=primary_ips)
    )
    return await UserMessage.clear(update, keep_current=True)
