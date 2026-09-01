from eiogram import Router
from eiogram.filters import StateFilter, Text
from eiogram.state import State, StateGroup, StateManager
from eiogram.types import CallbackQuery, Message

from src.db import AsyncSession, ServerAccess, User, UserMessage
from src.keys import AreaType, BotCB, BotKB, StepType, TaskType
from src.lang import Dialogs
from src.utils.depends import GetHetzner

router = Router()


class ServerUpdateForm(StateGroup):
    approval = State()
    image = State()
    ip = State()
    input = State()
    upgrade = State()


def check_access(dbuser: User, server_id: int, client_id: int) -> bool:
    if dbuser.is_owner:
        return True
    return server_id in dbuser.get_server_ids(client_id)


@router.callback_query(BotCB.filter(area=AreaType.SERVER, task=TaskType.UPDATE))
async def servers_update(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    dbuser: User,
    state_data: dict,
):
    kb = BotKB.servers_back(id=callback_data.target)
    server = await hetzner.get_server_by_id(int(callback_data.target))
    if not server:
        return await callback_query.message.edit(text=Dialogs.SERVERS_NOT_FOUND, reply_markup=kb)

    client_id = state_data.get("client_id")
    if client_id:
        if not check_access(dbuser, server.id, int(client_id)):
            return await callback_query.answer("Access Denied", show_alert=True)

    _state = ServerUpdateForm.input
    match callback_data.step:
        case (
            StepType.SERVERS_POWER_OFF
            | StepType.SERVERS_POWER_ON
            | StepType.SERVERS_RESET_PASSWORD
            | StepType.SERVERS_RESET
            | StepType.SERVERS_REBOOT
            | StepType.SERVERS_REMOVE
            | StepType.SERVERS_CREATE_SNAPSHOT
            | StepType.SERVERS_UNASSIGN_IPV4
            | StepType.SERVERS_UNASSIGN_IPV6
        ):
            text = Dialogs.ACTIONS_CONFIRM
            _state = ServerUpdateForm.approval
            kb = BotKB.approval(area=AreaType.SERVER, task=TaskType.UPDATE)
        case StepType.SERVERS_ASSIGN_IPV4 | StepType.SERVERS_ASSIGN_IPV6:
            ip_type = "ipv4" if callback_data.step == StepType.SERVERS_ASSIGN_IPV4 else "ipv6"
            if ip_type == "ipv4" and server.public_net.primary_ipv4:
                return await callback_query.answer(text=Dialogs.SERVERS_ASSIGN_UNASSIGN_IPV4, show_alert=True)
            if ip_type == "ipv6" and server.public_net.primary_ipv6:
                return await callback_query.answer(text=Dialogs.SERVERS_ASSIGN_UNASSIGN_IPV6, show_alert=True)
            primary_ips = await hetzner.get_primary_ips()
            if not primary_ips:
                return await callback_query.answer(text=Dialogs.SERVERS_PRIMARY_IPS_NOT_FOUND, show_alert=True)
            filtered_ips = [ip for ip in primary_ips if not ip.assignee_id and ip.type == ip_type]
            if not filtered_ips:
                return await callback_query.answer(text=Dialogs.SERVERS_PRIMARY_IPS_NOT_FOUND, show_alert=True)
            text = Dialogs.SERVERS_ASSIGN_SELECT
            _state = ServerUpdateForm.ip
            kb = BotKB.servers_primary_ips_select(primary_ips=filtered_ips)
        case StepType.SERVERS_REBUILD:
            text = Dialogs.SERVERS_REBUILD_CONFIRM
            _state = ServerUpdateForm.image
            images = await hetzner.get_images(type=["system", "snapshot"], architecture=server.image.architecture)
            if not images:
                return await callback_query.answer(text=Dialogs.SERVERS_IMAGES_NOT_FOUND, show_alert=True)
            images.sort(key=lambda x: x.name or x.description)
            images.sort(key=lambda x: x.type, reverse=True)
            kb = BotKB.images_select(images=images, task=TaskType.UPDATE, target=callback_data.target)
        case StepType.SERVERS_DEL_SNAPSHOT:
            text = Dialogs.SERVERS_SNAPSHOT_DELETE_CONFIRM
            _state = ServerUpdateForm.image
            images = await hetzner.get_images(type="snapshot")
            if not images:
                return await callback_query.answer(text=Dialogs.SERVERS_SNAPSHOT_NOT_FOUND, show_alert=True)
            images = [img for img in images if img.created_from and img.created_from.id == int(callback_data.target)]
            if not images:
                return await callback_query.answer(text=Dialogs.SERVERS_SNAPSHOT_NOT_FOUND, show_alert=True)
            kb = BotKB.images_select(images=images, task=TaskType.UPDATE, target=int(callback_data.target))
        case StepType.SERVERS_REMARK:
            text = Dialogs.SERVERS_ENTER_REMARK
        case StepType.SERVERS_UPGRADE:
            server_types = await hetzner.get_server_types()
            current_type = server.server_type
            upgrade_plans = [
                st
                for st in server_types
                if st.architecture == current_type.architecture
                and st.id != current_type.id
                and (st.memory >= current_type.memory or st.cores >= current_type.cores or st.disk >= current_type.disk)
            ]
            if not upgrade_plans:
                return await callback_query.answer(text=Dialogs.SERVERS_UPGRADE_NOT_FOUND, show_alert=True)
            upgrade_plans.sort(key=lambda x: (x.memory, x.cores, x.disk))
            text = Dialogs.SERVERS_UPGRADE_SELECT.format(
                current_plan=(
                    f"{current_type.name} [{current_type.memory}GB RAM, {current_type.cores} CPU, {current_type.disk}GB Disk]"
                )
            )
            _state = ServerUpdateForm.upgrade
            kb = BotKB.upgrade_plans_select(plans=upgrade_plans, server_id=server.id)
        case StepType.SERVERS_ACCESS_GRANT:
            if not dbuser.is_owner:
                return await callback_query.answer("Access Denied", show_alert=True)
            text = Dialogs.SERVERS_ACCESS_GRANT_PROMPT
        case StepType.SERVERS_ACCESS_REVOKE:
            if not dbuser.is_owner:
                return await callback_query.answer("Access Denied", show_alert=True)
            text = Dialogs.SERVERS_ACCESS_REVOKE_PROMPT
        case StepType.SERVERS_ACCESS_LIST:
            if not dbuser.is_owner:
                return await callback_query.answer("Access Denied", show_alert=True)
            server_id = int(callback_data.target)
            accesses = await ServerAccess.get_all_by_server(db, int(state_data.get("client_id")), server_id)
            if not accesses:
                list_text = "No access granted."
            else:
                list_text = "\n".join([f"• <code>{a.user_id}</code>" for a in accesses])
            return await callback_query.message.edit(
                text=Dialogs.SERVERS_ACCESS_LIST.format(list=list_text), reply_markup=BotKB.servers_back(server_id)
            )

        case _:
            return await callback_query.answer(text="Invalid step!", show_alert=True)
    await state.upsert_context(db=db, state=_state, step=callback_data.step, target=callback_data.target)
    return await callback_query.message.edit(text=text, reply_markup=kb)


@router.callback_query(StateFilter(ServerUpdateForm.image), BotCB.filter(area=AreaType.SERVER, task=TaskType.UPDATE))
async def select_image_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    dbuser: User,
    state_data: dict,
    hetzner: GetHetzner,
):
    server = await hetzner.get_server_by_id(int(state_data["target"]))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)

    client_id = state_data.get("client_id")
    if client_id:
        if not check_access(dbuser, server.id, int(client_id)):
            return await callback_query.answer("Access Denied", show_alert=True)

    await state.upsert_context(db=db, state=ServerUpdateForm.approval, image_id=callback_data.target)
    return await callback_query.message.edit(
        text=Dialogs.ACTIONS_CONFIRM,
        reply_markup=BotKB.approval(area=AreaType.SERVER, task=TaskType.UPDATE),
    )


@router.message(StateFilter(ServerUpdateForm.input), Text())
async def input_handler(
    message: Message, state: StateManager, db: AsyncSession, state_data: dict, hetzner: GetHetzner, dbuser: User
):
    server = await hetzner.get_server_by_id(int(state_data["target"]))
    if not server:
        update = await message.answer(text=Dialogs.SERVERS_NOT_FOUND, reply_markup=BotKB.servers_back())
        return await UserMessage.add(update)

    client_id = state_data.get("client_id")
    if client_id:
        if not check_access(dbuser, server.id, int(client_id)):
            update = await message.answer("Access Denied")
            return await UserMessage.add(update)

    match state_data["step"]:
        case StepType.SERVERS_REMARK:
            if len(message.text.split(" ")) > 1:
                update = await message.answer(text=Dialogs.SERVERS_REMARK_VALIDATION)
                return await UserMessage.add(update)
            await hetzner.update_server(server, name=message.text)
        case StepType.SERVERS_ACCESS_GRANT:
            if not client_id:
                update = await message.answer("Client ID missing from state.", reply_markup=BotKB.home_back())
                return await UserMessage.clear(update)

            if not message.text.isdigit():
                update = await message.answer("Invalid User ID. Please enter a number.")
                return await UserMessage.add(update)

            user_id = int(message.text)
            user = await User.get_by_id(db, user_id)
            if not user:
                update = await message.answer("User not found in database. The user must start the bot first.")
                return await UserMessage.add(update)

            existing = await ServerAccess.get_all_by_server(db, int(client_id), server.id)
            if any(a.user_id == user_id for a in existing):
                update = await message.answer(Dialogs.SERVERS_ACCESS_ALREADY_EXISTS.format(chat_id=user_id))
                return await UserMessage.add(update)
            else:
                await ServerAccess.create(db, client_id=int(client_id), server_id=server.id, user_id=user_id)
                update = await message.answer(Dialogs.SERVERS_ACCESS_GRANTED.format(chat_id=user_id))
                return await UserMessage.add(update)
        case StepType.SERVERS_ACCESS_REVOKE:
            if not client_id:
                update = await message.answer("Client ID missing from state.", reply_markup=BotKB.home_back())
                return await UserMessage.clear(update)
            if not message.text.isdigit():
                update = await message.answer("Invalid User ID.")
                return await UserMessage.add(update)
            user_id = int(message.text)
            existing = await ServerAccess.get_all_by_server(db, int(client_id), server.id)
            if not any(a.user_id == user_id for a in existing):
                update = await message.answer(Dialogs.SERVERS_ACCESS_NOT_FOUND.format(chat_id=user_id))
                return await UserMessage.add(update)
            else:
                await ServerAccess.delete(db, int(client_id), server.id, user_id)
                update = await message.answer(Dialogs.SERVERS_ACCESS_REVOKED.format(chat_id=user_id))
                return await UserMessage.add(update)

    await state.clear_state(db=db)
    update = await message.answer(text=Dialogs.ACTIONS_SUCCESS, reply_markup=BotKB.servers_back(server.id))
    return await UserMessage.clear(update)


@router.callback_query(StateFilter(ServerUpdateForm.ip), BotCB.filter(area=AreaType.SERVER, task=TaskType.UPDATE))
async def select_ip_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    dbuser: User,
):
    primary_ip = await hetzner.get_primary_ip_by_id(int(callback_data.target))
    if not primary_ip:
        return await callback_query.message.edit(text=Dialogs.SERVERS_PRIMARY_IPS_NOT_FOUND, reply_markup=BotKB.home_back())
    server = await hetzner.get_server_by_id(int(state_data["target"]))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)

    client_id = state_data.get("client_id")
    if client_id:
        if not check_access(dbuser, server.id, int(client_id)):
            return await callback_query.answer("Access Denied", show_alert=True)

    await callback_query.message.edit(text=Dialogs.ACTIONS_WAITING)
    if server.status != "off":
        await hetzner.power_off_server(server)
    await hetzner.assign_primary_ip(primary_ip, assignee_id=server.id, assignee_type="server")
    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.ACTIONS_SUCCESS, reply_markup=BotKB.servers_back(server.id))


@router.callback_query(StateFilter(ServerUpdateForm.upgrade), BotCB.filter(area=AreaType.SERVER, task=TaskType.UPDATE))
async def select_upgrade_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    hetzner: GetHetzner,
    state_data: dict,
    dbuser: User,
):
    server_type = await hetzner.get_server_type_by_id(int(callback_data.target))
    if not server_type:
        return await callback_query.answer(text=Dialogs.SERVERS_UPGRADE_NOT_FOUND, show_alert=True)
    server = await hetzner.get_server_by_id(int(state_data["target"]))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)

    client_id = state_data.get("client_id")
    if client_id:
        if not check_access(dbuser, server.id, int(client_id)):
            return await callback_query.answer("Access Denied", show_alert=True)

    if server.status != "off":
        return await callback_query.answer(text=Dialogs.SERVERS_SHOULD_BE_OFF, show_alert=True)
    await callback_query.message.edit(text=Dialogs.ACTIONS_WAITING)
    await hetzner.change_server_type(server, server_type=server_type, upgrade_disk=True)
    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.SERVERS_UPGRADE_SUCCESS, reply_markup=BotKB.servers_back(server.id))


@router.callback_query(StateFilter(ServerUpdateForm.approval), BotCB.filter(area=AreaType.SERVER, task=TaskType.UPDATE))
async def approval_handler(
    callback_query: CallbackQuery,
    callback_data: BotCB,
    db: AsyncSession,
    state: StateManager,
    state_data: dict,
    hetzner: GetHetzner,
    dbuser: User,
):
    if not callback_data.is_approve:
        return await callback_query.message.edit(text=Dialogs.ACTIONS_CANCELLED, reply_markup=BotKB.servers_back())

    server = await hetzner.get_server_by_id(int(state_data["target"]))
    if not server:
        return await callback_query.answer(text=Dialogs.SERVERS_NOT_FOUND, show_alert=True)

    client_id = state_data.get("client_id")
    if client_id:
        if not check_access(dbuser, server.id, int(client_id)):
            return await callback_query.answer("Access Denied", show_alert=True)

    kb = BotKB.servers_back(id=server.id)
    match state_data["step"]:
        case StepType.SERVERS_UNASSIGN_IPV4:
            await callback_query.message.edit(text=Dialogs.ACTIONS_WAITING)
            if server.status != "off":
                await hetzner.power_off_server(server)
            if server.public_net.primary_ipv4:
                await hetzner.unassign_primary_ip(server.public_net.primary_ipv4)
        case StepType.SERVERS_UNASSIGN_IPV6:
            await callback_query.message.edit(text=Dialogs.ACTIONS_WAITING)
            if server.status != "off":
                await hetzner.power_off_server(server)
            if server.public_net.primary_ipv6:
                await hetzner.unassign_primary_ip(server.public_net.primary_ipv6)
        case StepType.SERVERS_POWER_OFF:
            await hetzner.power_off_server(server)
        case StepType.SERVERS_POWER_ON:
            await hetzner.power_on_server(server)
        case StepType.SERVERS_RESET_PASSWORD:
            response = await hetzner.reset_server_password(server)
            await callback_query.message.answer(
                text=Dialogs.SERVERS_PASSWORD_RESET_SUCCESS.format(password=response.root_password),
            )
        case StepType.SERVERS_RESET:
            await hetzner.reset_server(server)
        case StepType.SERVERS_REBOOT:
            await hetzner.reboot_server(server)
        case StepType.SERVERS_CREATE_SNAPSHOT:
            await hetzner.create_server_image(server, type="snapshot")
        case StepType.SERVERS_REMOVE:
            await hetzner.delete_server(server)
            kb = BotKB.servers_back()
        case StepType.SERVERS_REBUILD:
            image = await hetzner.get_image_by_id(int(state_data["image_id"]))
            if not image:
                return await callback_query.message.edit(text=Dialogs.SERVERS_IMAGES_NOT_FOUND, reply_markup=BotKB.home_back())
            await hetzner.rebuild_server(server, image=image)
        case StepType.SERVERS_DEL_SNAPSHOT:
            image = await hetzner.get_image_by_id(int(state_data["image_id"]))
            if not image:
                return await callback_query.message.edit(
                    text=Dialogs.SERVERS_SNAPSHOT_NOT_FOUND, reply_markup=BotKB.home_back()
                )
            await hetzner.delete_image(image)

    await state.clear_state(db=db)
    return await callback_query.message.edit(text=Dialogs.ACTIONS_SUCCESS, reply_markup=kb)
