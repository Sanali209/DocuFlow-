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
