from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.CERTIFICATE, task=TaskType.INFO), IgnoreStateFilter())
async def certificates_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    certificate = await hetzner.get_certificate_by_id(int(callback_data.target))
    if not certificate:
        return await callback_query.message.edit(text=Dialogs.CERTIFICATES_NOT_FOUND)
    domains = ", ".join(certificate.domain_names) if certificate.domain_names else "None"
    update = await callback_query.message.edit(
        text=Dialogs.CERTIFICATES_INFO.format(
            name=certificate.name or "No Name",
            type=certificate.type,
            domains=domains,
            created=certificate.created.strftime("%Y-%m-%d") if certificate.created else "Unknown",
            created_day=(datetime.now(timezone.utc) - certificate.created).days if certificate.created else 0,
        ),
        reply_markup=BotKB.certificates_update(certificate=certificate),
    )
    return await UserMessage.clear(update, keep_current=True)
