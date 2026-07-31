
from sqlalchemy import Column, Integer, String, Float, Date
from database import Base
 
 
class IntakeEvent(Base):
    """One delivery of food scraps or green waste arriving at the site."""
 
    __tablename__ = "intake_events"
 
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    material_type = Column(String, nullable=False)  # "food_scraps" or "green_waste"
    volume_cy = Column(Float, nullable=False)
    hauler = Column(String, nullable=True)
    logged_by = Column(String, nullable=True)
 
 
class Batch(Base):
    """One compost batch, from formation through finished product."""
 
    __tablename__ = "batches"
 
    id = Column(Integer, primary_key=True, index=True)
    batch_label = Column(String, nullable=False, unique=True)  # e.g. "2026-07-B12"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # null until the batch is finished
    finished_volume_cy = Column(Float, nullable=True)  # null until screened/measured
    notes = Column(String, nullable=True)