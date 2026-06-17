from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    card_number = Column(Integer, unique=True, index=True)
    password = Column(String)
    date_created = Column(Date, default=datetime.utcnow)
    must_change_password = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relacionamentos One-to-One (Joined Table-like)
    student = relationship("Student", back_populates="user", uselist=False)
    admin = relationship("Admin", back_populates="user", uselist=False)
    comgrad = relationship("COMGRAD", back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "student"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    current_semester = Column(Integer)
    course = Column(String)
    curriculum_id = Column(Integer, ForeignKey("curriculum.id"), nullable=True)

    user = relationship("User", back_populates="student")
    curriculum_obj = relationship("Curriculum", back_populates="students")
    
    # Atividades do estudante
    completed_courses = relationship("CompletedCourse", back_populates="student")
    wishlist = relationship("CourseWishlist", back_populates="student")
    restrictions = relationship("TimeRestriction", back_populates="student")
    polls_created = relationship("ClassRequestPoll", back_populates="creator")
    poll_votes = relationship("PollVote", back_populates="student")


class Admin(Base):
    __tablename__ = "admin"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="admin")


class COMGRAD(Base):
    __tablename__ = "comgrad"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String)

    user = relationship("User", back_populates="comgrad")
    poll_responses = relationship("ClassRequestPoll", back_populates="committee_member")
