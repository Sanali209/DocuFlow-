"""
Тесты для UI виджетов.

Smoke тесты — проверяют, что виджеты рендерятся без ошибок.
"""

import pytest
pytest.importorskip("nicegui")
from unittest.mock import MagicMock, patch

from docuflow.domain.entities.production import TaskItemStatus, WorkItemStatus
from docuflow.lib.widgets import ExplorerButton, FileChangedAlert, StatusBadge


@pytest.mark.usefixtures("ui_context")
class TestStatusBadge:
    """Тесты для StatusBadge."""

    def test_render_work_item_status(self):
        """Рендерит бейдж для WorkItem статуса."""
        badge = StatusBadge(WorkItemStatus.NEW)
        result = badge.render()

        assert result is not None

    def test_render_task_item_status(self):
        """Рендерит бейдж для TaskItem статуса."""
        badge = StatusBadge(TaskItemStatus.IN_PROGRESS)
        result = badge.render()

        assert result is not None

    def test_render_with_size(self):
        """Рендерит бейдж с указанным размером."""
        badge = StatusBadge(WorkItemStatus.DONE, size="lg")
        result = badge.render()

        assert result is not None

    def test_get_color_work_item(self):
        """Возвращает правильный цвет для WorkItem статуса."""
        badge = StatusBadge(WorkItemStatus.NEW)
        color = badge._get_color()

        assert color == "blue"

    def test_get_color_task_item(self):
        """Возвращает правильный цвет для TaskItem статуса."""
        badge = StatusBadge(TaskItemStatus.BLOCKED)
        color = badge._get_color()

        assert color == "red"

    def test_get_label(self):
        """Возвращает правильную метку для статуса."""
        badge = StatusBadge(WorkItemStatus.REGISTERED)
        label = badge._get_label()

        assert label == "Зарегистрирован"


@pytest.mark.usefixtures("ui_context")
class TestExplorerButton:
    """Тесты для ExplorerButton."""

    def test_render(self):
        """Рендерит кнопку."""
        button = ExplorerButton(path="Z:\\test")
        result = button.render()

        assert result is not None

    def test_render_with_custom_label(self):
        """Рендерит кнопку с кастомным текстом."""
        button = ExplorerButton(path="Z:\\test", label="Открыть")
        result = button.render()

        assert result is not None

    @patch("subprocess.Popen")
    def test_open_explorer(self, mock_popen):
        """Вызывает subprocess.Popen для открытия папки."""
        button = ExplorerButton(path="Z:\\test")
        button._open_explorer()

        mock_popen.assert_called_once_with(["explorer.exe", "Z:\\test"])

    @patch("subprocess.Popen", side_effect=Exception("Error"))
    def test_open_explorer_error(self, mock_popen):
        """Обрабатывает ошибку при открытии папки."""
        button = ExplorerButton(path="Z:\\test")

        # Не должно падать
        button._open_explorer()


@pytest.mark.usefixtures("ui_context")
class TestFileChangedAlert:
    """Тесты для FileChangedAlert."""

    def test_render(self):
        """Рендерит баннер уведомления."""
        alert = FileChangedAlert(file_name="test.GNC", file_path="Z:\\test.GNC")
        result = alert.render()

        assert result is not None

    def test_render_with_refresh_callback(self):
        """Рендерит баннер с callback для обновления."""
        mock_callback = MagicMock()
        alert = FileChangedAlert(
            file_name="test.GNC", file_path="Z:\\test.GNC", on_refresh=mock_callback
        )
        result = alert.render()

        assert result is not None
