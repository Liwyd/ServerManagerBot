from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class SSHKeyUpdateForm(StateGroup):
    approval = State()
    input = State()


@router.callback_query(BotCB.filter(area=AreaType.SSH_KEY, task=TaskType.UPDATE))
async def ssh_keys_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    kb = BotKB.ssh_keys_back(id=callback_data.target)
    ssh_key = await hetzner.get_ssh_key_by_id(int(callback_data.target))
    if not ssh_key:
        return await callback_query.message.edit(text=Dialogs.SSH_KEYS_NOT_FOUND, reply_markup=kb)
    match callback_data.step:
        case StepType.SSH_KEYS_DELETE:
            text = Dialogs.ACTIONS_CONFIRM
            _state = SSHKeyUpdateForm.approval
            kb = BotKB.approval(area=AreaType.SSH_KEY, task=TaskType.UPDATE)
        case StepType.SSH_KEYS_REMARK:
            text = Dialogs.SSH_KEYS_ENTER_REMARK
            _state = SSHKeyUpdateForm.input
        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)
    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.message(StateFilter(SSHKeyUpdateForm.input), Text())
async def input_handler(
    message: Message,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    ssh_key = await hetzner.get_ssh_key_by_id(int(state_data["target"]))
    if not ssh_key:
        return await message.answer(text=Dialogs.SSH_KEYS_NOT_FOUND)

    match state_data["step"]:
        case StepType.SSH_KEYS_REMARK:
            await hetzner.update_ssh_key(ssh_key, name=message.text)
        case _:
            return await message.answer(text="Invalid step!", reply_markup=BotKB.ssh_keys_back(id=ssh_key.id))

    await state.clear_state(db=db)
    return await message.answer(text=Dialogs.SSH_KEYS_UPDATE_SUCCESS, reply_markup=BotKB.ssh_keys_back(id=ssh_key.id))


@router.callback_query(StateFilter(SSHKeyUpdateForm.approval), BotCB.filter(area=AreaType.SSH_KEY, task=TaskType.UPDATE))
async def approval_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    __: ShouldBeOwner,
):
    if not callback_data.is_approve:
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.ssh_keys_back())

    ssh_key = await hetzner.get_ssh_key_by_id(int(state_data["target"]))
    if not ssh_key:
        return await callback_query.answer(text=Dialogs.SSH_KEYS_NOT_FOUND, show_alert=True)

    kb = BotKB.ssh_keys_back(id=ssh_key.id)
    match state_data["step"]:
        case StepType.SSH_KEYS_DELETE:
            await hetzner.delete_ssh_key(ssh_key)
            kb = BotKB.ssh_keys_back()

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.SSH_KEYS_UPDATE_SUCCESS, reply_markup=kb)
