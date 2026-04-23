"""Design System Tokens for NiceGUI Tailwind classes.

Usage:
    from docuflow.lib.widgets.styles import Styles as S
    ui.label("Title").classes(S.HEADING)
    with ui.card().classes(S.CARD):
        ...
"""


class Styles:
    """Reusable Tailwind class combinations."""

    # Containers
    PAGE = "w-full h-full p-4 gap-4"
    CARD = "bg-white rounded-lg shadow-lg p-4"
    CARD_DARK = "glass-card rounded-2xl p-6 border-zinc-800"
    ROW = "flex items-center justify-between gap-4"
    ROW_END = "flex items-center justify-end gap-4"
    COLUMN = "flex flex-col gap-4"

    # Typography
    HEADING = "text-2xl font-bold text-white"
    HEADING_LARGE = "text-3xl font-bold text-white mb-2"
    SUBHEADING = "text-xl font-bold text-white"
    BODY = "text-sm text-zinc-100"
    CAPTION = "text-xs text-slate-400 italic"
    LABEL = "text-sm text-slate-500"

    # Form elements
    INPUT = "w-full bg-zinc-900 text-white border-zinc-700 rounded-lg p-3"
    BUTTON_PRIMARY = "bg-indigo-600 text-white rounded-lg px-4 py-2"
    BUTTON_DANGER = "bg-red-600 text-white rounded-lg px-4 py-2"
    BUTTON_GHOST = "text-slate-400 hover:text-white"

    # Tables
    TABLE_CONTAINER = "w-full overflow-auto rounded-lg border border-zinc-800"
    TABLE_HEADER = "bg-zinc-900 text-slate-400 text-xs uppercase"
    TABLE_ROW = "border-b border-zinc-800 hover:bg-zinc-800/50"

    # Status
    BADGE_SUCCESS = "bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded text-xs"
    BADGE_WARNING = "bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-xs"
    BADGE_ERROR = "bg-red-500/20 text-red-400 px-2 py-1 rounded text-xs"
    BADGE_INFO = "bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs"

    # Spacing helpers
    MT_4 = "mt-4"
    MB_4 = "mb-4"
    MT_2 = "mt-2"
    MB_2 = "mb-2"
    GAP_2 = "gap-2"
    GAP_4 = "gap-4"
    P_4 = "p-4"
    P_6 = "p-6"
