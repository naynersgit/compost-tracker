from pydantic import BaseModel
from datetime import date as date_type, datetime
from typing import Optional


class IntakeEventCreate(BaseModel):
    """What the frontend sends us when logging a new intake event."""
    date: date_type
    material_type: str
    volume_cy: float
    hauler: Optional[str] = None


class IntakeEventOut(BaseModel):
    """What we send back — logged_by and user_id are set by the server, not the client."""
    id: int
    date: date_type
    material_type: str
    volume_cy: float
    hauler: Optional[str] = None
    logged_by: Optional[str] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class BatchCreate(BaseModel):
    """What's sent when starting a new batch."""
    batch_label: str
    start_date: date_type
    end_date: Optional[date_type] = None
    finished_volume_cy: Optional[float] = None
    notes: Optional[str] = None


class BatchOut(BatchCreate):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    """What the frontend sees about the logged-in user — used to decide which UI to show."""
    id: int
    name: str
    role: str

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    """What a reviewer sends when flagging an entry."""
    body: str


class CommentOut(BaseModel):
    id: int
    body: str
    created_at: datetime
    author_name: str

    class Config:
        from_attributes = True
