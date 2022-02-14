from .config import cfgparser

config = cfgparser["DEFAULT"]

from pydantic import BaseModel
from typing import Optional


class Status(BaseModel):
    status: bool
    message: Optional[str]
