from collections.abc import Callable
from typing import Any

from nicegui import ui
from sqlmodel import select

from docuflow.domain.entities.production import ChatMessage, ChatMessageType
from docuflow.features.chat.system import ChatSystem
from docuflow.features.core.views import ViewInfo, ViewRegistry


def register_chat_view():
    """Register the chat portal view."""
    ViewRegistry.register(
        ViewInfo(
            name="chat",
            label="Chat",
            icon="chat",
            render_fn=chat_view_wrapper,
            dependencies=[ChatSystem],
            pass_user=True,
            pass_system_provider=True,
            is_async=True,
        )
    )


async def chat_view_wrapper(system: ChatSystem, user: str, system_provider: Callable, layout: Any):
    """Wrapper to instantiate and render the ChatView."""
    view = ChatView(system, current_user=user, system_provider=system_provider, layout=layout)
    await view.render_portal()


class ChatView:
    """
    Real-time communication portal for a distributed workshop floor.

    Principles:
    - Code as Documentation: UI methods are organized by functional area.
    - Theme Consistency: Styling extracted from logic into local theme constants.
    """

    # Global UI Theme for the Chat Module
    UI_STYLING = {
        "sidebar_bg": "bg-[#020617] border-r border-white/5 p-6 h-full gap-4",
        "feed_bg": "bg-[#020617]",
        "input_bar": "absolute bottom-0 w-full p-4 bg-slate-900/50 backdrop-blur-xl border-t border-white/5 gap-2 items-end",
        "message_bubble": "w-full gap-3 p-3 rounded-xl border transition-all hover:bg-white/5",
        "label_header": "text-[10px] font-bold text-slate-500 uppercase tracking-widest",
    }

    def __init__(
        self,
        chat_system: ChatSystem,
        current_user: str = "operator",
        system_provider: Callable | None = None,
        layout: Any = None,
    ):
        self.chat_system = chat_system
        self.current_user = current_user
        self.system_provider = system_provider
        self.layout = layout
        self.message_feed_container = None
        self.active_channel = "global"  # global thread by default
        self.user_input_area = None

    async def render_portal(self):
        """
        Builds the complete multi-pane chat interface.

        Example:
            view = ChatView(system)
            await view.render_portal()
        """
        with ui.row().classes("w-full h-full gap-0 bg-[#020617]"):
            # 1. Sidebar Navigation
            self._build_navigation_sidebar()

            # 2. Main Discussion Area
            with ui.column().classes(
                f"flex-grow flex-col h-full {self.UI_STYLING['feed_bg']} relative"
            ):
                self._build_chat_header()

                with ui.scroll_area().classes("flex-grow w-full px-8 py-4"):
                    self.message_feed_container = ui.column().classes("w-full gap-4 pb-24")
                    await self.refresh_discussion_feed()

                    # Live update loop (registered with layout)
                    if self.layout:
                        self.layout.register_timer(ui.timer(5.0, self.refresh_discussion_feed))
                    else:
                        ui.timer(5.0, self.refresh_discussion_feed)

                self._build_footer_input()

    def _build_navigation_sidebar(self):
        """Internal helper to render the side channel-switcher."""
        with ui.column().classes(self.UI_STYLING["sidebar_bg"]).classes("w-64"):
            ui.label("WORKSHOP CHANNELS").classes(self.UI_STYLING["label_header"])

            with ui.column().classes("w-full gap-1"):
                self._render_channel_link("General Feed", "forum", "global")
                self._render_channel_link("Supply & Orders", "shopping_cart", "order")
                self._render_channel_link("Failure Log", "report_problem", "incident")

            ui.separator().classes("bg-white/5 my-4")
            ui.label("QUICK ACTIONS").classes(self.UI_STYLING["label_header"])
            ui.button("Report Breakdown", icon="error", on_click=self.open_incident_dialog).classes(
                "w-full mt-2 normal-case text-xs"
            ).props("flat color=red")

    def _render_channel_link(self, label: str, icon: str, channel_key: str):
        """Renders an individual sidebar navigation button."""
        is_active = self.active_channel == channel_key
        bg_style = "bg-white/5" if is_active else ""
        text_style = "text-white font-bold" if is_active else "text-slate-400 font-medium"

        with (
            ui.row()
            .classes(
                f"w-full p-2 rounded-lg cursor-pointer transition-all items-center gap-3 {bg_style} hover:bg-white/5"
            )
            .on("click", lambda: self._switch_channel(channel_key))
        ):
            ui.icon(icon, size="20px", color="primary" if is_active else "slate-400")
            ui.label(label).classes(f"text-sm {text_style}")

    def _build_chat_header(self):
        with ui.row().classes("w-full p-6 border-b border-white/5 items-center justify-between"):
            ui.label(f"Channel: {self.active_channel.title()}").classes(
                "text-lg font-bold text-slate-100 uppercase tracking-tighter"
            )
            ui.button(icon="refresh", on_click=self.refresh_discussion_feed).props(
                "flat round size=sm color=slate-500"
            )

    def _build_footer_input(self):
        with ui.row().classes(self.UI_STYLING["input_bar"]):
            self.user_input_area = (
                ui.textarea(placeholder="Write a message...")
                .classes("flex-grow bg-white/5 text-white")
                .props("outlined autogrow dense dark rounded")
            )
            ui.button(icon="send", on_click=self.handle_message_submission).props(
                "unelevated color=primary rounded"
            )

    # --- Discussion Flow Logic ---

    async def _switch_channel(self, channel_key: str):
        self.active_channel = channel_key
        await self.refresh_discussion_feed()

    async def refresh_discussion_feed(self):
        """Reload and clear the feed based on the active selection."""
        if not self.message_feed_container:
            return
        self.message_feed_container.clear()

        relevant_messages = self._query_messages_for_channel()

        if not relevant_messages:
            with self.message_feed_container:
                ui.label("No transmission in this channel yet.").classes(
                    "text-slate-600 text-sm mt-10 w-full text-center italic"
                )
            return

        # Sort chronological (bottom is newest)
        for chat_msg in sorted(relevant_messages, key=lambda x: x.created_at):
            self._render_message_bubble(chat_msg)

    def _query_messages_for_channel(self) -> list[ChatMessage]:
        """Internal selector for database queries depending on channel context."""
        if self.active_channel == "global":
            return self.chat_system.get_global_messages()

        # Mapping channel keys to Database message types
        TYPE_MAP = {"order": ChatMessageType.ORDER, "incident": ChatMessageType.INCIDENT}
        target_type = TYPE_MAP.get(self.active_channel)

        statement = (
            select(ChatMessage)
            .where(ChatMessage.message_type == target_type)
            .order_by(ChatMessage.created_at.desc())
        )

        return list(self.chat_system.db_session.exec(statement).all())

    def _render_message_bubble(self, msg: ChatMessage):
        """Displays a single colored message component."""
        with self.message_feed_container:
            # 1. Determine Visual Theme based on type
            THEME_MAP = {
                ChatMessageType.ORDER: {
                    "bg": "bg-emerald-950/20",
                    "border": "border-emerald-500/20",
                    "icon": "shopping_cart",
                    "color": "emerald",
                },
                ChatMessageType.INCIDENT: {
                    "bg": "bg-red-950/20",
                    "border": "border-red-500/20",
                    "icon": "error",
                    "color": "red",
                },
                ChatMessageType.MESSAGE: {
                    "bg": "bg-slate-900",
                    "border": "border-white/5",
                    "icon": "chat",
                    "color": "primary",
                },
            }
            theme = THEME_MAP.get(msg.message_type, THEME_MAP[ChatMessageType.MESSAGE])

            # 2. Render Bubble
            with ui.row().classes(
                f"{self.UI_STYLING['message_bubble']} {theme['bg']} {theme['border']}"
            ):
                ui.icon(theme["icon"], color=theme["color"], size="20px").classes("mt-1")
                with ui.column().classes("flex-grow gap-0"):
                    with ui.row().classes("w-full justify-between items-center"):
                        ui.label(msg.author).classes("text-xs font-bold text-slate-100")
                        ui.label(msg.created_at.strftime("%H:%M")).classes(
                            "text-[10px] text-slate-500 font-mono"
                        )

                    ui.label(msg.content).classes("text-sm text-slate-300 mt-1 leading-relaxed")

    async def handle_message_submission(self):
        """Submit and clear the user input."""
        content = self.user_input_area.value.strip()
        if not content:
            return

        # Default mapping for quick entry from specific channels
        TYPE_MAP = {"order": ChatMessageType.ORDER, "incident": ChatMessageType.INCIDENT}

        # H2 FIX: Fresh system for action
        fresh_system = await self.system_provider(ChatSystem)
        await fresh_system.send_message(
            author=self.current_user,
            content=content,
            message_type=TYPE_MAP.get(self.active_channel, ChatMessageType.MESSAGE),
        )

        self.user_input_area.value = ""
        await self.refresh_discussion_feed()

    # --- Interaction Dialogs ---

    def open_incident_dialog(self):
        """Modal for formal workshop breakdown reporting."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("bg-slate-900 border border-red-500/20 w-96 p-6"),
        ):
            ui.label("REPORT BREAKDOWN").classes(
                "text-sm font-black text-red-400 mb-4 tracking-widest"
            )

            task_ref = ui.number(label="Task Reference (ID)", format="%d").classes("w-full")
            description = ui.textarea(
                label="Failure Description", placeholder="Laser tube power loss..."
            ).classes("w-full")

            async def submit():
                if not description.value:
                    return
                # Refactored incident system call
                from docuflow.features.chat.incidents import IncidentSystem

                incident_sys = await self.system_provider(IncidentSystem)
                incident_sys.report_incident(
                    incident_sys.TYPE_BREAKDOWN,
                    description.value,
                    "operator",
                    task_item_id=int(task_ref.value or 0),
                )

                dialog.close()
                await self.refresh_discussion_feed()
                ui.notify("Incident logged and broadcasted", color="red")

            with ui.row().classes("w-full justify-end mt-6"):
                ui.button("Cancel", on_click=dialog.close).props("flat text-color=slate-500")
                ui.button("LOG INCIDENT", on_click=submit).props("unelevated color=red")
        dialog.open()
