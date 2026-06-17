from sqlalchemy import Column, Integer, String, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base

# Association table for Many-to-Many (Prerequisites)
course_prerequisite = Table(
    "course_prerequisite",
    Base.metadata,
    Column("course_id", Integer, ForeignKey("course.id"), primary_key=True),
    Column("prerequisite_id", Integer, ForeignKey("course.id"), primary_key=True),
)

class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    credits = Column(Integer)
    min_credits_required = Column(Integer)

    # Relationships
    prerequisites = relationship(
        "Course",
        secondary=course_prerequisite,
        primaryjoin=id == course_prerequisite.c.course_id,
        secondaryjoin=id == course_prerequisite.c.prerequisite_id,
        backref="required_by"
    )
    
    sections = relationship("ClassSection", back_populates="course")
    wishlisted_by = relationship("CourseWishlist", back_populates="course")
    completed_by = relationship("CompletedCourse", back_populates="course")
    polls = relationship("ClassRequestPoll", back_populates="course")


class CourseWishlist(Base):
    __tablename__ = "course_wishlist"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.user_id"))
    course_id = Column(Integer, ForeignKey("course.id"))

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="_student_course_uc"),)

    student = relationship("Student", back_populates="wishlist")
    course = relationship("Course", back_populates="wishlisted_by")
