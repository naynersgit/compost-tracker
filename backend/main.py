from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import os
from datetime import date

import models
import schemas
from database import engine, get_db, Base
from auth import get_current_user, require_reviewer

# Creates any tables that don't exist yet. Does NOT alter existing tables —
# adding a column to models.py later requires a manual migration.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Compost Tracker API")

default_origins = "https://compost-tracker.vercel.app,http://localhost:5173"
allowed_origins = os.getenv("ALLOWED_ORIGINS", default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Current user ----------

@app.get("/users/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Lets the frontend find out who's logged in and what they're allowed to see."""
    return current_user


# ---------- Admin: promote a user to reviewer ----------
# Bootstrap-only mechanism — no admin UI yet. Protected by a shared secret
# rather than a role, since there's no "admin" role to check against yet.

ADMIN_SECRET = os.getenv("ADMIN_SECRET")


@app.patch("/users/{user_id}/role")
def set_user_role(user_id: int, role: str, x_admin_secret: str = "", db: Session = Depends(get_db)):
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    if role not in ("field_user", "reviewer"):
        raise HTTPException(status_code=400, detail="role must be field_user or reviewer")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "role": user.role}


# ---------- Intake events ----------

@app.post("/intake-events/", response_model=schemas.IntakeEventOut)
def create_intake_event(
    event: schemas.IntakeEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_event = models.IntakeEvent(
        **event.model_dump(),
        logged_by=current_user.name,
        user_id=current_user.id,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.get("/intake-events/", response_model=List[schemas.IntakeEventOut])
def list_intake_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.IntakeEvent)
    if current_user.role != "reviewer":
        query = query.filter(models.IntakeEvent.user_id == current_user.id)
    return query.order_by(models.IntakeEvent.date.desc()).all()


@app.patch("/intake-events/{event_id}", response_model=schemas.IntakeEventOut)
def update_intake_event(
    event_id: int,
    event: schemas.IntakeEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Lets the original logger correct their own entry."""
    db_event = db.query(models.IntakeEvent).filter(models.IntakeEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Entry not found")
    if db_event.user_id != current_user.id and current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="You can only edit your own entries")
    for field, value in event.model_dump().items():
        setattr(db_event, field, value)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.get("/intake-events/summary")
def diversion_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(func.sum(models.IntakeEvent.volume_cy))
    if current_user.role != "reviewer":
        query = query.filter(models.IntakeEvent.user_id == current_user.id)
    return {"total_volume_cy": query.scalar() or 0}


@app.get("/intake-events/logging-summary")
def logging_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_reviewer),
):
    """Reviewer-only: last log date per person, across everyone's entries."""
    rows = (
        db.query(models.IntakeEvent.logged_by, func.max(models.IntakeEvent.date).label("last_date"))
        .filter(models.IntakeEvent.logged_by.isnot(None), models.IntakeEvent.logged_by != "")
        .group_by(models.IntakeEvent.logged_by)
        .all()
    )
    today = date.today()
    summary = [
        {"logged_by": logged_by, "last_date": last_date, "days_since": (today - last_date).days}
        for logged_by, last_date in rows
    ]
    return sorted(summary, key=lambda r: r["days_since"], reverse=True)


@app.get("/intake-events/flagged")
def flagged_intake_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_reviewer),
):
    """Reviewer-only: entries missing key fields or with suspicious volumes."""
    flagged = []
    for e in db.query(models.IntakeEvent).order_by(models.IntakeEvent.date.desc()).all():
        reasons = []
        if not e.logged_by:
            reasons.append("Missing logged by")
        if not e.hauler:
            reasons.append("Missing hauler")
        if e.volume_cy <= 0:
            reasons.append("Volume is zero or negative")
        if e.volume_cy > 50:
            reasons.append("Unusually high volume")
        if reasons:
            flagged.append({
                "id": e.id, "date": e.date, "material_type": e.material_type,
                "volume_cy": e.volume_cy, "hauler": e.hauler, "logged_by": e.logged_by,
                "reasons": reasons,
            })
    return flagged


# ---------- Comments (reviewer writes, owner + reviewer read) ----------

@app.post("/intake-events/{event_id}/comments", response_model=schemas.CommentOut)
def create_comment(
    event_id: int,
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_reviewer),
):
    db_event = db.query(models.IntakeEvent).filter(models.IntakeEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Entry not found")
    db_comment = models.Comment(intake_event_id=event_id, author_id=current_user.id, body=comment.body)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return schemas.CommentOut(
        id=db_comment.id, body=db_comment.body,
        created_at=db_comment.created_at, author_name=current_user.name,
    )


@app.get("/intake-events/{event_id}/comments", response_model=List[schemas.CommentOut])
def list_comments(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_event = db.query(models.IntakeEvent).filter(models.IntakeEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Entry not found")
    if db_event.user_id != current_user.id and current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="You can only view comments on your own entries")

    results = (
        db.query(models.Comment, models.User.name)
        .join(models.User, models.Comment.author_id == models.User.id)
        .filter(models.Comment.intake_event_id == event_id)
        .order_by(models.Comment.created_at)
        .all()
    )
    return [
        schemas.CommentOut(id=c.id, body=c.body, created_at=c.created_at, author_name=name)
        for c, name in results
    ]


# ---------- Batches ----------

@app.post("/batches/", response_model=schemas.BatchOut)
def create_batch(
    batch: schemas.BatchCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_batch = models.Batch(**batch.model_dump(), user_id=current_user.id)
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch


@app.get("/batches/", response_model=List[schemas.BatchOut])
def list_batches(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Batch)
    if current_user.role != "reviewer":
        query = query.filter(models.Batch.user_id == current_user.id)
    return query.order_by(models.Batch.start_date.desc()).all()


@app.get("/batches/{batch_id}", response_model=schemas.BatchOut)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.user_id != current_user.id and current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="You can only view your own batches")
    return batch


@app.patch("/batches/{batch_id}/close", response_model=schemas.BatchOut)
def close_batch(
    batch_id: int,
    end_date: str,
    finished_volume_cy: float,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.user_id != current_user.id and current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="You can only edit your own batches")
    batch.end_date = end_date
    batch.finished_volume_cy = finished_volume_cy
    db.commit()
    db.refresh(batch)
    return batch
