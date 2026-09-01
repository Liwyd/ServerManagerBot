from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class SSHKeyCreateForm(StateGroup):
    remark = State()
    public_key = State()


@router.callback_query(BotCB.filter(area=AreaType.SSH_KEY, task=TaskType.CREATE))
async def ssh_keys_create(
    callback_query: CallbackQuery, callback_data: BotCB, db: AsyncSession, state: StateManager, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=SSHKeyCreateForm.remark)
    return await callback_query.message.edit(text=Dialogs.SSH_KEYS_ENTER_REMARK, reply_markup=BotKB.ssh_keys_back())


@router.message(StateFilter(SSHKeyCreateForm.remark), Text())
async def remark_handler(message: Message, db: AsyncSession, state: StateManager, state_data: dict, __: ShouldBeOwner):
    await state.upsert_context(db=db, state=SSHKeyCreateForm.public_key, remark=message.text)
    update = await message.answer(text=Dialogs.SSH_KEYS_ENTER_PUBLIC_KEY)
    return await UserMessage.clear(update)


@router.message(StateFilter(SSHKeyCreateForm.public_key), Text())
async def public_key_handler(
    message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, state_data: dict, __: ShouldBeOwner
):
    try:
        response = await hetzner.create_ssh_key(name=state_data["remark"], public_key=message.text)
    except Exception:
        return await message.answer(text=Dialogs.SSH_KEYS_CREATE_FAILED)
    if not response:
        return await message.answer(text=Dialogs.SSH_KEYS_CREATE_FAILED)
    await state.clear_state(db=db)
    update = await message.answer(
        text=Dialogs.SSH_KEYS_CREATE_SUCCESS, reply_markup=BotKB.ssh_keys_back(id=response.ssh_key.id)
    )
    return await UserMessage.add(update)
