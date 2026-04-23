"""
Seed тестовые данные для разработки.
"""

import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import Session, SQLModel, create_engine, select

from docuflow.domain.entities.production import (
    MaterialType,
    Project,
    TaskItem,
    TaskItemStatus,
    WorkItem,
    WorkItemStatus,
    WorkItemType,
)
from docuflow.features.view_presets.system import ViewPresetSystem


def seed():
    """Создаёт тестовые данные."""
    engine = create_engine("sqlite:///node_01.db")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Проверяем, есть ли уже данные
        existing = session.exec(select(WorkItem)).first()
        if existing:
            print("Данные уже существуют, пропускаем seed")
            return

        # Создаём проект
        project = Project(name="SHLAV-2", description="Тестовый проект")
        session.add(project)
        session.commit()
        session.refresh(project)

        # Создаём материал
        material = MaterialType(
            code="ST37",
            thickness=3.0,
            nominal_x=3000,
            nominal_y=1500,
        )
        session.add(material)
        session.commit()
        session.refresh(material)

        # Создаём WorkItem
        work_items = [
            WorkItem(
                folder_name="SIDRA-353203-SHLAV-2",
                folder_path="Z:\\sidra\\SIDRA-353203-SHLAV-2",
                project_id=project.id,
                work_item_type=WorkItemType.SIDRA,
                status=WorkItemStatus.NEW,
                sidra_number="353203",
            ),
            WorkItem(
                folder_name="SIDRA-353204-SHLAV-2",
                folder_path="Z:\\sidra\\SIDRA-353204-SHLAV-2",
                project_id=project.id,
                work_item_type=WorkItemType.SIDRA,
                status=WorkItemStatus.REGISTERED,
                sidra_number="353204",
            ),
            WorkItem(
                folder_name="MIHTAV-2025-07",
                folder_path="Z:\\mihtav\\MIHTAV-2025-07",
                project_id=project.id,
                work_item_type=WorkItemType.MIHTAV,
                status=WorkItemStatus.IN_PROGRESS,
            ),
        ]

        for wi in work_items:
            session.add(wi)
        session.commit()

        # Обновляем ID
        for wi in work_items:
            session.refresh(wi)

        # Создаём TaskItem для каждого WorkItem
        for wi in work_items:
            for i in range(2):
                task = TaskItem(
                    work_item_id=wi.id,
                    mat_type_id=material.id,
                    file_name=f"{wi.folder_name}_step_{i + 1}.gnc",
                    file_path=f"/path/{wi.folder_name}/step_{i + 1}.gnc",
                    status=TaskItemStatus.PLANNED,
                    sheet_qty=10,
                    estimated_minutes=30,
                    step_index=i + 1,
                )
                session.add(task)

        session.commit()

        # Создаём дефолтные ViewPreset
        preset_system = ViewPresetSystem(session)

        preset_system.create(
            module="work_items",
            owner="global",
            name="Все активные",
            preset_json={
                "view_type": "table",
                "filters": {"status": ["new", "registered", "in_progress"]},
            },
        )

        preset_system.create(
            module="work_items",
            owner="global",
            name="Только новые",
            preset_json={
                "view_type": "table",
                "filters": {"status": ["new"]},
            },
        )

        print(f"Создано: {len(work_items)} WorkItem, {len(work_items) * 2} TaskItem, 2 ViewPreset")


if __name__ == "__main__":
    seed()
