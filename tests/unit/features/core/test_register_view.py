"""TDD Tests for @register_view decorator.

Target: features/core/views.py
"""

from docuflow.features.core.views import ViewRegistry, register_view


class TestRegisterViewDecorator:
    """RED: @register_view should register view classes in ViewRegistry."""

    def test_registers_view_class(self):
        @register_view(name="test_view", label="Test", icon="star")
        class TestView:
            async def render(self):
                pass

        info = ViewRegistry.get_view("test_view")
        assert info is not None
        assert info.name == "test_view"
        assert info.label == "Test"
        assert info.icon == "star"

    def test_registers_with_dependencies(self):
        class FakeSystem:
            pass

        @register_view(name="dep_view", label="Dep", icon="settings", dependencies=[FakeSystem])
        class DepView:
            async def render(self):
                pass

        info = ViewRegistry.get_view("dep_view")
        assert FakeSystem in info.dependencies

    def test_default_flags(self):
        @register_view(name="flag_view", label="Flags", icon="flag")
        class FlagView:
            async def render(self):
                pass

        info = ViewRegistry.get_view("flag_view")
        assert info.pass_system_scope is True
        assert info.pass_layout is True
        assert info.is_async is True

    def test_overrides_flags(self):
        @register_view(
            name="override_view",
            label="Override",
            icon="edit",
            pass_system_scope=False,
            is_async=False,
        )
        class OverrideView:
            def render(self):
                pass

        info = ViewRegistry.get_view("override_view")
        assert info.pass_system_scope is False
        assert info.is_async is False

    def test_render_fn_is_callable(self):
        @register_view(name="callable_view", label="Callable", icon="check")
        class CallableView:
            async def render(self):
                pass

        info = ViewRegistry.get_view("callable_view")
        assert callable(info.render_fn)

    def test_returns_original_class(self):
        @register_view(name="original_view", label="Original", icon="home")
        class OriginalView:
            pass

        assert OriginalView.__name__ == "OriginalView"
