from pydantic import BaseModel, ConfigDict
from .user import UserCreate, UserResponse

class StudentBase(BaseModel):
    current_semester: int
    course: str

class StudentCreate(StudentBase):
    user: UserCreate

class StudentResponse(StudentBase):
    user_id: int
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)
