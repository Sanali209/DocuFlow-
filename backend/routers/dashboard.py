from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta
from typing import Dict, List, Any

from .. import models, crud
from ..dependencies import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    # 1. Document Stats
    doc_status_counts = db.query(
        models.Document.status, func.count(models.Document.id)
    ).group_by(models.Document.status).all()
    
    doc_type_counts = db.query(
        models.Document.type, func.count(models.Document.id)
    ).group_by(models.Document.type).all()
    
    # 2. Task Stats
    task_status_counts = db.query(
        models.Task.status, func.count(models.Task.id)
    ).group_by(models.Task.status).all()
    
    task_assignee_distribution = db.query(
        models.Task.assignee, func.count(models.Task.id)
    ).filter(models.Task.assignee != None).group_by(models.Task.assignee).all()
    
    # 3. Inventory Summary
    total_materials = db.query(func.count(models.Material.id)).scalar()
    stock_summary = db.query(
        func.sum(models.StockItem.quantity).label("total_qty"),
        func.sum(models.StockItem.reserved).label("total_reserved")
    ).first()
    
    # 4. Recent Activity (Audit Logs)
    recent_logs = db.query(models.AuditLog).order_by(desc(models.AuditLog.timestamp)).limit(10).all()
    
    # 5. Journal Summary (Warnings/Errors)
    recent_journal = db.query(
        models.JournalEntry.type, func.count(models.JournalEntry.id)
    ).filter(models.JournalEntry.type.in_([models.JournalEntryType.WARNING, models.JournalEntryType.ERROR])).group_by(models.JournalEntry.type).all()
    
    # 6. Trends (Last 7 days)
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    created_trends = db.query(
        models.Document.registration_date, func.count(models.Document.id)
    ).filter(models.Document.registration_date >= week_ago).group_by(models.Document.registration_date).all()
    
    completed_trends = db.query(
        models.Document.done_date, func.count(models.Document.id)
    ).filter(models.Document.done_date >= week_ago).group_by(models.Document.done_date).all()

    return {
        "document_stats": {
            "by_status": {status.value if status else "unknown": count for status, count in doc_status_counts},
            "by_type": {dtype.value if dtype else "unknown": count for dtype, count in doc_type_counts},
            "total": sum(count for _, count in doc_status_counts)
        },
        "task_stats": {
            "by_status": {status.value if status else "unknown": count for status, count in task_status_counts},
            "by_assignee": {assignee: count for assignee, count in task_assignee_distribution},
            "total": sum(count for _, count in task_status_counts)
        },
        "inventory": {
            "total_materials": total_materials,
            "total_quantity": stock_summary.total_qty or 0,
            "total_reserved": stock_summary.total_reserved or 0
        },
        "recent_activity": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "actor": log.actor,
                "action": log.action_type,
                "entity": log.entity_type,
                "entity_id": log.entity_id
            } for log in recent_logs
        ],
        "journal_summary": {jtype.value: count for jtype, count in recent_journal},
        "trends": {
            "created": {str(d): count for d, count in created_trends},
            "completed": {str(d): count for d, count in completed_trends if d}
        }
    }
