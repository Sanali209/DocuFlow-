"""TDD Tests for Styles tokens.

Target: lib/widgets/styles.py
"""

from docuflow.lib.widgets.styles import Styles


class TestStylesTokens:
    """RED: Styles should expose reusable Tailwind class strings."""

    def test_page_container(self):
        assert "w-full" in Styles.PAGE
        assert "p-4" in Styles.PAGE

    def test_card(self):
        assert "bg-white" in Styles.CARD
        assert "rounded-lg" in Styles.CARD

    def test_heading(self):
        assert "text-2xl" in Styles.HEADING
        assert "font-bold" in Styles.HEADING

    def test_badge_success(self):
        assert "emerald" in Styles.BADGE_SUCCESS

    def test_tokens_are_strings(self):
        assert isinstance(Styles.CARD, str)
        assert isinstance(Styles.HEADING, str)
        assert isinstance(Styles.BUTTON_PRIMARY, str)
