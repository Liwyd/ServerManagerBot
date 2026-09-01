from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import AsyncSession, User, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.SERVER, task=TaskType.MENU), IgnoreStateFilter())
async def servers_menu(
    callback_query: CallbackQuery, hetzner: GetHetzner, _: ClearState, db: AsyncSession, dbuser: User, state_data: dict
):
    all_servers = await hetzner.get_servers()
    if not dbuser.is_owner:
        all_servers = [server for server in all_servers if server.id in dbuser.get_server_ids(int(state_data.get("client_id")))]
    update = await callback_query.message.edit(text=Dialogs.SERVERS_MENU, reply_markup=BotKB.servers_menu(servers=all_servers))
    return await UserMessage.clear(update, keep_current=True)
