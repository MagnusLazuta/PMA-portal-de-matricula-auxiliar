from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import time, datetime
from .enums import DayOfWeek


class SuggestedSlot(BaseModel):
    suggested_day_of_week: DayOfWeek
    suggested_start_time: time
    suggested_end_time: time


class PollBase(BaseModel):
    course_id: int
    suggested_slots: List[SuggestedSlot]
    voting_deadline: Optional[datetime] = None

class PollCreate(PollBase):
    creator_student_id: int

class PollResponse(PollBase):
    id: int
    creator_student_id: int
    status: str
    committee_response: Optional[str] = None
    committee_member_id: Optional[int] = None
    response_date: Optional[datetime] = None
    voted_student_ids: List[int] = []
    # keep legacy single-slot fields optional for compatibility
    suggested_day_of_week: Optional[DayOfWeek] = None
    suggested_start_time: Optional[time] = None
    suggested_end_time: Optional[time] = None

    model_config = ConfigDict(from_attributes=True)

class WishlistCreate(BaseModel):
    student_id: int
    course_id: int


class PollVoteCreate(BaseModel):
    student_id: int


class PollVoteResponse(BaseModel):
    poll_id: int
    student_id: int
    vote_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PollWithVoteCount(PollResponse):
    vote_count: int


class PollSummaryResponse(BaseModel):
    total_polls: int
    approved_polls: int
    denied_polls: int


class PollReview(BaseModel):
    committee_response: str
    status: str
    committee_member_id: int

