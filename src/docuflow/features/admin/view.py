import logging
from typing import Any

from nicegui import ui

from docuflow.features.admin.system import AdminSystem
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper


def register_admin_view():
    """Register the admin view in the global registry."""
    ViewRegistry.register(
        ViewInfo(
            name="admin",
            label="Admin",
            icon="settings",
            render_fn=admin_view_wrapper,
            dependencies=[AdminSystem],
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def admin_view_wrapper(admin_system: AdminSystem, system_scope: Any, layout: Any):
    """Wrapper to instantiate and render the AdminView."""
    view = AdminView(admin_system, system_scope, layout)
    await view.render()


logger = logging.getLogger("docuflow.admin.view")


class AdminView(BaseDocuWidget):
    """Cluster Control Plane — tabbed admin dashboard."""

    def __init__(self, admin_system: AdminSystem, system_scope: Any, layout: Any):
        super().__init__(system_scope)
        self.admin_system = admin_system
        self.layout = layout

    @ui.refreshable
    async def render_user_registry(self) -> None:
        """Renders the Identity Registry list."""
        try:
            async with self.scope() as req:
                admin_system = await req.get(AdminSystem)
                users = admin_system.get_all_users()
                logger.debug(f"AdminView [USERS]: fetched count={len(users)}")

                if not users:
                    ui.label("No users found in Identity Registry").classes(
                        "text-slate-500 italic p-4"
                    )
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
                                    role_name = u.role.name if u.role else "None"
                                    ui.label(f"Role: {role_name}").classes(
                                        "text-[10px] text-slate-400"
                                    )

                            if not is_root_admin:

                                async def _remove(un=u.username):
                                    async with self.scope() as r:
                                        fresh_system = await r.get(AdminSystem)
                                        fresh_system.delete_user(un)
                                    await self.render_user_registry.refresh()
                                    NotifyHelper.warning(f"User {un} deleted")

                                ui.button(icon="delete")

        except Exception as e:
            ui.label("Registry Offline...").classes("text-red-400 italic")
            logger.exception(f"render_user_registry failed: {e}")

    @ui.refreshable
    async def render_role_matrix(self) -> None:
        """Renders the Permission Matrix."""
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
            async with self.scope() as req:
                admin_system = await req.get(AdminSystem)
                roles = admin_system.get_all_roles()
                logger.debug(f"AdminView [ROLES]: fetched count={len(roles)}")

                if not roles:
                    ui.label("No roles defined.").classes("text-slate-500 italic p-4")
                    return

                with ui.column().classes("w-full gap-4"):
                    for r in roles:
                        is_admin_role = r.name.strip().lower() == "admin"
                        border = "border-indigo-500/40" if is_admin_role else "border-white/5"
                        with ui.column().classes(
                            f"w-full p-6 bg-white/5 rounded-2xl border {border}"
                        ):
                            with ui.row().classes("w-full justify-between items-center mb-4"):
                                with ui.column().classes("gap-0"):
                                    label_color = (
                                        "text-indigo-400" if is_admin_role else "text-white"
                                    )
                                    ui.label(r.name).classes(f"text-xl font-bold {label_color}")
                                    ui.label(f"Role ID: {r.id}").classes(
                                        "text-[10px] text-slate-500 font-mono"
                                    )

                                if not is_admin_role:

                                    async def _del_role(rn=r.name):
                                        async with self.scope() as req2:
                                            fresh_system = await req2.get(AdminSystem)
                                            fresh_system.delete_role(rn)
                                        await self.render_role_matrix.refresh()
                                        NotifyHelper.warning(f"Role {rn} deleted")

                                    ui.button(icon="delete")

                            with ui.row().classes("gap-2 flex-wrap"):
                                for mod in MODULES:
                                    current_perms = r.permissions_list
                                    module_perm = next(
                                        (p for p in current_perms if p.startswith(f"{mod}:")), None
                                    )
                                    is_on = module_perm is not None
                                    perm_type = module_perm.split(":")[1] if is_on else "none"

                                    async def _toggle(
                                        m=mod, r_name=r.name, active=is_on, mp=module_perm
                                    ):
                                        if r_name.strip().lower() == "admin":
                                            return

                                        async with self.scope() as req3:
                                            fresh_system = await req3.get(AdminSystem)
                                            # Fetch fresh role object within scope
                                            from sqlmodel import select

                                            from docuflow.domain.entities.identity import Role

                                            r_ref = fresh_system.session.exec(
                                                select(Role).where(Role.name == r_name)
                                            ).first()

                                            if not r_ref:
                                                return

                                            remaining = [
                                                p
                                                for p in r_ref.permissions_list
                                                if not p.startswith(f"{m}:")
                                            ]
                                            if not active:
                                                remaining.append(f"{m}:read")
                                            elif mp and "read" in mp:
                                                remaining.append(f"{m}:full")

                                            fresh_system.upsert_role(r_ref.name, remaining)
                                        await self.render_role_matrix.refresh()

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
        self,
        module: str,
        node_id: str | None,
        node_rows: list[dict],
    ) -> None:
        """Renders the dynamic settings form."""
        try:
            from docuflow.domain.settings import registry

            async with self.scope() as req:
                admin_system = await req.get(AdminSystem)

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

                with ui.column().classes(
                    "w-full mt-4 p-6 bg-white/5 rounded-2xl border border-white/10"
                ):
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
                                async with self.scope() as req2:
                                    fresh_system = await req2.get(AdminSystem)
                                    fresh_system.update_node_setting(
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
    async def render_notifications_form(self) -> None:
        """Renders the notification templates form."""
        try:
            async with self.scope() as req:
                admin_system = await req.get(AdminSystem)
                tmpls = admin_system.get_notification_templates()
                if not tmpls:
                    ui.label("No Notification Templates defined.").classes(
                        "text-slate-500 italic p-4"
                    )
                    return

                with ui.column().classes("w-full mt-4 gap-4"):
                    for tmpl in tmpls:
                        with ui.row().classes(
                            "w-full items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10"
                        ):
                            with ui.column().classes("gap-1 flex-1"):
                                ui.label(tmpl.key).classes("text-lg font-bold text-indigo-400")

                                async def update_text(e, tmpl_id=tmpl.id, enabled=tmpl.enabled):
                                    async with self.scope() as req2:
                                        fresh_system = await req2.get(AdminSystem)
                                        fresh_system.update_notification_template(
                                            tmpl_id, text=e.value, enabled=enabled
                                        )
                                        NotifyHelper.warning("Шаблон уведомления сохранен")

                                # Use lazy binding via on_change
                                txt_input = (
                                    ui.input(value=tmpl.text)
                                    .props("dark standout rounded")
                                    .classes("w-full text-slate-300")
                                )
                                txt_input.on(
                                    "change",
                                    lambda e, tid=tmpl.id, en=tmpl.enabled: update_text(e, tid, en),
                                )

                            with ui.column().classes("ml-8 items-end w-32"):

                                async def update_toggle(e, tmpl_id=tmpl.id, text=tmpl.text):
                                    async with self.scope() as req3:
                                        fresh_system = await req3.get(AdminSystem)
                                        fresh_system.update_notification_template(
                                            tmpl_id, text=text, enabled=e.value
                                        )

                                ui.switch("Active", value=tmpl.enabled, on_change=update_toggle)
        except Exception as e:
            ui.label(f"Notif Error: {e}").classes("text-red-400")

    @ui.refreshable
    async def render_presets_form(self) -> None:
        """Renders the global view presets form."""
        try:
            async with self.scope() as req:
                admin_system = await req.get(AdminSystem)
                # Only global presets
                presets = admin_system.get_view_presets(owner="global")

                with ui.row().classes("w-full mt-4 gap-4 justify-between items-center"):
                    ui.label("Глобальные Пресеты (View Presets)").classes(
                        "text-xl font-bold text-white"
                    )

                    with ui.dialog().classes("glass-card p-4 rounded-3xl") as dialog:
                        with ui.column().classes("gap-4 w-[350px] p-6"):
                            ui.label("Новый Пресет").classes("text-xl font-bold text-indigo-400")
                            p_mod = (
                                ui.input("Модуль (напр. work_items)")
                                .props("dark rounded standout")
                                .classes("w-full")
                            )
                            p_name = (
                                ui.input("Название")
                                .props("dark rounded standout")
                                .classes("w-full")
                            )
                            p_json = (
                                ui.input("Пресет (JSON)", value="{}")
                                .props("dark rounded standout")
                                .classes("w-full")
                            )

                            async def _create(dlg=dialog):
                                try:
                                    async with self.scope() as req2:
                                        fresh_system = await req2.get(AdminSystem)
                                        fresh_system.create_view_preset(
                                            p_mod.value, p_name.value, p_json.value
                                        )
                                    dlg.close()
                                    await self.render_presets_form.refresh()
                                except Exception as ex:
                                    NotifyHelper.error(f"Ошибка: {ex}")

                            ui.button("СОЗДАТЬ", on_click=_create).classes(
                                "w-full vibrant-btn rounded-xl h-12"
                            )

                    ui.button("Добавить")

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
                                ui.label(preset.preset_json).classes(
                                    "text-xs text-slate-500 font-mono"
                                )

                            async def _del(p_id=preset.id):
                                async with self.scope() as req3:
                                    fresh_system = await req3.get(AdminSystem)
                                    fresh_system.delete_view_preset(p_id)
                                await self.render_presets_form.refresh()

                            ui.button(icon="delete", color="red", on_click=_del).props("flat dense")
        except Exception as e:
            ui.label(f"Preset Error: {e}").classes("text-red-400")

    @ui.refreshable
    async def render_bindings_panel(self) -> None:
        """Displays all workplace bindings."""
        try:
            async with self.scope() as req:
                admin_system = await req.get(AdminSystem)
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
                                    "Allowed Modules (comma-sep)", value=w.allowed_modules or ""
                                ).props("dark rounded standout")

                                async def _update_binding(
                                    wp_name=w.name, nid=new_nid, allow=allowed
                                ):
                                    async with self.scope() as req2:
                                        fresh_system = await req2.get(AdminSystem)
                                        fresh_system.upsert_workplace(
                                            {
                                                "name": wp_name,
                                                "node_id": nid.value,
                                                "allowed_modules": allow.value or "",
                                            }
                                        )
                                    edit_wp.close()
                                    NotifyHelper.warning("Binding updated")
                                    await self.render_bindings_panel.refresh()

                                ui.button("UPDATE BINDING", on_click=_update_binding).classes(
                                    "w-full vibrant-btn rounded-xl h-12"
                                )

                        with ui.dialog().classes("glass-card p-8 rounded-3xl") as delete_confirm:
                            with ui.column().classes("gap-4 w-[350px]"):
                                ui.label(f"Delete '{w.name}'?").classes(
                                    "text-xl font-bold text-red-400"
                                )
                                ui.label("This action cannot be undone.").classes("text-slate-400")

                                async def _confirm_delete(node_id=w.node_id):
                                    async with self.scope() as req3:
                                        fresh_system = await req3.get(AdminSystem)
                                        fresh_system.delete_workplace(node_id)
                                    delete_confirm.close()
                                    NotifyHelper.success("Binding deleted")
                                    await self.render_bindings_panel.refresh()

                                ui.button("DELETE", on_click=_confirm_delete).classes(
                                    "w-full bg-red-600 text-white rounded-xl h-12"
                                )
                                ui.button("Cancel", on_click=delete_confirm.close).classes(
                                    "w-full bg-white/10 rounded-xl"
                                )

                        with ui.row().classes("gap-2"):
                            ui.button("Edit")
                            ui.button(
                                "Delete", icon="delete", on_click=delete_confirm.open
                            ).classes(
                                "rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 text-xs py-2 px-4"
                            )

        except Exception as e:
            ui.label(f"Binding Error: {e}").classes("text-red-400")
            logger.exception(f"Bindings panel failed: {e}")

    @ui.refreshable
    async def render_system_audit(self) -> None:
        """Renders a global timeline of system events."""
        try:
            async with self.scope() as req:
                fresh_system = await req.get(AdminSystem)
                logs = fresh_system.get_system_audit_logs(limit=100)

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
                                ui.label(log.created_at.strftime("%H:%M")).classes(
                                    "text-white font-bold"
                                )
                                ui.label(log.created_at.strftime("%d.%m.%y")).classes(
                                    "text-[10px] text-slate-500"
                                )
                                ui.badge(log.log_type).props("color=indigo-900 size=xs").classes(
                                    "mt-1"
                                )

                            # Content
                            with ui.column().classes("flex-grow gap-1"):
                                ui.label(log.message).classes("text-slate-200 text-sm")
                                if log.payload and len(log.payload) > 2:
                                    ui.label(log.payload).classes(
                                        "text-[9px] text-slate-600 font-mono"
                                    )

                            # Author and Node
                            with ui.column().classes("items-end w-32 gap-0"):
                                if log.author:
                                    ui.label(log.author).classes(
                                        "text-xs text-indigo-400 font-bold"
                                    )
                                ui.label(log.node_id or "system").classes(
                                    "text-[10px] text-slate-500"
                                )

        except Exception as e:
            ui.label(f"Audit Log Error: {e}").classes("text-red-400")

    async def render(self) -> None:
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

        health_grid_ref: list[ui.table] = []  # mutable container avoids NameError

        with ui.tab_panels(tabs, value=t_users).classes("w-full glass-card rounded-b-2xl p-8"):
            # ── HEALTH ─────────────────────────────────────────────
            with ui.tab_panel(t_health):
                ui.label("Active Node Heartbeats").classes("text-xl font-bold text-indigo-400 mb-6")
                cols = [
                    {"name": "node_id", "label": "Identifier", "field": "node_id", "align": "left"},
                    {"name": "status", "label": "State", "field": "status", "align": "center"},
                    {
                        "name": "is_leader",
                        "label": "Leader",
                        "field": "is_leader",
                        "align": "center",
                    },
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
                        async with self.scope() as req:
                            fresh_system = await req.get(AdminSystem)
                            nodes = fresh_system.get_cluster_nodes()
                            hg.rows[:] = nodes
                            hg.update()
                    except Exception as exc:
                        logger.error(f"Health refresh failed: {exc}")

                self.layout.register_timer(ui.timer(0.5, _refresh_health, once=True))
                self.layout.register_timer(ui.timer(5.0, _refresh_health))

                async def force_step_down_action():
                    async with self.scope() as req:
                        fresh_system = await req.get(AdminSystem)
                        fresh_system.force_global_step_down()
                        NotifyHelper.warning("Step down command broadcasted")

                ui.button("EMERGENCY STEP DOWN")

            # ── USERS ──────────────────────────────────────────────
            with ui.tab_panel(t_users):
                with ui.row().classes("w-full justify-between items-center mb-6"):
                    ui.label("Identity Registry").classes("text-2xl font-bold text-white")

                    with ui.dialog().classes("glass-card p-4 rounded-3xl") as user_dialog:
                        with ui.column().classes("gap-4 w-[350px] p-6"):
                            ui.label("Register New Identity").classes(
                                "text-xl font-bold text-white"
                            )
                            u_name = (
                                ui.input("Username")
                                .props("dark rounded standout")
                                .classes("w-full")
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

                            async def _load_roles():
                                async with self.scope() as req:
                                    fresh_system = await req.get(AdminSystem)
                                    opts = {r.id: r.name for r in fresh_system.get_all_roles()}
                                    u_role_sel.set_options(opts)
                                    if opts:
                                        u_role_sel.value = next(iter(opts.keys()))

                            user_dialog.on("show", _load_roles)

                            async def _create_user():
                                if u_name.value and u_role_sel.value:
                                    async with self.scope() as req:
                                        fresh_system = await req.get(AdminSystem)
                                        fresh_system.create_user(
                                            {
                                                "username": u_name.value,
                                                "password_hash": u_pass.value,
                                                "role_id": u_role_sel.value,
                                            }
                                        )
                                    user_dialog.close()
                                    await self.render_user_registry.refresh()
                                    NotifyHelper.warning(f"User {u_name.value} registered")
                                else:
                                    NotifyHelper.warning("Username and Role required")

                            ui.button("CREATE USER", on_click=_create_user).classes(
                                "w-full vibrant-btn rounded-xl h-12"
                            )

                    ui.button("Register User")

                await self.render_user_registry()

            # ── ROLES ──────────────────────────────────────────────
            with ui.tab_panel(t_roles):
                with ui.row().classes("w-full justify-between items-center mb-6"):
                    ui.label("Permission Matrix").classes("text-2xl font-bold text-white")

                    with ui.dialog().classes("glass-card p-4 rounded-3xl") as role_dialog:
                        with ui.column().classes("gap-4 w-[350px] p-6"):
                            ui.label("Create Custom Role").classes("text-xl font-bold text-white")
                            r_name = (
                                ui.input("Role Name")
                                .props("dark rounded standout")
                                .classes("w-full")
                            )

                            async def _create_role():
                                if r_name.value:
                                    async with self.scope() as req:
                                        fresh_system = await req.get(AdminSystem)
                                        fresh_system.upsert_role(r_name.value, [])
                                    role_dialog.close()
                                    await self.render_role_matrix.refresh()
                                    NotifyHelper.warning(f"Role {r_name.value} created")

                            ui.button("INITIALIZE ROLE", on_click=_create_role).classes(
                                "w-full vibrant-btn rounded-xl h-12"
                            )

                    ui.button("Add Role")

                await self.render_role_matrix()

            # ── BINDINGS ───────────────────────────────────────────
            with ui.tab_panel(t_bind):
                with ui.row().classes("w-full justify-between items-center mb-6"):
                    ui.label("Hardware Node Bindings").classes("text-xl font-bold text-indigo-400")

                    with ui.dialog().classes("glass-card p-8 rounded-3xl") as create_wp:
                        with ui.column().classes("gap-4 w-[400px]"):
                            ui.label("Create New Binding").classes("text-xl font-bold text-white")
                            wp_name = ui.input("Workplace Name").props("dark rounded standout")
                            wp_node = ui.input("Hardware Node ID").props("dark rounded standout")
                            wp_modules = ui.input("Allowed Modules (comma-sep)").props(
                                "dark rounded standout"
                            )

                            async def _create_binding():
                                if not wp_name.value or len(wp_name.value) < 3:
                                    NotifyHelper.warning(
                                        "Workplace name must be at least 3 characters"
                                    )
                                    return
                                if not wp_node.value:
                                    NotifyHelper.warning("Hardware Node ID is required")
                                    return

                                async with self.scope() as req:
                                    fresh_system = await req.get(AdminSystem)
                                    fresh_system.upsert_workplace(
                                        {
                                            "name": wp_name.value,
                                            "node_id": wp_node.value,
                                            "allowed_modules": wp_modules.value or "",
                                        }
                                    )
                                create_wp.close()
                                wp_name.value = ""
                                wp_node.value = ""
                                wp_modules.value = ""
                                NotifyHelper.info("Binding created")
                                await self.render_bindings_panel.refresh()

                            ui.button("CREATE BINDING", on_click=_create_binding).classes(
                                "w-full vibrant-btn rounded-xl h-12"
                            )

                    ui.button("Add Binding")

                await self.render_bindings_panel()

            # ── CONFIGURATION ──────────────────────────────────────
            with ui.tab_panel(t_conf):
                ui.label("Declarative Settings Grid").classes(
                    "text-xl font-bold text-indigo-400 mb-2"
                )
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
                            async with self.scope() as req:
                                fresh_system = await req.get(AdminSystem)
                                nodes = fresh_system.get_cluster_nodes()
                                node_options = {None: "Global"}
                                for n in nodes:
                                    node_options[n["node_id"]] = (
                                        f"{n['node_id']} ({n.get('status', 'unknown')})"
                                    )
                                target_node.set_options(node_options)
                                logger.debug(f"Config: loaded {len(nodes)} nodes")
                        except Exception as e:
                            logger.error(f"Config nodes load failed: {e}")

                    self.layout.register_timer(ui.timer(0.5, _load_conf_nodes, once=True))

                    async def _refresh_settings():
                        node_id = target_node.value
                        scope = "global" if node_id is None else "local"
                        logger.debug(
                            f"Config refresh: module={mod_select.value}, scope={scope}, node={node_id}"
                        )
                        await self.render_settings_form.refresh(mod_select.value, node_id, [])

                    mod_select.on_value_change(lambda: _refresh_settings())
                    target_node.on_value_change(lambda: _refresh_settings())

                    await self.render_settings_form(modules[0], None, [])

            # ── NOTIFICATIONS ──────────────────────────────────────
            with ui.tab_panel(t_notif):
                ui.label("Notification Templates").classes("text-xl font-bold text-indigo-400 mb-2")
                await self.render_notifications_form()

            # ── PRESETS ────────────────────────────────────────────
            with ui.tab_panel(t_preset):
                await self.render_presets_form()

            # ── SYSTEM LOG (Visual Audit) ──────────────────────────
            with ui.tab_panel(t_audit):
                ui.label("Global Cluster Event Stream").classes(
                    "text-xl font-bold text-indigo-400 mb-6"
                )
                await self.render_system_audit()
                self.layout.register_timer(
                    ui.timer(10.0, lambda: self.render_system_audit.refresh())
                )

        logger.debug("AdminView: build complete")
