"""Internal task endpoints for task-oriented workflow actions."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.schemas import TaskOut, TaskDecisionResponse
from app.services.audit import log_event

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: Optional[str] = Query(None, pattern="^(open|done)$"),
    limit: int = Query(100, ge=1, le=300),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    return query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/{task_id}/complete", response_model=TaskDecisionResponse)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "done"
    db.commit()
    db.refresh(task)
    log_event(
        db,
        event_type="task_completed",
        message=f"Task {task_id} marked complete.",
        related_action_id=task.action_id,
        details={"task_id": task_id},
    )
    return TaskDecisionResponse(task=task, message="Task completed.")


@router.post("/{task_id}/reopen", response_model=TaskDecisionResponse)
def reopen_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "open"
    db.commit()
    db.refresh(task)
    log_event(
        db,
        event_type="task_reopened",
        message=f"Task {task_id} reopened.",
        related_action_id=task.action_id,
        details={"task_id": task_id},
    )
    return TaskDecisionResponse(task=task, message="Task reopened.")
