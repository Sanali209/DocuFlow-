from fastapi import APIRouter, Depends, HTTPException
from typing import List
from src.application.services.journal_service import JournalService
from src.domain.models import JournalEntry
from src.api.dependencies import get_journal_service

router = APIRouter(tags=["journal"])

@router.get("/", response_model=List[JournalEntry])
def read_journal(skip: int = 0, limit: int = 100, service: JournalService = Depends(get_journal_service)):
    return service.list_entries(skip, limit)

@router.post("/", response_model=JournalEntry)
def create_journal(entry: JournalEntry, service: JournalService = Depends(get_journal_service)):
    return service.create_entry(entry)

@router.delete("/{entry_id}")
def delete_journal(entry_id: int, service: JournalService = Depends(get_journal_service)):
    if not service.delete_entry(entry_id):
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"ok": True}
