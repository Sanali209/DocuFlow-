from dataclasses import dataclass

from sqlmodel import Session, col, select

from docuflow.domain.entities.production import (
    PartLibrary,
    ProductionUnit,
    WorkItem,
)


@dataclass
class SearchResult:
    """Унифицированный результат поиска."""

    id: int
    title: str
    subtitle: str
    type: str  # 'work_item', 'part', 'pallet'
    view_name: str
    icon: str
    payload: dict = None


class SearchSystem:
    """
    Система сквозного поиска по всему производственному кластеру.
    Объединяет результаты из WorkItems, PartLibrary и ProductionUnits.
    """

    def __init__(self, session: Session):
        self.session = session

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """
        Выполняет поиск по всем основным сущностям.

        Args:
            query: Поисковый запрос (минимум 2 символа)
            limit: Максимальное количество результатов

        Returns:
            List[SearchResult]
        """
        if not query or len(query) < 2:
            return []

        results = []
        pattern = f"%{query}%"

        # 1. Поиск по Нарядам (WorkItems)
        items = self.session.exec(
            select(WorkItem)
            .where(
                (col(WorkItem.folder_name).ilike(pattern))
                | (col(WorkItem.sidra_number).ilike(pattern))
            )  # type: ignore[attr-defined]
            .limit(limit)
        ).all()

        for item in items:
            results.append(
                SearchResult(
                    id=item.id,
                    title=item.folder_name,
                    subtitle=f"Наряд: {item.sidra_number or '—'} | {item.work_item_type}",
                    type="work_item",
                    view_name="work_items",
                    icon="assignment",
                    payload={"folder_name": item.folder_name},
                )
            )

        # 2. Поиск по Деталям (PartLibrary)
        parts = self.session.exec(
            select(PartLibrary)
            .where(
                (col(PartLibrary.sku).ilike(pattern))  # type: ignore[attr-defined]
                | (col(PartLibrary.name).ilike(pattern))  # type: ignore[attr-defined]
            )
            .limit(limit)
        ).all()

        for part in parts:
            results.append(
                SearchResult(
                    id=part.id,
                    title=part.sku,
                    subtitle=f"Деталь | Версия: {part.version}",
                    type="part",
                    view_name="parts",
                    icon="extension",
                    payload={"sku": part.sku},
                )
            )

        # 3. Поиск по Паллетам (ProductionUnits)
        units = self.session.exec(
            select(ProductionUnit).where(col(ProductionUnit.label_id).ilike(pattern)).limit(limit)  # type: ignore[attr-defined]
        ).all()

        for unit in units:
            results.append(
                SearchResult(
                    id=unit.id,
                    title=unit.label_id,
                    subtitle=f"Паллета | Кол-во: {unit.qty_produced}",
                    type="pallet",
                    view_name="production",
                    icon="inventory_2",
                    payload={"label_id": unit.label_id},
                )
            )

        return results[:limit]
