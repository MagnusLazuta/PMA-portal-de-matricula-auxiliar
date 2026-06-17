from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from ..services.section import ClassSectionService
from ..database import get_db

router = APIRouter(
    prefix="/sections",
    tags=["sections"],
)

@router.post("/", response_model=schemas.ClassSectionResponse)
def create_section(section: schemas.ClassSectionCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova turma (ClassSection) com seus respectivos horários de aula.

    Parâmetros de entrada:
        section (schemas.ClassSectionCreate): Corpo da requisição contendo dados da turma e horários.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.ClassSectionResponse: A turma cadastrada no banco de dados.
    """
    service = ClassSectionService(db)
    return service.create_section(section=section)

@router.get("/", response_model=List[schemas.ClassSectionResponse])
def read_sections(semester: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna a lista de turmas cadastradas, opcionalmente filtrada por semestre acadêmico ou paginada.

    Parâmetros de entrada:
        semester (str): O semestre acadêmico para filtrar (opcional).
        skip (int): Quantidade de turmas a pular para paginação.
        limit (int): Número máximo de turmas a retornar.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.ClassSectionResponse]: Lista de turmas encontradas.
    """
    service = ClassSectionService(db)
    if semester:
        return service.get_all_sections(semester=semester)
    return service.get_sections(skip=skip, limit=limit)

@router.get("/semesters", response_model=List[str])
def get_available_semesters(db: Session = Depends(get_db)):
    """
    Retorna a lista de todos os semestres acadêmicos distintos que possuem turmas cadastradas,
    ordenados de forma decrescente (do mais recente para o mais antigo).

    Parâmetros de entrada:
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[str]: Lista de strings dos semestres disponíveis (ex: ["2026/1", "2025/2"]).
    """
    from .. import models
    semesters = db.query(models.ClassSection.semester).distinct().all()
    semester_list = [s[0] for s in semesters if s[0]]
    def semester_key(sem_str):
        """
        Função auxiliar interna para converter strings de semestres (ex: '2026/1') em tuplas numéricas
        para ordenação correta.

        Parâmetros de entrada:
            sem_str (str): String do semestre acadêmico.

        Parâmetros de saída:
            tuple (int, int): Tupla contendo o ano e o período.
        """
        try:
            parts = sem_str.split('/')
            return (int(parts[0]), int(parts[1]))
        except Exception:
            return (0, 0)
    semester_list.sort(key=semester_key, reverse=True)
    return semester_list
