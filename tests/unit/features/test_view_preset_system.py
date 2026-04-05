"""
Тесты для ViewPresetSystem.

TDD подход:
1. Сначала тесты
2. Потом код
3. Рефакторинг
"""

import json

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from docuflow.domain.entities.production import ViewPreset
from docuflow.features.view_presets.system import ViewPresetSystem
from docuflow.infrastructure.config import Config


@pytest.fixture(name="session")
def session_fixture():
    """Создаёт in-memory SQLite сессию для тестов."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="config")
def config_fixture():
    """Создаёт тестовую конфигурацию."""
    return Config(node_id="test_node", shared_path="./test_shared")


@pytest.fixture(name="system")
def system_fixture(config: Config, session: Session):
    """Создаёт экземпляр ViewPresetSystem."""
    return ViewPresetSystem(config=config, session=session)


class TestViewPresetSystemCreate:
    """Тесты для метода create()."""

    def test_create_preset(self, system: ViewPresetSystem):
        """Создание нового пресета."""
        preset = system.create(
            module="work_items",
            owner="user1",
            name="Мои задачи",
            preset_json={
                "view_type": "table",
                "columns": ["folder_name", "status"],
                "filters": {"status": ["NEW", "REGISTERED"]},
            },
        )

        assert preset.id is not None
        assert preset.module == "work_items"
        assert preset.owner == "user1"
        assert preset.name == "Мои задачи"
        assert preset.is_default == False

        # Проверяем, что preset_json валидный JSON
        config = json.loads(preset.preset_json)
        assert config["view_type"] == "table"
        assert config["columns"] == ["folder_name", "status"]

    def test_create_global_preset(self, system: ViewPresetSystem):
        """Создание глобального пресета."""
        preset = system.create(
            module="work_items",
            owner="global",
            name="Все активные",
            preset_json={"view_type": "table", "filters": {}},
        )

        assert preset.owner == "global"

    def test_create_default_preset(self, system: ViewPresetSystem):
        """Создание пресета по умолчанию."""
        preset = system.create(
            module="work_items",
            owner="user1",
            name="По умолчанию",
            preset_json={},
            is_default=True,
        )

        assert preset.is_default == True


class TestViewPresetSystemList:
    """Тесты для метода list()."""

    def test_list_personal_and_global(self, system: ViewPresetSystem):
        """Возвращает и global и personal пресеты."""
        system.create(
            module="work_items",
            owner="global",
            name="Все активные",
            preset_json={},
        )
        system.create(
            module="work_items",
            owner="user1",
            name="Мои задачи",
            preset_json={},
        )
        system.create(
            module="work_items",
            owner="user2",
            name="Задачи user2",
            preset_json={},
        )

        presets = system.list("work_items", "user1")

        # user1 видит global + свой, но не видит user2
        assert len(presets) == 2
        owners = {p.owner for p in presets}
        assert owners == {"global", "user1"}

    def test_list_only_global(self, system: ViewPresetSystem):
        """Возвращает только global пресеты."""
        system.create(
            module="work_items",
            owner="global",
            name="Все активные",
            preset_json={},
        )

        presets = system.list("work_items", "user1")

        assert len(presets) == 1
        assert presets[0].owner == "global"

    def test_list_empty(self, system: ViewPresetSystem):
        """Возвращает пустой список, если нет пресетов."""
        presets = system.list("work_items", "user1")

        assert len(presets) == 0


class TestViewPresetSystemGetActive:
    """Тесты для метода get_active()."""

    def test_get_active_personal(self, system: ViewPresetSystem):
        """Получает personal active пресет."""
        system.create(
            module="work_items",
            owner="user1",
            name="Мои задачи",
            preset_json={},
            is_default=True,
        )

        active = system.get_active("work_items", "user1")

        assert active is not None
        assert active.name == "Мои задачи"
        assert active.is_default == True

    def test_get_active_global_fallback(self, system: ViewPresetSystem):
        """Если нет personal active, возвращает global default."""
        system.create(
            module="work_items",
            owner="global",
            name="Все активные",
            preset_json={},
            is_default=True,
        )

        active = system.get_active("work_items", "user1")

        assert active is not None
        assert active.owner == "global"

    def test_get_active_none(self, system: ViewPresetSystem):
        """Возвращает None, если нет active пресетов."""
        system.create(
            module="work_items",
            owner="user1",
            name="Мои задачи",
            preset_json={},
            is_default=False,
        )

        active = system.get_active("work_items", "user1")

        assert active is None


class TestViewPresetSystemSetActive:
    """Тесты для метода set_active()."""

    def test_set_active(self, system: ViewPresetSystem):
        """Устанавливает active пресет."""
        p1 = system.create(
            module="work_items",
            owner="user1",
            name="Пресет 1",
            preset_json={},
            is_default=True,
        )
        p2 = system.create(
            module="work_items",
            owner="user1",
            name="Пресет 2",
            preset_json={},
        )

        result = system.set_active("work_items", "user1", p2.id)

        assert result.is_default == True
        assert result.id == p2.id

        # Проверяем, что старый пресет больше не default
        p1_updated = system.session.get(ViewPreset, p1.id)
        assert p1_updated.is_default == False

    def test_set_active_not_found(self, system: ViewPresetSystem):
        """Ошибка, если пресет не найден."""
        with pytest.raises(ValueError, match="не найден"):
            system.set_active("work_items", "user1", 999999)

    def test_set_active_wrong_module(self, system: ViewPresetSystem):
        """Ошибка, если пресет не принадлежит модулю."""
        p = system.create(
            module="task_board",
            owner="user1",
            name="Пресет",
            preset_json={},
        )

        with pytest.raises(ValueError, match="не принадлежит модулю"):
            system.set_active("work_items", "user1", p.id)

    def test_set_active_wrong_owner(self, system: ViewPresetSystem):
        """Ошибка, если пресет не принадлежит пользователю."""
        p = system.create(
            module="work_items",
            owner="user2",
            name="Пресет user2",
            preset_json={},
        )

        with pytest.raises(ValueError, match="не принадлежит пользователю"):
            system.set_active("work_items", "user1", p.id)


class TestViewPresetSystemDelete:
    """Тесты для метода delete()."""

    def test_delete_personal(self, system: ViewPresetSystem):
        """Удаление personal пресета."""
        p = system.create(
            module="work_items",
            owner="user1",
            name="Мои задачи",
            preset_json={},
        )

        system.delete(p.id, owner="user1")

        deleted = system.session.get(ViewPreset, p.id)
        assert deleted is None

    def test_delete_global_by_admin(self, system: ViewPresetSystem):
        """Удаление global пресета админом."""
        p = system.create(
            module="work_items",
            owner="global",
            name="Все активные",
            preset_json={},
        )

        system.delete(p.id, owner="admin")

        deleted = system.session.get(ViewPreset, p.id)
        assert deleted is None

    def test_delete_global_by_user_raises(self, system: ViewPresetSystem):
        """Ошибка при удалении global пресета обычным пользователем."""
        p = system.create(
            module="work_items",
            owner="global",
            name="Все активные",
            preset_json={},
        )

        with pytest.raises(PermissionError, match="глобальные пресеты"):
            system.delete(p.id, owner="user1")

    def test_delete_other_user_raises(self, system: ViewPresetSystem):
        """Ошибка при удалении чужого пресета."""
        p = system.create(
            module="work_items",
            owner="user2",
            name="Задачи user2",
            preset_json={},
        )

        with pytest.raises(PermissionError, match="чужие пресеты"):
            system.delete(p.id, owner="user1")

    def test_delete_not_found(self, system: ViewPresetSystem):
        """Ошибка, если пресет не найден."""
        with pytest.raises(ValueError, match="не найден"):
            system.delete(999999, owner="user1")


class TestViewPresetSystemGetPresetJson:
    """Тесты для метода get_preset_json()."""

    def test_get_preset_json(self, system: ViewPresetSystem):
        """Возвращает конфигурацию пресета как словарь."""
        config = {
            "view_type": "table",
            "columns": ["folder_name", "status"],
            "filters": {"status": ["NEW"]},
            "sort": {"field": "created_at", "dir": "desc"},
            "group_by": "project_id",
        }
        p = system.create(
            module="work_items",
            owner="user1",
            name="Пресет",
            preset_json=config,
        )

        result = system.get_preset_json(p)

        assert result == config
        assert result["view_type"] == "table"
        assert result["columns"] == ["folder_name", "status"]
