from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from ..services.poll import PollService
from ..database import get_db

router = APIRouter(
    prefix="/polls",
    tags=["polls"],
)


@router.post("/", response_model=schemas.PollResponse)
def create_poll(poll: schemas.PollCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova enquete de solicitação de abertura de turma para uma disciplina específica.

    Parâmetros de entrada:
        poll (schemas.PollCreate): Corpo da requisição contendo ID do criador, ID da disciplina e slots sugeridos.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.PollResponse: A enquete criada no banco de dados.
    """
    service = PollService(db)
    return service.create_poll(poll=poll)


@router.get("/", response_model=List[schemas.PollWithVoteCount])
def list_polls(student_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna a lista de enquetes abertas nas quais o estudante é elegível para participar.

    Parâmetros de entrada:
        student_id (int): O ID do usuário estudante.
        skip (int): Quantidade de enquetes a pular para paginação.
        limit (int): Limite máximo de enquetes a retornar.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.PollWithVoteCount]: Lista de enquetes correspondentes com contagem de votos.
    """
    service = PollService(db)
    return service.get_polls(student_id=student_id, skip=skip, limit=limit)


@router.get("/all", response_model=List[schemas.PollWithVoteCount])
def get_all_polls_for_admin(db: Session = Depends(get_db)):
    """
    Retorna a lista de todas as enquetes cadastradas sem filtros de elegibilidade (visão de administrador/comgrad).

    Parâmetros de entrada:
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        List[schemas.PollWithVoteCount]: Lista de todas as enquetes com suas contagens de votos.
    """
    service = PollService(db)
    return service.get_all_polls()


@router.get("/summary", response_model=schemas.PollSummaryResponse)
def get_poll_summary(db: Session = Depends(get_db)):
    """
    Retorna o resumo estatístico contendo a contagem de enquetes totais, aprovadas e negadas/encerradas.

    Parâmetros de entrada:
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.PollSummaryResponse: Objeto com as estatísticas de enquetes.
    """
    service = PollService(db)
    return service.get_summary()


@router.get("/{poll_id}", response_model=schemas.PollWithVoteCount)
def get_poll(poll_id: int, student_id: int, db: Session = Depends(get_db)):
    """
    Consulta os detalhes de uma enquete específica.

    Parâmetros de entrada:
        poll_id (int): ID da enquete.
        student_id (int): ID do estudante consultando.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.PollWithVoteCount: Detalhes da enquete consultada com contagem de votos.
    """
    service = PollService(db)
    return service.get_poll(poll_id=poll_id, student_id=student_id)


@router.post("/{poll_id}/votes", response_model=schemas.PollVoteResponse)
def add_vote(poll_id: int, vote: schemas.PollVoteCreate, db: Session = Depends(get_db)):
    """
    Adiciona o voto de um estudante em uma enquete aberta.

    Parâmetros de entrada:
        poll_id (int): ID da enquete.
        vote (schemas.PollVoteCreate): Dados do voto contendo o ID do estudante.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.PollVoteResponse: O voto cadastrado no banco de dados.
    """
    service = PollService(db)
    return service.add_vote(poll_id=poll_id, vote=vote)


@router.delete("/{poll_id}/votes/{student_id}", status_code=204)
def remove_vote(poll_id: int, student_id: int, db: Session = Depends(get_db)):
    """
    Remove o voto de um estudante em uma enquete aberta. Retorna status 204 se removido com sucesso,
    ou gera um erro 404 caso não seja encontrado.

    Parâmetros de entrada:
        poll_id (int): ID da enquete.
        student_id (int): ID do estudante.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        Nenhum.
    """
    service = PollService(db)
    removed = service.remove_vote(poll_id=poll_id, student_id=student_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Voto não encontrado")


@router.post("/{poll_id}/review", response_model=schemas.PollResponse)
def review_poll(poll_id: int, review: schemas.PollReview, db: Session = Depends(get_db)):
    """
    Registra a revisão e parecer da comissão de curso (Comgrad/Admin) sobre uma enquete de solicitação.

    Parâmetros de entrada:
        poll_id (int): ID da enquete a ser revisada.
        review (schemas.PollReview): Dados do parecer, novo status e ID do revisor.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        schemas.PollResponse: A enquete atualizada com a resposta da comissão.
    """
    service = PollService(db)
    return service.review_poll(poll_id=poll_id, review=review)
