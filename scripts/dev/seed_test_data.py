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

        proj_id = project.id
        if proj_id is None:
            raise RuntimeError("Project was not created")

        # Создаём WorkItem
        work_items = [
            WorkItem(
                folder_name="SIDRA-353203-SHLAV-2",
                folder_path="Z:\\sidra\\SIDRA-353203-SHLAV-2",
                project_id=proj_id,  # type: ignore[arg-type]
                work_item_type=WorkItemType.SIDRA,
                status=WorkItemStatus.NEW,
                sidra_number="353203",
            ),
            WorkItem(
                folder_name="SIDRA-353204-SHLAV-2",
                folder_path="Z:\\sidra\\SIDRA-353204-SHLAV-2",
                project_id=proj_id,  # type: ignore[arg-type]
                work_item_type=WorkItemType.SIDRA,
                status=WorkItemStatus.REGISTERED,
                sidra_number="353204",
            ),
            WorkItem(
                folder_name="MIHTAV-2025-07",
                folder_path="Z:\\mihtav\\MIHTAV-2025-07",
                project_id=proj_id,  # type: ignore[arg-type]
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
        mat_id = material.id
        if mat_id is None:
            raise RuntimeError("Material was not created")

        for wi in work_items:
            wi_id = wi.id
            if wi_id is None:
                continue
            for i in range(2):
                task = TaskItem(
                    work_item_id=wi_id,  # type: ignore[arg-type]
                    mat_type_id=mat_id,  # type: ignore[arg-type]
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
        from docuflow.features.view_presets.system import ViewPresetSystem

        preset_system = ViewPresetSystem(session=session)  # type: ignore[call-arg]

        preset_system.create(
            view_name="work_items",
            user_id="global",
            name="Все активные",
            filters_json={
                "view_type": "table",
                "filters": {"status": ["new", "registered", "in_progress"]},
            },
        )

        preset_system.create(
            view_name="work_items",
            user_id="global",
            name="Только новые",
            filters_json={
                "view_type": "table",
                "filters": {"status": ["new"]},
            },
        )

        print(f"Создано: {len(work_items)} WorkItem, {len(work_items) * 2} TaskItem, 2 ViewPreset")


if __name__ == "__main__":
    seed()
