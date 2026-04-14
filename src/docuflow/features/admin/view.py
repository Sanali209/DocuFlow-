import logging
from collections.abc import Callable
from typing import Any

from nicegui import ui

from docuflow.features.admin.system import AdminSystem
from docuflow.features.core.views import ViewInfo, ViewRegistry


def register_admin_view():
    """Register the admin view in the global registry."""
    ViewRegistry.register(
        ViewInfo(
            name="admin",
            label="Admin",
            icon="settings",
            render_fn=admin_view,
            dependencies=[AdminSystem],
            pass_system_provider=True,
            is_async=True,
        )
    )


logger = logging.getLogger("docuflow.admin.view")


# ────────────────────────────────────────────────────────────────
# H1+H3 FIX: All refreshables are at module-level (stable WS refs)
# H3 FIX:    .refresh() always passes admin_system explicitly
# ────────────────────────────────────────────────────────────────


@ui.refreshable
async def render_user_registry(system_provider: Callable) -> None:
    """Renders the Identity Registry list. Module-level for stable WebSocket slot."""
    try:
        admin_system = await system_provider(AdminSystem)
        users = admin_system.get_all_users()
        logger.debug(f"AdminView [USERS]: fetched count={len(users)}")

        if not users:
            ui.label("No users found in Identity Registry").classes("text-slate-500 italic p-4")
            return

        with ui.column().classes("w-full gap-2"):
            for u in users:
                is_root_admin = u.username.strip().lower() == "admin"
                with ui.row().classes(
                    "w-full items-center justify-between p-4 bg-white/5 "
                    "rounded-xl border border-white/5 hover:border-indigo-500/30 transition-all"
                ):
                    with ui.row().classes("items-center gap-4"):
                        ui.avatar(u.username[0].upper(), color="indigo").classes(
                            "text-xs font-bold"
                        )
                        with ui.column().classes("gap-0"):
                            ui.label(u.username).classes("text-slate-200 font-bold")
                            # H2 FIX: u.role already eagerly loaded via selectinload
                            role_name = u.role.name if u.role else "None"
                            ui.label(f"Role: {role_name}").classes("text-[10px] text-slate-400")

                    if not is_root_admin:

                        async def _remove(un=u.username):
                            fresh_system = await system_provider(AdminSystem)
                            fresh_system.delete_user(un)
                            await render_user_registry.refresh(system_provider)  # H3 FIX
                            ui.notify(f"User {un} deleted", color="warning")

                        ui.button(icon="delete", color="red", on_click=_remove).props("flat dense")

    except Exception as e:
        ui.label("Registry Offline...").classes("text-red-400 italic")
        logger.exception(f"render_user_registry failed: {e}")


@ui.refreshable
async def render_role_matrix(system_provider: Callable) -> None:
    """Renders the Permission Matrix. Module-level for stable WebSocket slot."""
    MODULES = [
        "bucket",
        "board",
        "chat",
        "workitems",
        "batching",
        "mat_stock",
        "consumables",
        "part_stock",
        "part_library",
        "scanner",
        "settings",
        "reports",
        "admin",
    ]
    try:
        admin_system = await system_provider(AdminSystem)
        roles = admin_system.get_all_roles()
        logger.debug(f"AdminView [ROLES]: fetched count={len(roles)}")

        if not roles:
            ui.label("No roles defined.").classes("text-slate-500 italic p-4")
            return

        with ui.column().classes("w-full gap-4"):
            for r in roles:
                is_admin_role = r.name.strip().lower() == "admin"
                border = "border-indigo-500/40" if is_admin_role else "border-white/5"
                with ui.column().classes(f"w-full p-6 bg-white/5 rounded-2xl border {border}"):
                    with ui.row().classes("w-full justify-between items-center mb-4"):
                        with ui.column().classes("gap-0"):
                            label_color = "text-indigo-400" if is_admin_role else "text-white"
                            ui.label(r.name).classes(f"text-xl font-bold {label_color}")
                            ui.label(f"Role ID: {r.id}").classes(
                                "text-[10px] text-slate-500 font-mono"
                            )

                        if not is_admin_role:

                            async def _del_role(rn=r.name):
                                fresh_system = await system_provider(AdminSystem)
                                fresh_system.delete_role(rn)
                                await render_role_matrix.refresh(system_provider)  # H3 FIX
                                ui.notify(f"Role {rn} deleted", color="warning")

                            ui.button(icon="delete", color="red", on_click=_del_role).props(
                                "flat dense"
                            )

                    with ui.row().classes("gap-2 flex-wrap"):
                        for mod in MODULES:
                            current_perms = r.permissions_list
                            module_perm = next(
                                (p for p in current_perms if p.startswith(f"{mod}:")), None
                            )
                            is_on = module_perm is not None
                            perm_type = module_perm.split(":")[1] if is_on else "none"

                            async def _toggle(m=mod, r_obj=r, active=is_on, mp=module_perm):
                                if r_obj.name.strip().lower() == "admin":
                                    return
                                remaining = [
                                    p for p in r_obj.permissions_list if not p.startswith(f"{m}:")
                                ]
                                if not active:
                                    remaining.append(f"{m}:read")
                                elif mp and "read" in mp:
                                    remaining.append(f"{m}:full")

                                fresh_system = await system_provider(AdminSystem)
                                fresh_system.upsert_role(r_obj.name, remaining)
                                await render_role_matrix.refresh(system_provider)  # H3 FIX

                            color = (
                                "emerald"
                                if perm_type == "full"
                                else "indigo"
                                if perm_type == "read"
                                else "slate-800"
                            )
                            ui.button(f"{mod}:{perm_type}", on_click=_toggle).classes(
                                f"text-[10px] uppercase font-bold rounded-lg px-3 py-1 "
                                f"bg-{color}-500/20 text-{color}-400 border border-{color}-500/30"
                            ).props("flat dense")

    except Exception as e:
        ui.label("Role Matrix Offline...").classes("text-red-400 italic")
        logger.exception(f"render_role_matrix failed: {e}")


@ui.refreshable
async def render_settings_form(
    system_provider: Callable,
    module: str,
    node_id: str | None,
    node_rows: list[dict],
) -> None:
    """Renders the dynamic settings form. Module-level for stable WebSocket slot."""
    try:
        from docuflow.domain.settings import registry

        admin_system = await system_provider(AdminSystem)

        # DEBUG: Log all registered modules
        all_modules = registry.get_all_modules()
        logger.debug(f"render_settings_form: module={module}, all_modules={all_modules}")

        schema = registry.get_schema(module)
        if not schema:
            logger.warning(f"No schema registered for module: {module}")
            ui.label(f"No schema registered for: {module}").classes("text-red-400")
            return

        scope_type = "global" if node_id is None else "local"
        fields = registry.get_fields_by_scope(module, scope_type)
        current = admin_system.get_node_settings(node_id or "global", module)

        logger.debug(
            f"render_settings_form: scope={scope_type}, fields_count={len(fields) if fields else 0}, current_keys={list(current.keys()) if current else []}"
        )

        with ui.column().classes("w-full mt-4 p-6 bg-white/5 rounded-2xl border border-white/10"):
            if not fields:
                ui.label(f"No {scope_type} settings defined for {module}.").classes(
                    "text-slate-500 italic text-sm"
                )
                return

            ui.label(f"{scope_type.upper()} SETTINGS: {module}").classes(
                "text-xs font-bold text-indigo-300/50 mb-4 uppercase tracking-widest"
            )
            for field_name in fields:
                fi = schema.model_fields[field_name]
                display_val = current.get(field_name, str(fi.default))
                with ui.row().classes("w-full items-center justify-between mb-4"):
                    with ui.column():
                        ui.label(field_name.replace("_", " ")).classes(
                            "text-slate-200 font-bold text-sm"
                        )
                        if fi.description:
                            ui.label(fi.description).classes("text-[10px] text-slate-500")

                    async def _push(e, f=field_name):
                        admin_system.update_node_setting(
                            node_id or "global", module, f, str(e.value)
                        )

                    if fi.annotation is bool:
                        ui.switch(value=str(display_val).lower() == "true", on_change=_push)
                    elif fi.annotation is int:
                        ui.number(value=int(display_val), on_change=_push).props(
                            "dark dense standout"
                        )
                    else:
                        ui.input(value=str(display_val), on_change=_push).props(
                            "dark dense standout"
                        )

    except Exception as e:
        ui.label("Syncing Property Grid...").classes("text-slate-500 italic")
        logger.exception(f"render_settings_form failed: {e}")


@ui.refreshable
async def render_notifications_form(system_provider: Callable) -> None:
    from sqlmodel import select

    from docuflow.domain.entities.production import NotificationTemplate

    try:
        admin_system = await system_provider(AdminSystem)
        tmpls = admin_system.session.exec(select(NotificationTemplate)).all()
        if not tmpls:
            ui.label("No Notification Templates defined.").classes("text-slate-500 italic p-4")
            return

        with ui.column().classes("w-full mt-4 gap-4"):
            for tmpl in tmpls:
                with ui.row().classes(
                    "w-full items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10"
                ):
                    with ui.column().classes("gap-1 flex-1"):
                        ui.label(tmpl.key).classes("text-lg font-bold text-indigo-400")

                        def update_text(e, t_obj=tmpl):
                            t_obj.text = e.value
                            admin_system.session.add(t_obj)
                            admin_system.session.commit()
                            ui.notify("Шаблон уведомления сохранен", color="positive")

                        # Use lazy binding via on_change
                        txt_input = (
                            ui.input(value=tmpl.text)
                            .props("dark standout rounded")
                            .classes("w-full text-slate-300")
                        )
                        txt_input.on("change", lambda e, t=tmpl: update_text(e, t))

                    with ui.column().classes("ml-8 items-end w-32"):

                        def update_toggle(e, t_obj=tmpl):
                            t_obj.enabled = e.value
                            admin_system.session.add(t_obj)
                            admin_system.session.commit()

                        ui.switch("Active", value=tmpl.enabled, on_change=update_toggle)
    except Exception as e:
        ui.label(f"Notif Error: {e}").classes("text-red-400")


@ui.refreshable
async def render_presets_form(system_provider: Callable) -> None:
    from sqlmodel import select

    from docuflow.domain.entities.production import ViewPreset

    try:
        admin_system = await system_provider(AdminSystem)
        # Only global presets
        presets = admin_system.session.exec(
            select(ViewPreset).where(ViewPreset.owner == "global")
        ).all()

        with ui.row().classes("w-full mt-4 gap-4 justify-between items-center"):
            ui.label("Глобальные Пресеты (View Presets)").classes("text-xl font-bold text-white")

            with ui.dialog().classes("glass-card p-4 rounded-3xl") as dialog:
                with ui.column().classes("gap-4 w-[350px] p-6"):
                    ui.label("Новый Пресет").classes("text-xl font-bold text-indigo-400")
                    p_mod = (
                        ui.input("Модуль (напр. work_items)")
                        .props("dark rounded standout")
                        .classes("w-full")
                    )
                    p_name = ui.input("Название").props("dark rounded standout").classes("w-full")
                    p_json = (
                        ui.input("Пресет (JSON)", value="{}")
                        .props("dark rounded standout")
                        .classes("w-full")
                    )

                    def _create(dlg=dialog):
                        try:
                            preset = ViewPreset(
                                module=p_mod.value,
                                owner="global",
                                name=p_name.value,
                                preset_json=p_json.value,
                            )
                            admin_system.session.add(preset)
                            admin_system.session.commit()
                            dlg.close()
                            render_presets_form.refresh(admin_system)
                        except Exception as ex:
                            ui.notify(f"Ошибка: {ex}", type="negative")

                    ui.button("СОЗДАТЬ", on_click=_create).classes(
                        "w-full vibrant-btn rounded-xl h-12"
                    )

            ui.button("Добавить", icon="add", on_click=dialog.open).classes(
                "rounded-xl px-6 py-2 vibrant-btn"
            )

        with ui.column().classes("w-full mt-4 gap-2"):
            if not presets:
                ui.label("No Global Presets defined.").classes("text-slate-500 italic p-4")
                return

            for preset in presets:
                with ui.row().classes(
                    "w-full items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10"
                ):
                    with ui.column().classes("gap-1"):
                        ui.label(f"{preset.name} ({preset.module})").classes(
                            "text-lg font-bold text-indigo-400"
                        )
                        ui.label(preset.preset_json).classes("text-xs text-slate-500 font-mono")

                    def _del(p=preset):
                        admin_system.session.delete(p)
                        admin_system.session.commit()
                        render_presets_form.refresh(admin_system)

                    ui.button(icon="delete", color="red", on_click=_del).props("flat dense")
    except Exception as e:
        ui.label(f"Preset Error: {e}").classes("text-red-400")


# ────────────────────────────────────────────────────────────────
# Main view entry point
# ────────────────────────────────────────────────────────────────


async def admin_view(admin_system: AdminSystem, system_provider: Callable, layout: Any) -> None:
    """Cluster Control Plane — tabbed admin dashboard."""
    logger.debug("AdminView: build started")

    ui.label("Cluster Control Plane").classes("text-3xl font-bold text-white mb-4")

    with ui.tabs().classes("w-full bg-white/5 rounded-t-2xl p-2") as tabs:
        t_health = ui.tab("HEALTH", icon="monitor_heart")
        t_users = ui.tab("USERS", icon="person")
        t_roles = ui.tab("ROLES", icon="security")
        t_bind = ui.tab("BINDINGS", icon="settings_remote")
        t_conf = ui.tab("CONFIGURATION", icon="tune")
        t_notif = ui.tab("NOTIFICATIONS", icon="notifications")
        t_preset = ui.tab("PRESETS", icon="view_list")
        t_audit = ui.tab("SYSTEM LOG", icon="history")

    # H1 FIX: declare health_grid BEFORE tab_panels so CONF tab can reference it safely
    health_grid_ref: list[ui.table] = []  # mutable container avoids NameError

    with ui.tab_panels(tabs, value=t_users).classes("w-full glass-card rounded-b-2xl p-8"):
        # ── HEALTH ─────────────────────────────────────────────
        with ui.tab_panel(t_health):
            ui.label("Active Node Heartbeats").classes("text-xl font-bold text-indigo-400 mb-6")
            cols = [
                {"name": "node_id", "label": "Identifier", "field": "node_id", "align": "left"},
                {"name": "status", "label": "State", "field": "status", "align": "center"},
                {"name": "is_leader", "label": "Leader", "field": "is_leader", "align": "center"},
                {
                    "name": "last_active",
                    "label": "Last Activity",
                    "field": "last_active",
                    "align": "right",
                },
            ]
            hg = ui.table(columns=cols, rows=[], row_key="node_id").classes(
                "w-full bg-transparent text-slate-300"
            )
            health_grid_ref.append(hg)  # store reference for CONF tab

            async def _refresh_health():
                try:
                    fresh_system = await system_provider(AdminSystem)
                    nodes = await fresh_system.get_cluster_nodes()
                    hg.rows[:] = nodes
                    hg.update()
                except Exception as exc:
                    logger.error(f"Health refresh failed: {exc}")

            # H4 FIX: don't await during page build — defer to avoid WS latency
            layout.register_timer(ui.timer(0.5, _refresh_health, once=True))
            layout.register_timer(ui.timer(5.0, _refresh_health))

            async def force_step_down_action():
                fresh_system = await system_provider(AdminSystem)
                fresh_system.force_global_step_down()
                ui.notify("Step down command broadcasted", color="warning")

            ui.button(
                "EMERGENCY STEP DOWN",
                icon="warning",
                color="red",
                on_click=force_step_down_action,
            ).classes("mt-12 rounded-xl px-8")

        # ── USERS ──────────────────────────────────────────────
        with ui.tab_panel(t_users):
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.label("Identity Registry").classes("text-2xl font-bold text-white")

                with ui.dialog().classes("glass-card p-4 rounded-3xl") as user_dialog:
                    with ui.column().classes("gap-4 w-[350px] p-6"):
                        ui.label("Register New Identity").classes("text-xl font-bold text-white")
                        u_name = (
                            ui.input("Username").props("dark rounded standout").classes("w-full")
                        )
                        u_pass = (
                            ui.input("Password", password=True)
                            .props("dark rounded standout")
                            .classes("w-full")
                        )
                        u_role_sel = (
                            ui.select({}, label="Assign Role")
                            .props("dark rounded standout")
                            .classes("w-full")
                        )

                        def _load_roles():
                            opts = {r.id: r.name for r in admin_system.get_all_roles()}
                            u_role_sel.set_options(opts)
                            if opts:
                                u_role_sel.value = list(opts.keys())[0]

                        user_dialog.on("show", _load_roles)

                        async def _create_user():
                            if u_name.value and u_role_sel.value:
                                admin_system.create_user(
                                    {
                                        "username": u_name.value,
                                        "password_hash": u_pass.value,
                                        "role_id": u_role_sel.value,
                                    }
                                )
                                user_dialog.close()
                                render_user_registry.refresh(admin_system)  # H3 FIX
                                ui.notify(f"User {u_name.value} registered", color="positive")
                            else:
                                ui.notify("Username and Role required", color="negative")

                        ui.button("CREATE USER", on_click=_create_user).classes(
                            "w-full vibrant-btn rounded-xl h-12"
                        )

                ui.button("Register User", icon="person_add", on_click=user_dialog.open).classes(
                    "rounded-xl px-6 py-2 vibrant-btn"
                )

            await render_user_registry(system_provider)

        # ── ROLES ──────────────────────────────────────────────
        with ui.tab_panel(t_roles):
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.label("Permission Matrix").classes("text-2xl font-bold text-white")

                with ui.dialog().classes("glass-card p-4 rounded-3xl") as role_dialog:
                    with ui.column().classes("gap-4 w-[350px] p-6"):
                        ui.label("Create Custom Role").classes("text-xl font-bold text-white")
                        r_name = (
                            ui.input("Role Name").props("dark rounded standout").classes("w-full")
                        )

                        async def _create_role():
                            if r_name.value:
                                fresh_system = await system_provider(AdminSystem)
                                fresh_system.upsert_role(r_name.value, [])
                                role_dialog.close()
                                await render_role_matrix.refresh(system_provider)  # H3 FIX
                                ui.notify(f"Role {r_name.value} created", color="positive")

                        ui.button("INITIALIZE ROLE", on_click=_create_role).classes(
                            "w-full vibrant-btn rounded-xl h-12"
                        )

                ui.button("Add Role", icon="add", on_click=role_dialog.open).classes(
                    "rounded-xl px-6 py-2 vibrant-btn"
                )

            await render_role_matrix(system_provider)

        # ── BINDINGS ───────────────────────────────────────────
        with ui.tab_panel(t_bind):
            ui.label("Hardware Node Bindings").classes("text-xl font-bold text-indigo-400 mb-6")
            try:
                workplaces = admin_system.get_all_workplaces()
                if not workplaces:
                    ui.label("No workplaces configured.").classes("text-slate-500 italic p-4")
                for w in workplaces:
                    with ui.row().classes(
                        "w-full p-6 bg-indigo-500/5 rounded-2xl mb-4 "
                        "border border-indigo-500/10 items-center justify-between"
                    ):
                        with ui.column():
                            ui.label(w.name).classes("text-2xl font-bold text-white")
                            ui.badge(w.node_id, color="slate-700").classes("font-mono text-xs")

                        with ui.dialog().classes("glass-card p-8 rounded-3xl") as edit_wp:
                            with ui.column().classes("gap-4 w-[400px]"):
                                ui.label(f"Configure {w.name}").classes(
                                    "text-xl font-bold text-indigo-400"
                                )
                                new_nid = ui.input("Hardware Node ID", value=w.node_id).props(
                                    "dark rounded standout"
                                )
                                allowed = ui.input(
                                    "Allowed Modules (comma-sep)", value=w.allowed_modules
                                ).props("dark rounded standout")

                                async def _update_binding(wp=w, nid=new_nid, allow=allowed):
                                    admin_system.upsert_workplace(
                                        {
                                            "name": wp.name,
                                            "node_id": nid.value,
                                            "allowed_modules": allow.value,
                                        }
                                    )
                                    edit_wp.close()
                                    ui.notify("Binding updated", color="positive")

                                ui.button("UPDATE BINDING", on_click=_update_binding).classes(
                                    "w-full vibrant-btn rounded-xl h-12"
                                )

                        ui.button("Manage Station", icon="edit", on_click=edit_wp.open).classes(
                            "rounded-xl bg-white/5 border border-white/10 text-xs py-2 px-4"
                        )
            except Exception as e:
                ui.label(f"Binding Error: {e}").classes("text-red-400")
                logger.exception(f"Bindings tab failed: {e}")

        # ── CONFIGURATION ──────────────────────────────────────
        with ui.tab_panel(t_conf):
            ui.label("Declarative Settings Grid").classes("text-xl font-bold text-indigo-400 mb-2")
            ui.label(
                "Changing these parameters will broadcast signed P2P updates across the cluster."
            ).classes("text-xs text-slate-500 mb-6")

            from docuflow.domain.settings import registry

            modules = registry.get_all_modules()

            if not modules:
                ui.label("No modules registered in SettingsRegistry.").classes(
                    "text-slate-500 italic p-8 rounded-2xl"
                )
            else:
                # FIX: Load nodes directly via timer, independent of HEALTH tab
                with ui.row().classes("w-full gap-4"):
                    mod_select = (
                        ui.select(modules, value=modules[0], label="Select Module")
                        .classes("w-64")
                        .props("dark rounded standout")
                    )
                    target_node = (
                        ui.select({None: "Global"}, value=None, label="Scope (Node or Global)")
                        .classes("w-64")
                        .props("dark rounded standout")
                    )

                ui.separator().classes("my-4 opacity-10")

                async def _load_conf_nodes():
                    """Load cluster nodes for CONFIGURATION tab independently."""
                    try:
                        fresh_system = await system_provider(AdminSystem)
                        nodes = await fresh_system.get_cluster_nodes()
                        node_options = {None: "Global"}
                        for n in nodes:
                            node_options[n["node_id"]] = (
                                f"{n['node_id']} ({n.get('status', 'unknown')})"
                            )
                        target_node.set_options(node_options)
                        logger.debug(f"Config: loaded {len(nodes)} nodes")
                    except Exception as e:
                        logger.error(f"Config nodes load failed: {e}")

                # Load nodes after page build
                layout.register_timer(ui.timer(0.5, _load_conf_nodes, once=True))

                async def _refresh_settings():
                    node_id = target_node.value
                    scope = "global" if node_id is None else "local"
                    logger.debug(
                        f"Config refresh: module={mod_select.value}, scope={scope}, node={node_id}"
                    )
                    await render_settings_form.refresh(
                        system_provider, mod_select.value, node_id, []
                    )

                mod_select.on_value_change(lambda: _refresh_settings())
                target_node.on_value_change(lambda: _refresh_settings())

                # Initial render with first module and Global scope
                await render_settings_form(system_provider, modules[0], None, [])

        # ── NOTIFICATIONS ──────────────────────────────────────
        with ui.tab_panel(t_notif):
            ui.label("Notification Templates").classes("text-xl font-bold text-indigo-400 mb-2")
            await render_notifications_form(system_provider)

        # ── PRESETS ────────────────────────────────────────────
        with ui.tab_panel(t_preset):
            await render_presets_form(system_provider)

        # ── SYSTEM LOG (Visual Audit) ──────────────────────────
        with ui.tab_panel(t_audit):
            ui.label("Global Cluster Event Stream").classes(
                "text-xl font-bold text-indigo-400 mb-6"
            )
            await render_system_audit(system_provider)
            # Auto-refresh every 10 seconds
            layout.register_timer(
                ui.timer(10.0, lambda: render_system_audit.refresh(system_provider))
            )

    logger.debug("AdminView: build complete")


@ui.refreshable
async def render_system_audit(system_provider: Callable) -> None:
    """Renders a global timeline of system events."""
    from sqlmodel import select

    from docuflow.domain.entities.production import WorkLog

    try:
        fresh_system = await system_provider(AdminSystem)
        logs = fresh_system.session.exec(
            select(WorkLog).order_by(WorkLog.created_at.desc()).limit(100)
        ).all()

        if not logs:
            ui.label("No events recorded yet.").classes("text-slate-500 italic p-4")
            return

        with ui.column().classes("w-full gap-2"):
            for log in logs:
                with ui.row().classes(
                    "w-full items-start gap-4 p-4 bg-white/5 rounded-xl border border-white/5 hover:border-indigo-500/20 transition-all"
                ):
                    # Time and Type
                    with ui.column().classes("w-24 gap-0"):
                        ui.label(log.created_at.strftime("%H:%M")).classes("text-white font-bold")
                        ui.label(log.created_at.strftime("%d.%m.%y")).classes(
                            "text-[10px] text-slate-500"
                        )
                        ui.badge(log.log_type).props("color=indigo-900 size=xs").classes("mt-1")

                    # Content
                    with ui.column().classes("flex-grow gap-1"):
                        ui.label(log.message).classes("text-slate-200 text-sm")
                        if log.payload and len(log.payload) > 2:
                            ui.label(log.payload).classes("text-[9px] text-slate-600 font-mono")

                    # Author and Node
                    with ui.column().classes("items-end w-32 gap-0"):
                        if log.author:
                            ui.label(log.author).classes("text-xs text-indigo-400 font-bold")
                        ui.label(log.node_id or "system").classes("text-[10px] text-slate-500")

    except Exception as e:
        ui.label(f"Audit Log Error: {e}").classes("text-red-400")
