from typing import List
from sqlalchemy.orm import Session
from . import models, schemas

class BaseService:
    def __init__(self, db: Session):
        self.db = db

class CourseService(BaseService):
    def create_course(self, course: schemas.CourseCreate) -> models.Course:
        db_course = models.Course(name=course.name, code=course.code)
        self.db.add(db_course)
        self.db.commit()
        self.db.refresh(db_course)
        return db_course

    def create_courses_bulk(self, courses: list[schemas.CourseCreate]) -> List[models.Course]:
        db_courses = [models.Course(name=c.name, code=c.code) for c in courses]
        self.db.add_all(db_courses)
        self.db.commit()
        for course in db_courses:
            self.db.refresh(course)
        return db_courses

    def get_courses(self, skip: int = 0, limit: int = 100) -> List[models.Course]:
        return self.db.query(models.Course).offset(skip).limit(limit).all()

class StudentService(BaseService):
    def create_student(self, student: schemas.StudentCreate) -> models.Student:
        db_student = models.Student(name=student.name)
        self.db.add(db_student)
        self.db.commit()
        self.db.refresh(db_student)
        return db_student

    def get_students(self, skip: int = 0, limit: int = 100) -> List[models.Student]:
        return self.db.query(models.Student).offset(skip).limit(limit).all()

    def get_student(self, student_id: int) -> models.Student | None:
        return self.db.query(models.Student).filter(models.Student.id == student_id).first()

    def update_desired_courses(self, student_id: int, course_ids: list[int]) -> models.Student | None:
        student = self.get_student(student_id)
        if student is None:
            return None

        courses = self.db.query(models.Course).filter(models.Course.id.in_(course_ids)).all()
        student.desired_courses = courses
        self.db.commit()
        self.db.refresh(student)
        return student

    def get_desired_courses(self, student_id: int) -> list[models.Course] | None:
        student = self.get_student(student_id)
        if student is None:
            return None

        return student.desired_courses

class OfferingService(BaseService):
    def create_offering(self, offering: schemas.OfferingCreate) -> models.Offering:
        db_offering = models.Offering(**offering.dict())
        self.db.add(db_offering)
        self.db.commit()
        self.db.refresh(db_offering)
        return db_offering

    def create_offerings_bulk(self, offerings: list[schemas.OfferingCreate]) -> List[models.Offering]:
        db_offerings = [models.Offering(**o.dict()) for o in offerings]
        self.db.add_all(db_offerings)
        self.db.commit()
        for offering in db_offerings:
            self.db.refresh(offering)
        return db_offerings

    def get_offerings(self, skip: int = 0, limit: int = 100) -> List[models.Offering]:
        return self.db.query(models.Offering).offset(skip).limit(limit).all()

    def get_all_offerings(self) -> List[models.Offering]:
        return self.db.query(models.Offering).all()

    def get_offerings_by_course(self, course_id: int, skip: int = 0, limit: int = 100) -> List[models.Offering]:
        return (
            self.db.query(models.Offering)
            .filter(models.Offering.course_id == course_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

class RestrictionService(BaseService):
    def create_restriction(self, restriction: schemas.RestrictionCreate) -> models.Restriction:
        db_restriction = models.Restriction(**restriction.dict())
        self.db.add(db_restriction)
        self.db.commit()
        self.db.refresh(db_restriction)
        return db_restriction

    def create_restrictions_bulk(self, restrictions: list[schemas.RestrictionCreate]) -> List[models.Restriction]:
        db_restrictions = [models.Restriction(**r.dict()) for r in restrictions]
        self.db.add_all(db_restrictions)
        self.db.commit()
        for restriction in db_restrictions:
            self.db.refresh(restriction)
        return db_restrictions

    def delete_restriction(self, restriction_id: int) -> models.Restriction | None:
        restriction = (
            self.db.query(models.Restriction)
            .filter(models.Restriction.id == restriction_id)
            .first()
        )
        if restriction is None:
            return None

        self.db.delete(restriction)
        self.db.commit()
        return restriction

    def get_restrictions(self, skip: int = 0, limit: int = 100) -> List[models.Restriction]:
        return self.db.query(models.Restriction).offset(skip).limit(limit).all()

    def get_all_restrictions(self) -> List[models.Restriction]:
        return self.db.query(models.Restriction).all()

