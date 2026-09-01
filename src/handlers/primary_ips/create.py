from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class PrimaryCreateForm(StateGroup):
    remark = State()
    datacenter = State()


@router.callback_query(BotCB.filter(area=AreaType.PRIMARY_IP, task=TaskType.CREATE))
async def primary_ips_create(
    callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, state: StateManager, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=PrimaryCreateForm.remark, ip_type=callback_data.target)
    return await callback_query.message.edit(text=Dialogs.PRIMARY_IPS_ENTER_REMARK, reply_markup=BotKB.primary_ips_back())


@router.message(StateFilter(PrimaryCreateForm.remark), Text())
async def remark_handler(
    message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, state_data: dict, __: ShouldBeOwner
):
    datacenters = await hetzner.get_datacenters()
    if not datacenters:
        update = await message.answer(text=Dialogs.PRIMARY_IPS_NO_DATACENTERS)
        return await UserMessage.add(update)
    await state.upsert_context(db=db, state=PrimaryCreateForm.datacenter, remark=message.text)
    update = await message.answer(
        text=Dialogs.PRIMARY_IPS_SELECT_DATACENTER, reply_markup=BotKB.primary_ips_select_datacenter(datacenters=datacenters)
    )
    return await UserMessage.clear(update)


@router.callback_query(StateFilter(PrimaryCreateForm.datacenter), BotCB.filter(area=AreaType.PRIMARY_IP, task=TaskType.CREATE))
async def select_datacenter(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    datacenter = await hetzner.get_datacenter_by_id(int(callback_data.target))
    if not datacenter:
        return await callback_query.answer(text=Dialogs.PRIMARY_IPS_NO_DATACENTERS, show_alert=True)
    try:
        response = await hetzner.create_primary_ip(
            name=state_data["remark"],
            auto_delete=True,
            type=state_data["ip_type"],
            assignee_type="server",
            datacenter=datacenter,
        )
    except Exception:
        return await callback_query.answer(text=Dialogs.PRIMARY_IPS_CREATE_FAILED, show_alert=True)
    if not response:
        return await callback_query.answer(text=Dialogs.PRIMARY_IPS_CREATE_FAILED, show_alert=True)
    await state.clear_state(db=db)
    update = await callback_query.message.edit(
        text=Dialogs.PRIMARY_IPS_CREATE_SUCCESS, reply_markup=BotKB.primary_ips_back(id=response.primary_ip.id)
    )
    return await UserMessage.add(update)
