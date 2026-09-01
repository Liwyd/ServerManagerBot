from datetime import UTC, datetime

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.VOLUME, task=TaskType.INFO), IgnoreStateFilter())
async def volumes_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    volume = await hetzner.get_volume_by_id(int(callback_data.target))
    if not volume:
        return await callback_query.message.edit(text=Dialogs.VOLUMES_NOT_FOUND)
    location = volume.location.city if volume.location else "Unknown"
    server = volume.server.name if volume.server else "Not attached"
    update = await callback_query.message.edit(
        text=Dialogs.VOLUMES_INFO.format(
            name=volume.name or "No Name",
            size=volume.size,
            location=location,
            server=server,
            created=volume.created.strftime("%Y-%m-%d"),
            created_day=(datetime.now(UTC) - volume.created).days,
        ),
        reply_markup=BotKB.volumes_update(volume=volume),
    )
    return await UserMessage.clear(update, keep_current=True)
