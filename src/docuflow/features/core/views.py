from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class ViewInfo:
    """Metadata about a feature view for the registry."""

    name: str
    label: str
    icon: str
    render_fn: Callable[..., Any]  # The function or class method to call
    # List of dependency types to resolve from the container
    dependencies: list[type[Any]] = field(default_factory=list)
    # Extra flags or settings
    pass_user: bool = False
    pass_switch_view: bool = False
    pass_system_scope: bool = False
    pass_layout: bool = False
    is_async: bool = False


class ViewRegistry:
    """Central registry for all feature views in DocuFlow."""

    _views: ClassVar[dict[str, ViewInfo]] = {}

    @classmethod
    def register(cls, info: ViewInfo):
        cls._views[info.name] = info

    @classmethod
    def get_view(cls, name: str) -> ViewInfo | None:
        return cls._views.get(name)

    @classmethod
    def get_all_views(cls) -> list[ViewInfo]:
        return list(cls._views.values())


def register_view(
    name: str,
    label: str,
    icon: str,
    dependencies: list[type[Any]] | None = None,
    *,
    pass_system_scope: bool = True,
    pass_layout: bool = True,
    is_async: bool = True,
    **extra: Any,
):
    """Decorator to register a view class in the ViewRegistry.

    Usage:
        @register_view(name="warehouse", label="Warehouse", icon="inventory_2",
                        dependencies=[InventorySystem])
        class WarehouseView(BaseDocuWidget):
            ...
    """

    def decorator(view_class: type[Any]) -> type[Any]:
        async def render_fn(system, system_scope, layout):
            view = view_class(system, system_scope, layout)
            await view.render()

        ViewRegistry.register(
            ViewInfo(
                name=name,
                label=label,
                icon=icon,
                render_fn=render_fn,
                dependencies=dependencies or [],
                pass_system_scope=pass_system_scope,
                pass_layout=pass_layout,
                is_async=is_async,
                **extra,
            )
        )
        return view_class

    return decorator
