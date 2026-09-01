from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.SSH_KEY, task=TaskType.INFO), IgnoreStateFilter())
async def ssh_keys_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    ssh_key = await hetzner.get_ssh_key_by_id(int(callback_data.target))
    if not ssh_key:
        return await callback_query.message.edit(text=Dialogs.SSH_KEYS_NOT_FOUND)
    update = await callback_query.message.edit(
        text=Dialogs.SSH_KEYS_INFO.format(
            name=ssh_key.name or "No Name",
            fingerprint=ssh_key.fingerprint,
            created=ssh_key.created.strftime("%Y-%m-%d"),
            created_day=(datetime.now(timezone.utc) - ssh_key.created).days,
        ),
        reply_markup=BotKB.ssh_keys_update(ssh_key=ssh_key),
    )
    return await UserMessage.clear(update, keep_current=True)
