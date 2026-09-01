from datetime import datetime, timezone

from eiogram import Router
from eiogram.filters import IgnoreStateFilter
from eiogram.types import CallbackQuery

from src.db import UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import ClearState, GetHetzner, ShouldBeOwner

router = Router()


@router.callback_query(BotCB.filter(area=AreaType.LOAD_BALANCER, task=TaskType.INFO), IgnoreStateFilter())
async def load_balancer_info(
    callback_query: CallbackQuery, callback_data: BotCB, hetzner: GetHetzner, _: ClearState, __: ShouldBeOwner
):
    load_balancer = await hetzner.get_load_balancer_by_id(int(callback_data.target))
    if not load_balancer:
        return await callback_query.message.edit(text=Dialogs.LOAD_BALANCERS_NOT_FOUND)

    ip = "N/A"
    if load_balancer.public_net and load_balancer.public_net.ipv4:
        ip = load_balancer.public_net.ipv4.ip

    location = "N/A"
    if load_balancer.location:
        location = f"{load_balancer.location.city} [{load_balancer.location.country}]"

    lb_type = "N/A"
    if load_balancer.load_balancer_type:
        lb_type = load_balancer.load_balancer_type.name

    targets_count = len(load_balancer.targets) if load_balancer.targets else 0

    update = await callback_query.message.edit(
        text=Dialogs.LOAD_BALANCERS_INFO.format(
            name=load_balancer.name or "No Name",
            type=lb_type,
            ip=ip,
            location=location,
            targets=targets_count,
            created=load_balancer.created.strftime("%Y-%m-%d") if load_balancer.created else "N/A",
            created_day=(datetime.now(timezone.utc) - load_balancer.created).days if load_balancer.created else 0,
        ),
        reply_markup=BotKB.load_balancers_update(load_balancer=load_balancer),
    )
    return await UserMessage.clear(update, keep_current=True)
