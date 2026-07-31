from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

import models
import schemas
from database import engine, get_db, Base

# Creates the intake_events and batches tables if they don't exist yet.
# Safe to run every startup — it never touches existing tables/data.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Compost Tracker API")

# Allows only your actual frontend(s) to call this API — your deployed
# Vercel app, plus localhost so local development still works.
# ALLOWED_ORIGINS can be set on Railway to add more later without a code change.
import os

default_origins = "https://compost-tracker.vercel.app,http://localhost:5173"
allowed_origins = os.getenv("ALLOWED_ORIGINS", default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/intake-events/", response_model=schemas.IntakeEventOut)
def create_intake_event(event: schemas.IntakeEventCreate, db: Session = Depends(get_db)):
    db_event = models.IntakeEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.get("/intake-events/", response_model=List[schemas.IntakeEventOut])
def list_intake_events(db: Session = Depends(get_db)):
    return db.query(models.IntakeEvent).order_by(models.IntakeEvent.date.desc()).all()


@app.get("/intake-events/summary")
def diversion_summary(db: Session = Depends(get_db)):
    """Quick running total — the seed of your diversion report."""
    total = db.query(func.sum(models.IntakeEvent.volume_cy)).scalar() or 0
    return {"total_volume_cy": total}


@app.post("/batches/", response_model=schemas.BatchOut)
def create_batch(batch: schemas.BatchCreate, db: Session = Depends(get_db)):
    db_batch = models.Batch(**batch.model_dump())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch


@app.get("/batches/", response_model=List[schemas.BatchOut])
def list_batches(db: Session = Depends(get_db)):
    return db.query(models.Batch).order_by(models.Batch.start_date.desc()).all()


@app.get("/batches/{batch_id}", response_model=schemas.BatchOut)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@app.patch("/batches/{batch_id}/close", response_model=schemas.BatchOut)
def close_batch(batch_id: int, end_date: str, finished_volume_cy: float, db: Session = Depends(get_db)):
    """Mark a batch finished: set its end date and the volume of compost it produced."""
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    batch.end_date = end_date
    batch.finished_volume_cy = finished_volume_cy
    db.commit()
    db.refresh(batch)
    return batch
