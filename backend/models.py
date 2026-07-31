from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from datetime import datetime
from database import Base


class User(Base):
    """A person who can log into the app — either a field user or a reviewer."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_user_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    role = Column(String, nullable=False, default="field_user")  # "field_user" or "reviewer"


class IntakeEvent(Base):
    """One delivery of food scraps or green waste arriving at the site."""

    __tablename__ = "intake_events"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    material_type = Column(String, nullable=False)  # "food_scraps" or "green_waste"
    volume_cy = Column(Float, nullable=False)
    hauler = Column(String, nullable=True)
    logged_by = Column(String, nullable=True)  # display name, set from the logged-in user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # who owns this entry


class Batch(Base):
    """One compost batch, from formation through finished product."""

    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_label = Column(String, nullable=False, unique=True)  # e.g. "2026-07-B12"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # null until the batch is finished
    finished_volume_cy = Column(Float, nullable=True)  # null until screened/measured
    notes = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # who owns this batch


class Comment(Base):
    """A reviewer's note on an intake event, flagging it for a correction."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    intake_event_id = Column(Integer, ForeignKey("intake_events.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
