from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from ..database import get_db
from ..services.scheduler import ScheduleGenerator

router = APIRouter(
    prefix="/generate-schedules",
    tags=["scheduler"],
)

@router.post("/", response_model=List[List[schemas.ScheduleItem]])
def generate_schedules(request: schemas.ScheduleRequest, db: Session = Depends(get_db)):
    """
    Gera opções de grades de horários (schedules) candidatas para um estudante, retornando apenas a lista de turmas por opção.

    Parâmetros de entrada:
        request (schemas.ScheduleRequest): Corpo da requisição contendo ID do estudante, limite de opções e semestre opcional.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[List[schemas.ScheduleItem]]: Lista contendo as opções de grades, em que cada opção é uma lista de turmas estruturadas.
    """
    generator = ScheduleGenerator(db)
    schedules = generator.generate_possible_schedules(request.student_id, limit=request.limit, semester=request.semester)
    return schedules


@router.post("/ranked", response_model=List[schemas.RankedScheduleOption])
def generate_ranked_schedules(request: schemas.ScheduleRequest, db: Session = Depends(get_db)):
    """
    Gera opções de grades de horários candidatas para um estudante, retornando a pontuação e metadados de relevância para ranqueamento.

    Parâmetros de entrada:
        request (schemas.ScheduleRequest): Corpo da requisição contendo ID do estudante, limite de opções e semestre opcional.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.RankedScheduleOption]: Lista contendo as opções de grades ranqueadas com suas respectivas pontuações.
    """
    generator = ScheduleGenerator(db)
    return generator.generate_ranked_schedules(request.student_id, limit=request.limit, semester=request.semester)
