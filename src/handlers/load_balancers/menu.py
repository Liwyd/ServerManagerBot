from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.MENU), IgnoreStateFilter())
async def load_balancers(
    callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict
):
    load_balancers = await hetzner.get_load_balancers()
    update = await callback_query.message.edit(
        text=Dialogs.LOAD_BALANCERS_MENU, reply_markup=BotKB.load_balancers_menu(load_balancers=load_balancers)
    )
    return await UserMessage.clear(update, keep_current=True)
