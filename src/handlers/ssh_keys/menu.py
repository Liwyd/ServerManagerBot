from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.SSH_KEY, task=TaskType.MENU), IgnoreStateFilter())
async def ssh_keys(callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner, state_data: dict):
    ssh_keys = await hetzner.get_ssh_keys()
    update = await callback_query.message.edit(text=Dialogs.SSH_KEYS_MENU, reply_markup=BotKB.ssh_keys_menu(ssh_keys=ssh_keys))
    return await UserMessage.clear(update, keep_current=True)
