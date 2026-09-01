from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class NetworkCreateForm(StateGroup):
    remark = State()
    ip_range = State()


@router.callback_query(BotCB.filter(area=AreaType.NETWORK, task=TaskType.CREATE))
async def networks_create(
    callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, state: StateManager, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=NetworkCreateForm.remark)
    return await callback_query.message.edit(text=Dialogs.NETWORKS_ENTER_REMARK, reply_markup=BotKB.networks_back())


@router.message(StateFilter(NetworkCreateForm.remark), Text())
async def remark_handler(message: Message, db: AsyncSession, state: StateManager, state_data: dict, __: ShouldBeOwner):
    await state.upsert_context(db=db, state=NetworkCreateForm.ip_range, remark=message.text)
    update = await message.answer(text=Dialogs.NETWORKS_ENTER_IP_RANGE, reply_markup=BotKB.networks_back())
    return await UserMessage.clear(update)


@router.message(StateFilter(NetworkCreateForm.ip_range), Text())
async def ip_range_handler(
    message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, state_data: dict, __: ShouldBeOwner
):
    try:
        response = await hetzner.create_network(name=state_data["remark"], ip_range=message.text)
    except Exception:
        return await message.answer(text=Dialogs.NETWORKS_CREATE_FAILED)
    if not response:
        return await message.answer(text=Dialogs.NETWORKS_CREATE_FAILED)
    await state.clear_state(db=db)
    update = await message.answer(
        text=Dialogs.NETWORKS_CREATE_SUCCESS, reply_markup=BotKB.networks_back(id=response.network.id)
    )
    return await UserMessage.add(update)
