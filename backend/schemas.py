
from pydantic import BaseModel
from datetime import date as date_type
from typing import Optional
 
 
class IntakeEventCreate(BaseModel):
    """What the frontend sends us when logging a new intake event."""
    date: date_type
    material_type: str
    volume_cy: float
    hauler: Optional[str] = None
    logged_by: Optional[str] = None
 
 
class IntakeEventOut(IntakeEventCreate):
    """What we send back — same fields, plus the database-assigned id."""
    id: int
 
    class Config:
        from_attributes = True  # lets Pydantic read straight from the SQLAlchemy model
 
 
class BatchCreate(BaseModel):
    """What's sent when starting a new batch."""
    batch_label: str
    start_date: date_type
    end_date: Optional[date_type] = None
    finished_volume_cy: Optional[float] = None
    notes: Optional[str] = None
 
 
class BatchOut(BatchCreate):
    id: int
 
    class Config:
        from_attributes = True
