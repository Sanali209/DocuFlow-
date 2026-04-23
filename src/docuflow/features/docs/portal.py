from pathlib import Path

from nicegui import ui

from docuflow.features.core.views import ViewInfo, ViewRegistry


def register_docs_view():
    """Register the documentation portal view."""
    ViewRegistry.register(
        ViewInfo(
            name="docs",
            label="Documentation",
            icon="menu_book",
            render_fn=docs_view_wrapper,
            dependencies=[],
        )
    )


def docs_view_wrapper(**kwargs):
    """Wrapper to instantiate and render the DocumentationPortal."""
    DocumentationPortal().build_portal()


class DocumentationPortal:
    """Provides an integrated, decentralized support portal for DocuFlow nodes.

    Serves operational manuals and setup guides directly from the feature slice.
    """

    def __init__(self):
        self._docs_path = Path(__file__).parent / "content"
        self._docs_path.mkdir(exist_ok=True)
        self._ensure_default_docs()

    def _ensure_default_docs(self):
        """Seeding initial support manuals if they don't exist."""
        admin_manual = self._docs_path / "admin_guide.md"
        if not admin_manual.exists():
            admin_manual.write_text("""
# DocuFlow System Administration Guide

## 1. P2P Cluster Monitoring
Administrative nodes can monitor the health of the entire cluster via the **Health Registry**. Every node emits a heartbeat every 30 seconds to the shared network.

## 2. Identity Management
User accounts and roles are decentralized. Updates to the **Identity Registry** are broadcast across the P2P bus using HMAC signatures.

## 3. Emergency Step-Down
In case of leader failure, utilize the 'EMERGENCY STEP DOWN' command to trigger a new election.
            """)

        user_manual = self._docs_path / "user_guide.md"
        if not user_manual.exists():
            user_manual.write_text("""
# DocuFlow Warehouse User Manual

## 1. Material Stock Tracking
The Warehouse module uses absolute-value synchronization. Changes to physical stock are immediately reflected across all nodes.

## 2. Access Authorization
Your sidebar will dynamicall update based on your **Role** and the **Workplace** binding of the current node.
            """)

    def build_portal(self):
        """Constructing the interactive documentation reader."""
        ui.label("Support Portal & Documentation").classes("text-3xl font-bold text-white mb-6")

        with ui.row().classes("w-full gap-8"):
            # Sidebar TOC
            with ui.column().classes("w-[300px] glass-card p-6 h-[600px] overflow-y-auto"):
                ui.label("OPERATIONAL MANUALS").classes(
                    "text-[10px] tracking-widest text-slate-500 font-bold mb-4"
                )

                def load_doc(name):
                    content.clear()
                    doc_file = self._docs_path / f"{name}.md"
                    if doc_file.exists():
                        with content:
                            ui.markdown(doc_file.read_text()).classes(
                                "text-slate-300 prose prose-invert max-w-none"
                            )

                ui.button(
                    "System Administration", on_click=lambda: load_doc("admin_guide")
                ).classes("w-full text-sm normal-case justify-start").props("flat color=slate-300")
                ui.button("Warehouse Operations", on_click=lambda: load_doc("user_guide")).classes(
                    "w-full text-sm normal-case justify-start"
                ).props("flat color=slate-300")

            # Content Viewer
            content = ui.column().classes(
                "flex-1 glass-card p-10 h-[600px] shadow-2xl overflow-y-auto bg-slate-900/10"
            )
            load_doc("admin_guide")  # Default
