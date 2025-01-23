from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SecurityWaitTime(BaseModel):
    terminal: str
    general_line: str
    tsa_pre: str
    timestamp: datetime

class ErrorResponse(BaseModel):
    detail: str