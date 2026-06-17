from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import time
from .enums import DayOfWeek

class ClassScheduleBase(BaseModel):
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    room: Optional[str] = None

class ClassScheduleCreate(ClassScheduleBase):
    pass

class ClassScheduleResponse(ClassScheduleBase):
    id: int
    class_section_id: int

    model_config = ConfigDict(from_attributes=True)
