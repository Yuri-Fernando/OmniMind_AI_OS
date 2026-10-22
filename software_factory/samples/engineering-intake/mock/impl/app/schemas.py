"""DTOs da Engineering Intake API."""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

JobStatus = Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED"]
ALLOWED_EXTENSIONS = {".dxf", ".pdf", ".png", ".tif", ".tiff", ".txt"}


class DocumentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1, max_length=255)
    content: str
    idempotency_key: str = Field(min_length=1, max_length=128)
    metadata: Dict[str, str] = Field(default_factory=dict)


class JobAccepted(BaseModel):
    job_id: str
    status: JobStatus
    idempotent_replay: bool = False


class JobEvent(BaseModel):
    event: str
    error_code: Optional[str] = None
    at: str


class JobOut(BaseModel):
    job_id: str
    status: JobStatus
    filename: str
    events: List[JobEvent]
