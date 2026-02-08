from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from src.application.services.production_service import ProductionService
from src.domain.models import Task
from src.api.dependencies import get_db, Depends

# I need to update dependencies.py first to include get_production_service
from src.api.dependencies import get_production_service

router = APIRouter(tags=["production"])

@router.get("/jobs/", response_model=List[Task])
def list_jobs(
    skip: int = 0, 
    limit: int = 100, 
    assignee: Optional[str] = None,
    status: Optional[str] = None,
    service: ProductionService = Depends(get_production_service)
):
    filters = {}
    if assignee: filters["assignee"] = assignee
    if status: filters["status"] = status
    return service.list_jobs(skip, limit, filters)

@router.get("/jobs/{job_id}", response_model=Task)
def get_job(job_id: int, service: ProductionService = Depends(get_production_service)):
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/jobs/", response_model=Task)
def create_job(job: Task, service: ProductionService = Depends(get_production_service)):
    return service.create_job(job)

@router.put("/jobs/{job_id}", response_model=Task)
def update_job(job_id: int, job: Task, service: ProductionService = Depends(get_production_service)):
    if job_id != job.id:
        raise HTTPException(status_code=400, detail="Job ID mismatch")
    return service.update_job(job)

@router.patch("/jobs/{job_id}/status", response_model=Task)
def update_job_status(job_id: int, status: str, service: ProductionService = Depends(get_production_service)):
    job = service.update_job_status(job_id, status)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, service: ProductionService = Depends(get_production_service)):
    if service.delete_job(job_id):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Job not found")
