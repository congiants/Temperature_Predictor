from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import UUID

class ReadingCreate(BaseModel):
    device_id:UUID
    temp_c:float = Field(ge=-80, le =80)
    humidity:float = Field (ge = 0, le =100)
    ts: datetime | None = None

class ReadingResponse(BaseModel):
    id:int #table id of db
    quality:str
    device_id:UUID
    temp_c:float = Field(ge=-80, le =80)
    humidity:float = Field (ge = 0, le =100)
    ts: datetime | None = None;


class DeviceCreate(BaseModel):
    display_name:str
    location:str | None = None
    firmware_version:str | None = None

class DeviceResponse(BaseModel):
    device_id:UUID
    token:str
    display_name:str
    status:str

class DeviceListItem(BaseModel):
    device_id:UUID
    display_name:str | None = None
    status:str
    location:str | None = None
    last_seen: datetime | None = None

class PredictionResponse(BaseModel):
    device_id:UUID
    based_on_date: date
    target_date: date
    temp_c_max: float |None = Field(ge=-100, le =80) 
    temp_c_min: float | None = Field(ge=-100, le =80) 
    model:str
    created_at: datetime | None = None
