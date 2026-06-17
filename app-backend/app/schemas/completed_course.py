from pydantic import BaseModel, ConfigDict

class CompletedCourseBase(BaseModel):
    student_id: int
    course_id: int

class CompletedCourseCreate(CompletedCourseBase):
    pass

class CompletedCourseResponse(CompletedCourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
