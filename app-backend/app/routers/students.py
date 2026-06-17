from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from ..services.student import StudentService
from ..services.pdf_parser import PDFParser
from ..database import get_db

router = APIRouter(
    prefix="/students",
    tags=["students"],
)

@router.post("/", response_model=schemas.StudentResponse)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    """
    Cria um novo perfil de estudante e o usuário associado.

    Parâmetros de entrada:
        student (schemas.StudentCreate): Dados do estudante e do usuário correspondente.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.StudentResponse: O perfil de estudante criado.
    """
    service = StudentService(db)
    return service.create_student(student=student)

@router.get("/", response_model=List[schemas.StudentResponse])
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna uma lista paginada de todos os estudantes cadastrados.

    Parâmetros de entrada:
        skip (int): Quantidade de registros a pular.
        limit (int): Número máximo de registros a retornar.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.StudentResponse]: Lista de estudantes cadastrados.
    """
    service = StudentService(db)
    return service.get_students(skip=skip, limit=limit)

@router.post("/{student_id}/wishlist", response_model=schemas.StudentResponse)
def update_student_wishlist(student_id: int, course_ids: List[int], db: Session = Depends(get_db)):
    """
    Atualiza a lista de desejos (wishlist) de disciplinas do estudante.

    Parâmetros de entrada:
        student_id (int): O ID do estudante.
        course_ids (List[int]): Lista com IDs de disciplinas desejadas.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.StudentResponse: O objeto do estudante atualizado.
    """
    service = StudentService(db)
    student = service.update_wishlist(student_id=student_id, course_ids=course_ids)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/{student_id}/desired-courses", response_model=List[schemas.CourseResponse])
def get_student_desired_courses(student_id: int, db: Session = Depends(get_db)):
    """
    Consulta todas as disciplinas da lista de desejos do estudante.

    Parâmetros de entrada:
        student_id (int): O ID do estudante.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.CourseResponse]: Lista de disciplinas desejadas.
    """
    service = StudentService(db)
    return service.get_wishlist_courses(student_id=student_id)


@router.post("/{student_id}/desired-courses", response_model=schemas.StudentResponse)
def update_student_desired_courses(
    student_id: int,
    payload: schemas.StudentDesiredCoursesUpdate,
    db: Session = Depends(get_db),
):
    """
    Atualiza as disciplinas desejadas a partir do payload da API.

    Parâmetros de entrada:
        student_id (int): O ID do estudante.
        payload (schemas.StudentDesiredCoursesUpdate): Payload contendo a lista de IDs das disciplinas desejadas.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.StudentResponse: O objeto do estudante atualizado.
    """
    service = StudentService(db)
    student = service.update_wishlist(student_id=student_id, course_ids=payload.course_ids)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.get("/{student_id}/eligible-courses", response_model=List[schemas.CourseResponse])
def get_eligible_courses(student_id: int, db: Session = Depends(get_db)):
    """
    Retorna as disciplinas que o estudante está elegível para cursar no momento.

    Parâmetros de entrada:
        student_id (int): O ID do estudante.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.CourseResponse]: Lista das disciplinas elegíveis.
    """
    service = StudentService(db)
    eligible = service.get_eligible_courses(student_id=student_id)
    if eligible is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return eligible

@router.get("/{student_id}/completed-courses", response_model=List[schemas.CourseResponse])
def get_completed_courses(student_id: int, db: Session = Depends(get_db)):
    """
    Consulta as disciplinas já concluídas (aprovadas/dispensadas) pelo estudante.

    Parâmetros de entrada:
        student_id (int): O ID do estudante.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.CourseResponse]: Lista de disciplinas concluídas.
    """
    service = StudentService(db)
    student = service.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return [cc.course for cc in student.completed_courses if cc.course is not None]

@router.post("/{student_id}/completed-courses", response_model=schemas.StudentResponse)
def update_student_completed_courses(
    student_id: int,
    course_ids: List[int] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Atualiza manualmente a lista de disciplinas concluídas do estudante informando os seus IDs.

    Parâmetros de entrada:
        student_id (int): O ID do estudante.
        course_ids (List[int]): Lista de IDs das disciplinas concluídas.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.StudentResponse: O objeto do estudante atualizado.
    """
    service = StudentService(db)
    student = service.update_completed_courses(student_id=student_id, course_ids=course_ids)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/{student_id}/completed-courses/upload-pdf", response_model=List[schemas.CourseResponse])
def upload_completed_courses_pdf(
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Recebe um histórico escolar em formato PDF da UFRGS, faz o parse de suas disciplinas concluídas
    e atualiza a lista correspondente no perfil do estudante.

    Parâmetros de entrada:
        student_id (int): O ID do estudante.
        file (UploadFile): Arquivo PDF contendo o histórico escolar.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.CourseResponse]: Lista das disciplinas associadas como concluídas ao perfil após o parse.
    """
    service = StudentService(db)
    student = service.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        pdf_bytes = file.file.read()
        from .. import models
        all_courses = db.query(models.Course).all()
        parser = PDFParser(db)
        completed_codes = parser.parse_pdf_completed_courses(pdf_bytes, expected_course=student.course, db_courses=all_courses)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing PDF file: {str(e)}")

    updated_courses = service.update_completed_courses_from_codes(student_id=student_id, codes=completed_codes)
    return updated_courses

@router.get("/{student_id}/curriculum", response_model=List[schemas.CourseResponse])
def get_student_curriculum(student_id: int, db: Session = Depends(get_db)):
    """
    Retorna a grade curricular/currículo de curso do estudante.

    Parâmetros de entrada:
        student_id (int): O ID do estudante.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.CourseResponse]: Lista das disciplinas do currículo mapeado do aluno.
    """
    service = StudentService(db)
    curriculum = service.get_student_curriculum(student_id=student_id)
    if curriculum is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return curriculum
