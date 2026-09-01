from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.NETWORK, task=TaskType.MENU), IgnoreStateFilter())
async def networks(callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict):
    networks = await hetzner.get_networks()
    update = await callback_query.message.edit(text=Dialogs.NETWORKS_MENU, reply_markup=BotKB.networks_menu(networks=networks))
    return await UserMessage.clear(update, keep_current=True)
