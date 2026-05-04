from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from .crud import CourseService, OfferingService, RestrictionService, StudentService
from . import models, schemas
from .database import SessionLocal, engine
from .scheduler import ScheduleGenerator

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS for frontend requests during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/courses/bulk", response_model=List[schemas.CourseResponse])
def create_courses_bulk(
    courses: List[schemas.CourseCreate],
    db: Session = Depends(get_db)
):
    service = CourseService(db)
    return service.create_courses_bulk(courses=courses)

@app.post("/courses/", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    service = CourseService(db)
    return service.create_course(course=course)

@app.get("/courses/", response_model=List[schemas.CourseResponse])
def read_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = CourseService(db)
    return service.get_courses(skip=skip, limit=limit)

@app.post("/students/", response_model=schemas.StudentResponse)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    service = StudentService(db)
    return service.create_student(student=student)

@app.get("/students/", response_model=List[schemas.StudentResponse])
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = StudentService(db)
    return service.get_students(skip=skip, limit=limit)

@app.post("/students/{student_id}/desired-courses", response_model=schemas.StudentResponse)
def set_student_desired_courses(student_id: int, data: schemas.StudentDesiredCoursesUpdate, db: Session = Depends(get_db)):
    service = StudentService(db)
    student = service.update_desired_courses(student_id=student_id, course_ids=data.course_ids)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.get("/students/{student_id}/desired-courses", response_model=List[schemas.CourseResponse])
def read_student_desired_courses(student_id: int, db: Session = Depends(get_db)):
    service = StudentService(db)
    courses = service.get_desired_courses(student_id=student_id)
    if courses is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return courses

@app.post("/offerings/", response_model=schemas.OfferingResponse)
def create_offering(offering: schemas.OfferingCreate, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return service.create_offering(offering=offering)

@app.post("/offerings/bulk", response_model=List[schemas.OfferingResponse])
def create_offerings_bulk(
    offerings: List[schemas.OfferingCreate],
    db: Session = Depends(get_db)
):
    service = OfferingService(db)
    return service.create_offerings_bulk(offerings=offerings)

@app.get("/offerings/", response_model=List[schemas.OfferingResponse])
def read_offerings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return service.get_offerings(skip=skip, limit=limit)


@app.get("/courses/{course_id}/offerings/", response_model=List[schemas.OfferingResponse])
def read_offerings_by_course(course_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return service.get_offerings_by_course(course_id=course_id, skip=skip, limit=limit)


@app.get("/days-of-week/", response_model=List[schemas.DayOfWeek])
def read_days_of_week():
    return list(schemas.DayOfWeek)

@app.post("/restrictions/", response_model=schemas.RestrictionResponse)
def create_restriction(restriction: schemas.RestrictionCreate, db: Session = Depends(get_db)):
    service = RestrictionService(db)
    return service.create_restriction(restriction=restriction)

@app.post("/restrictions/bulk", response_model=List[schemas.RestrictionResponse])
def create_restrictions_bulk(
    restrictions: List[schemas.RestrictionCreate],
    db: Session = Depends(get_db)
):
    service = RestrictionService(db)
    return service.create_restrictions_bulk(restrictions=restrictions)

@app.get("/restrictions/", response_model=List[schemas.RestrictionResponse])
def read_restrictions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = RestrictionService(db)
    return service.get_restrictions(skip=skip, limit=limit)


@app.delete("/restrictions/{restriction_id}", response_model=schemas.RestrictionResponse)
def delete_restriction(restriction_id: int, db: Session = Depends(get_db)):
    service = RestrictionService(db)
    restriction = service.delete_restriction(restriction_id=restriction_id)
    if restriction is None:
        raise HTTPException(status_code=404, detail="Restriction not found")
    return restriction

@app.post("/generate-schedules/", response_model=List[List[schemas.ScheduleItem]])
def generate_schedules(request: schemas.ScheduleRequest, db: Session = Depends(get_db)):
    generator = ScheduleGenerator(db)
    schedules = generator.generate_possible_schedules(request.student_id)
    return schedules