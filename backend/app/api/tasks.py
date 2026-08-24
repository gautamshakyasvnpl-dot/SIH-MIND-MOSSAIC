import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import LearnerProfile, Sprint, Task, User
from app.schemas import DEFAULT_PROFILE, SprintOut, TaskIn, TaskListOut, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task(db: Session, task_id: str, user: User) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def _task_out(task: Task, sprints: list[Sprint]) -> TaskOut:
    return TaskOut(
        id=task.id,
        title=task.title,
        due_date=task.due_date,
        notes=task.notes,
        status=task.status,
        created_at=task.created_at,
        sprints=[
            SprintOut(id=s.id, index=s.index, description=s.description, minutes=s.minutes, done=s.done)
            for s in sorted(sprints, key=lambda s: s.index)
        ],
    )


@router.post("", response_model=TaskOut)
def create_task(body: TaskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TaskOut:
    profile_row = db.get(LearnerProfile, user.id)
    profile_data: dict[str, object] = dict(DEFAULT_PROFILE)
    if profile_row is not None and isinstance(profile_row.data, dict):
        profile_data.update(profile_row.data)
    pace = str(profile_data.get("pace", "standard"))

    from app.services.tutor import break_into_sprints

    sprint_specs = break_into_sprints(body.title, body.notes, pace)

    task = Task(
        id=uuid.uuid4().hex,
        user_id=user.id,
        title=body.title,
        due_date=body.due_date,
        notes=body.notes,
        status="open",
    )
    db.add(task)
    sprints: list[Sprint] = []
    for i, spec in enumerate(sprint_specs):
        sprint = Sprint(
            id=uuid.uuid4().hex,
            task_id=task.id,
            index=i,
            description=str(spec.get("description", f"Sprint {i + 1}")),
            minutes=int(spec.get("minutes", 25)),
            done=False,
        )
        db.add(sprint)
        sprints.append(sprint)
    db.commit()
    return _task_out(task, sprints)


@router.get("", response_model=TaskListOut)
def list_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TaskListOut:
    tasks = db.query(Task).filter(Task.user_id == user.id).order_by(Task.created_at.desc()).all()
    items = []
    for t in tasks:
        sprints = db.query(Sprint).filter(Sprint.task_id == t.id).order_by(Sprint.index.asc()).all()
        items.append(_task_out(t, sprints))
    return TaskListOut(items=items)


@router.post("/{task_id}/sprints/{sprint_id}/toggle", response_model=TaskOut)
def toggle_sprint(
    task_id: str, sprint_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> TaskOut:
    task = _get_owned_task(db, task_id, user)
    sprint = db.get(Sprint, sprint_id)
    if sprint is None or sprint.task_id != task.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
    sprint.done = not sprint.done
    sprints = db.query(Sprint).filter(Sprint.task_id == task.id).all()
    task.status = "done" if all(s.done for s in sprints) else "open"
    db.commit()
    return _task_out(task, sprints)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    task = _get_owned_task(db, task_id, user)
    db.query(Sprint).filter(Sprint.task_id == task.id).delete()
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
