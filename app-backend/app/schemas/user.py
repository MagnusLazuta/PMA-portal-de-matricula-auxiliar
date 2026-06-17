from pydantic import BaseModel, ConfigDict
from datetime import date

class UserBase(BaseModel):
    name: str
    email: str
    card_number: int

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    date_created: date

    model_config = ConfigDict(from_attributes=True)
