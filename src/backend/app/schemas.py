from enum import Enum
from typing import List
from pydantic import BaseModel


class DayOfWeek(str, Enum):
    MONDAY = "Segunda-feira"
    TUESDAY = "Terça-feira"
    WEDNESDAY = "Quarta-feira"
    THURSDAY = "Quinta-feira"
    FRIDAY = "Sexta-feira"
    SATURDAY = "Sábado"
    SUNDAY = "Domingo"

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            return None

        normalized = value.strip().lower()
        legacy_values = {
            "seg": cls.MONDAY,
            "segunda": cls.MONDAY,
            "segunda-feira": cls.MONDAY,
            "ter": cls.TUESDAY,
            "terca": cls.TUESDAY,
            "terça": cls.TUESDAY,
            "terça-feira": cls.TUESDAY,
            "qua": cls.WEDNESDAY,
            "quarta": cls.WEDNESDAY,
            "quarta-feira": cls.WEDNESDAY,
            "qui": cls.THURSDAY,
            "quinta": cls.THURSDAY,
            "quinta-feira": cls.THURSDAY,
            "sex": cls.FRIDAY,
            "sexta": cls.FRIDAY,
            "sexta-feira": cls.FRIDAY,
            "sab": cls.SATURDAY,
            "sábado": cls.SATURDAY,
            "sabado": cls.SATURDAY,
            "dom": cls.SUNDAY,
            "domingo": cls.SUNDAY,
        }
        return legacy_values.get(normalized)

class CourseBase(BaseModel):
    name: str
    code: str

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int

    class Config:
        orm_mode = True

class OfferingBase(BaseModel):
    course_id: int
    day_of_week: DayOfWeek
    start_time: str
    end_time: str

class OfferingCreate(OfferingBase):
    pass

class OfferingResponse(OfferingBase):
    id: int

    class Config:
        orm_mode = True

class RestrictionBase(BaseModel):
    day_of_week: DayOfWeek
    start_time: str
    end_time: str

class RestrictionCreate(RestrictionBase):
    pass

class RestrictionResponse(RestrictionBase):
    id: int

    class Config:
        orm_mode = True

class StudentBase(BaseModel):
    name: str

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    desired_courses: List[CourseResponse] = []

    class Config:
        orm_mode = True

class StudentDesiredCoursesUpdate(BaseModel):
    course_ids: List[int]

class ScheduleRequest(BaseModel):
    student_id: int

class ScheduleItem(BaseModel):
    offering_id: int
    course_id: int
    course_name: str
    course_code: str
    day_of_week: DayOfWeek
    start_time: str
    end_time: str

    class Config:
        orm_mode = True