import re
from dataclasses import dataclass
from datetime import date

from docuflow.domain.entities.production import WorkItemType

# Constants for folder name patterns
REWORK_KEYWORD = "REWORK"


@dataclass
class FolderMeta:
    """Metadata extracted from a folder name."""

    work_item_type: WorkItemType
    sidra_number: str | None = None
    sidra_step: str | None = None
    doc_date: date | None = None
    project_hint: str | None = None


class FolderNameParser:
    """
    Parses folder names to determine work item attributes.
    Primary pattern: SIDRA-NUMBER-STEP-DD.MM.YYYY
    """

    SIDRA_REGEX = re.compile(
        r"^SIDRA-(?P<number>\d+)-(?P<step>.+?)-(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})$",
        re.IGNORECASE,
    )

    def parse(self, name: str) -> FolderMeta:
        """
        Parses folder name and returns FolderMeta.
        Never raises; returns MIHTAV fallback on failure.
        """
        # 1. Check for SIDRA standard
        match = self.SIDRA_REGEX.match(name)
        if match:
            try:
                doc_date = date(
                    int(match.group("year")), int(match.group("month")), int(match.group("day"))
                )
                return FolderMeta(
                    work_item_type=WorkItemType.SIDRA,
                    sidra_number=match.group("number"),
                    sidra_step=match.group("step"),
                    project_hint=match.group("step"),
                    doc_date=doc_date,
                )
            except (ValueError, TypeError):
                # Fallback if date conversion fails despite regex match
                pass

        # 2. Check for REWORK
        if REWORK_KEYWORD in name.upper():
            return FolderMeta(
                work_item_type=WorkItemType.REWORK,
                project_hint=None,  # Default project for reworks unless specified
            )

        # 3. Default Fallback (MIHTAV)
        return FolderMeta(work_item_type=WorkItemType.MIHTAV, project_hint=None)
