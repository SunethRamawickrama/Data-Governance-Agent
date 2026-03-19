from pydantic import BaseModel
from typing import Optional, Dict, Any


class DataSourceCreate(BaseModel):
    name: str
    source_type: str

    host: Optional[str] = None
    port: Optional[int] = None
    source_name: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = None