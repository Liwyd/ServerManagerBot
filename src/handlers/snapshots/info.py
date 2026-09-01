from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.SNAPSHOT, task=TaskType.INFO), IgnoreStateFilter())
async def snapshots_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    snapshot = await hetzner.get_image_by_id(int(callback_data.target))
    if not snapshot:
        return await callback_query.message.edit(text=Dialogs.SNAPSHOTS_NOT_FOUND)
    update = await callback_query.message.edit(
        text=Dialogs.SNAPSHOTS_INFO.format(
            name=snapshot.name or snapshot.description or "No Name",
            status=snapshot.status,
            size=round(snapshot.image_size, 3) if snapshot.image_size else "Unknown",
            created=snapshot.created.strftime("%Y-%m-%d"),
            created_day=(datetime.now(timezone.utc) - snapshot.created).days,
        ),
        reply_markup=BotKB.snapshots_update(snapshot=snapshot),
    )
    return await UserMessage.clear(update, keep_current=True)
