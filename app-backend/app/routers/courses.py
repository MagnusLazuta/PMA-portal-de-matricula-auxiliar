from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from ..services.course import CourseService
from ..database import get_db

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)

@router.post("/bulk", response_model=List[schemas.CourseResponse])
def create_courses_bulk(
    courses: List[schemas.CourseCreate],
    db: Session = Depends(get_db)
):
    """
    Cria múltiplas disciplinas em lote (bulk) no banco de dados.

    Parâmetros de entrada:
        courses (List[schemas.CourseCreate]): Lista de objetos contendo os dados das disciplinas a serem criadas.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.CourseResponse]: Lista de disciplinas criadas no banco de dados.
    """
    service = CourseService(db)
    return service.create_courses_bulk(courses=courses)

@router.post("/", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    """
    Cria uma única nova disciplina no banco de dados.

    Parâmetros de entrada:
        course (schemas.CourseCreate): Corpo da requisição contendo os dados da disciplina.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.CourseResponse: A disciplina cadastrada no banco de dados.
    """
    service = CourseService(db)
    return service.create_course(course=course)

@router.get("/curricula", response_model=List[schemas.CurriculumResponse])
def read_curricula(db: Session = Depends(get_db)):
    """
    Consulta todos os currículos (grades curriculares) disponíveis no banco de dados.

    Parâmetros de entrada:
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.CurriculumResponse]: Lista contendo todos os currículos encontrados.
    """
    service = CourseService(db)
    return service.get_curricula()

@router.get("/", response_model=List[schemas.CourseResponse])
def read_courses(curriculum_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Consulta a lista de disciplinas cadastradas no banco de dados, opcionalmente filtrada por currículo.

    Parâmetros de entrada:
        curriculum_id (int | None): ID do currículo para filtrar (opcional).
        skip (int): Quantidade de disciplinas a pular para paginação.
        limit (int): Limite máximo de disciplinas a retornar.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.CourseResponse]: Lista de disciplinas encontradas.
    """
    service = CourseService(db)
    return service.get_courses(curriculum_id=curriculum_id, skip=skip, limit=limit)
