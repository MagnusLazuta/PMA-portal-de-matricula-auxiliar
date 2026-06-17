from sqlalchemy import Column, Integer, String, Time, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class ClassRequestPoll(Base):
    __tablename__ = "class_request_poll"

    id = Column(Integer, primary_key=True, index=True)
    creator_student_id = Column(Integer, ForeignKey("student.user_id"))
    course_id = Column(Integer, ForeignKey("course.id"))
    
    suggested_day_of_week = Column(String)
    suggested_start_time = Column(Time)
    suggested_end_time = Column(Time)
    # New: store multiple suggested slots as JSON string: [{"day":"Monday","start":"08:30","end":"10:10"}, ...]
    suggested_slots = Column(Text)
    
    voting_deadline = Column(DateTime)
    status = Column(String) # Ex: 'Open', 'Closed', 'Approved'
    
    committee_response = Column(Text)
    committee_member_id = Column(Integer, ForeignKey("comgrad.user_id"))
    response_date = Column(DateTime)

    creator = relationship("Student", back_populates="polls_created")
    course = relationship("Course", back_populates="polls")
    committee_member = relationship("COMGRAD", back_populates="poll_responses")
    votes = relationship("PollVote", back_populates="poll")

    @property
    def voted_student_ids(self) -> list[int]:
        return [v.student_id for v in self.votes]


class PollVote(Base):
    __tablename__ = "poll_vote"

    poll_id = Column(Integer, ForeignKey("class_request_poll.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("student.user_id"), primary_key=True)
    vote_date = Column(DateTime, default=datetime.utcnow)

    poll = relationship("ClassRequestPoll", back_populates="votes")
    student = relationship("Student", back_populates="poll_votes")
