from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class FirewallCreateForm(StateGroup):
    remark = State()


@router.callback_query(BotCB.filter(area=AreaType.FIREWALL, task=TaskType.CREATE))
async def firewalls_create(
    callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, state: StateManager, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=FirewallCreateForm.remark)
    return await callback_query.message.edit(text=Dialogs.FIREWALLS_ENTER_REMARK, reply_markup=BotKB.firewalls_back())


@router.message(StateFilter(FirewallCreateForm.remark), Text())
async def remark_handler(
    message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, state_data: dict, __: ShouldBeOwner
):
    try:
        response = await hetzner.create_firewall(name=message.text)
    except Exception:
        return await message.answer(text=Dialogs.FIREWALLS_CREATE_FAILED)
    if not response:
        return await message.answer(text=Dialogs.FIREWALLS_CREATE_FAILED)
    await state.clear_state(db=db)
    update = await message.answer(
        text=Dialogs.FIREWALLS_CREATE_SUCCESS, reply_markup=BotKB.firewalls_back(id=response.firewall.id)
    )
    return await UserMessage.clear(update)
