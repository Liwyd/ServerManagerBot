from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, UserMessage
from src.keys import AreaType, BotCB, BotKB, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner, ShouldBeOwner

router = Router()


class ServerCreateForm(StateGroup):
    remark = State()
    datacenter = State()
    plan = State()
    image = State()


@router.callback_query(BotCB.filter(area=AreaType.SERVER, task=TaskType.CREATE))
async def servers_create(
    callback_query: CallbackQuery, db: AsyncSession, state: StateManager, state_data: dict, __: ShouldBeOwner
):
    await state.upsert_context(db=db, state=ServerCreateForm.remark)
    return await callback_query.message.edit(text=Dialogs.SERVERS_ENTER_REMARK, reply_markup=BotKB.servers_back())


@router.message(StateFilter(ServerCreateForm.remark), Text())
async def remark_handler(message: Message, db: AsyncSession, state: StateManager, hetzner: GetHetzner, __: ShouldBeOwner):
    if len(message.text.split(" ")) > 1:
        update = await message.answer(text=Dialogs.SERVERS_REMARK_VALIDATION)
        return await UserMessage.add(update)
    datacenters = await hetzner.get_datacenters()
    if not datacenters:
        update = await message.answer(text=Dialogs.SERVERS_DATACENTERS_NOT_FOUND)
        return await UserMessage.add(update)
    await state.upsert_context(db=db, state=ServerCreateForm.datacenter, remark=message.text)
    update = await message.answer(
        text=Dialogs.SERVERS_SELECT_DATACENTER, reply_markup=BotKB.datacenters_select(datacenters=datacenters)
    )
    return await UserMessage.clear(update)


@router.callback_query(StateFilter(ServerCreateForm.datacenter), BotCB.filter(area=AreaType.SERVER, task=TaskType.CREATE))
async def datacenter_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    plans = await hetzner.get_server_types()
    if not plans:
        return await callback_query.answer(text=Dialogs.SERVERS_PLANS_NOT_FOUND, show_alert=True)
    plans.sort(key=lambda x: float(x.prices[0]["price_monthly"]["net"]))
    await state.upsert_context(db=db, state=ServerCreateForm.plan, datacenter_id=callback_data.target)
    return await callback_query.message.edit(text=Dialogs.SERVERS_SELECT_PLAN, reply_markup=BotKB.plans_select(plans=plans))


@router.callback_query(StateFilter(ServerCreateForm.plan), BotCB.filter(area=AreaType.SERVER, task=TaskType.CREATE))
async def plan_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    plan = await hetzner.get_server_type_by_id(int(callback_data.target))
    if not plan:
        return await callback_query.answer(text=Dialogs.SERVERS_PLANS_NOT_FOUND, show_alert=True)
    images = await hetzner.get_images(type=["system", "snapshot"], architecture=plan.architecture)
    if not images:
        return await callback_query.answer(text=Dialogs.SERVERS_IMAGES_NOT_FOUND, show_alert=True)
    images.sort(key=lambda x: x.name or x.description)
    images.sort(key=lambda x: x.type, reverse=True)
    await state.upsert_context(db=db, state=ServerCreateForm.image, plan_id=callback_data.target)
    return await callback_query.message.edit(
        text=Dialogs.SERVERS_SELECT_IMAGE, reply_markup=BotKB.images_select(images=images, task=TaskType.CREATE)
    )


@router.callback_query(StateFilter(ServerCreateForm.image), BotCB.filter(area=AreaType.SERVER, task=TaskType.CREATE))
async def image_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    hetzner: GetHetzner,
    __: ShouldBeOwner,
):
    image = await hetzner.get_image_by_id(int(callback_data.target))
    if not image:
        return await callback_query.answer(text=Dialogs.SERVERS_IMAGES_NOT_FOUND, show_alert=True)
    server_type = await hetzner.get_server_type_by_id(state_data["plan_id"])
    if not server_type:
        return await callback_query.answer(text=Dialogs.SERVERS_PLANS_NOT_FOUND, show_alert=True)
    datacenter = await hetzner.get_datacenter_by_id(state_data["datacenter_id"])
    if not datacenter:
        return await callback_query.answer(text=Dialogs.SERVERS_DATACENTERS_NOT_FOUND, show_alert=True)

    await callback_query.answer(text=Dialogs.ACTIONS_WAITING)

    try:
        response = await hetzner.create_server(
            name=state_data["remark"],
            datacenter=datacenter,
            server_type=server_type,
            image=image,
        )
    except Exception as e:
        return await callback_query.answer(text=f"{Dialogs.SERVERS_CREATION_FAILED}\n{e}", show_alert=True)

    if not response or not response.server:
        return await callback_query.answer(text=Dialogs.SERVERS_CREATION_FAILED, show_alert=True)

    await state.clear_state(db=db)
    update = await callback_query.message.answer(
        text=Dialogs.SERVERS_CREATION_SUCCESS, reply_markup=BotKB.servers_back(id=response.server.id)
    )
    return await UserMessage.clear(update)
