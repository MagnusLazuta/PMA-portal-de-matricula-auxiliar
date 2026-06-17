from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from ..services.restriction import TimeRestrictionService
from ..database import get_db

router = APIRouter(
    prefix="/restrictions",
    tags=["restrictions"],
)

@router.post("/", response_model=schemas.TimeRestrictionResponse)
def create_restriction(restriction: schemas.TimeRestrictionCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova restrição de horário ou preferência associada a um estudante.

    Parâmetros de entrada:
        restriction (schemas.TimeRestrictionCreate): Dados da nova restrição.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.TimeRestrictionResponse: A restrição cadastrada no banco de dados.
    """
    service = TimeRestrictionService(db)
    return service.create_restriction(restriction=restriction)

@router.get("/", response_model=List[schemas.TimeRestrictionResponse])
def read_restrictions(student_id: int | None = None, db: Session = Depends(get_db)):
    """
    Retorna a lista de restrições ou preferências cadastradas, opcionalmente filtrada por um estudante.

    Parâmetros de entrada:
        student_id (int | None): ID do estudante para filtrar (opcional).
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.TimeRestrictionResponse]: Lista de restrições encontradas.
    """
    service = TimeRestrictionService(db)
    return service.get_all_restrictions(student_id=student_id)


@router.delete("/{restriction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restriction(restriction_id: int, db: Session = Depends(get_db)):
    """
    Exclui uma restrição de horário ou preferência pelo ID. Retorna status 204 se excluída com sucesso,
    ou gera um erro 404 caso não seja encontrada.

    Parâmetros de entrada:
        restriction_id (int): O ID da restrição a ser deletada.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        Response: Objeto Response com status HTTP 204 No Content.
    """
    service = TimeRestrictionService(db)
    deleted = service.delete_restriction(restriction_id=restriction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Restriction not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
