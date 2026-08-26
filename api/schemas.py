from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class ReadingCreate(BaseModel):
    device_id:UUID
    temp_c:float = Field(ge=-80, le =80)
    humidity:float = Field (ge = 0, le =100)
    ts: datetime | None = None
    token:str;

class ReadingResponse(BaseModel):
    id:int #table id of db
    ts: datetime
    quality:str
    device_id:UUID
    temp_c:float = Field(ge=-80, le =80)
    humidity:float = Field (ge = 0, le =100)
    ts: datetime | None = None;