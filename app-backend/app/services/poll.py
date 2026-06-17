from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from .base import BaseService


class PollService(BaseService):

    def _is_eligible(self, student: models.Student, course: models.Course) -> bool:
        """
        Verifica se um estudante é elegível para uma disciplina com base nos pré-requisitos
        e se ele já não concluiu a disciplina anteriormente.

        Parâmetros de entrada:
            student (models.Student): Objeto de modelo do estudante.
            course (models.Course): Objeto de modelo da disciplina.

        Parâmetros de saída:
            bool: True se o estudante for elegível (não concluiu e possui todos os pré-requisitos), False caso contrário.
        """
        # IDs of courses already passed by the student
        passed_course_ids = {
            completed.course_id
            for completed in student.completed_courses
        }

        # Must not have already completed the course
        if course.id in passed_course_ids:
            return False

        # Must have met all prerequisites
        for prereq in course.prerequisites:
            if prereq.id not in passed_course_ids:
                return False

        return True

    def _get_student_or_404(self, student_id: int) -> models.Student:
        """
        Busca um estudante pelo ID do usuário no banco de dados ou levanta um erro 404 se não encontrado.

        Parâmetros de entrada:
            student_id (int): O ID do usuário associado ao estudante.

        Parâmetros de saída:
            models.Student: O objeto correspondente ao estudante encontrado.
        """
        student = self.db.query(models.Student).filter(
            models.Student.user_id == student_id
        ).first()
        if not student:
            raise HTTPException(status_code=404, detail="Estudante não encontrado")
        return student

    def _get_course_or_404(self, course_id: int) -> models.Course:
        """
        Busca uma disciplina pelo ID no banco de dados ou levanta um erro 404 se não encontrada.

        Parâmetros de entrada:
            course_id (int): O ID da disciplina.

        Parâmetros de saída:
            models.Course: O objeto da disciplina encontrada.
        """
        course = self.db.query(models.Course).filter(
            models.Course.id == course_id
        ).first()
        if not course:
            raise HTTPException(status_code=404, detail="Disciplina não encontrada")
        return course

    def _get_poll_or_404(self, poll_id: int) -> models.ClassRequestPoll:
        """
        Busca uma enquete de solicitação de turma pelo ID ou levanta um erro 404 se não encontrada.

        Parâmetros de entrada:
            poll_id (int): O ID da enquete.

        Parâmetros de saída:
            models.ClassRequestPoll: O objeto da enquete encontrada.
        """
        poll = self.db.query(models.ClassRequestPoll).filter(
            models.ClassRequestPoll.id == poll_id
        ).first()
        if not poll:
            raise HTTPException(status_code=404, detail="Enquete não encontrada")
        return poll

    def _check_and_close_expired_poll(self, poll: models.ClassRequestPoll) -> None:
        """
        Verifica se a enquete passou do prazo limite de votação. Se sim, altera seu status para "Closed".

        Parâmetros de entrada:
            poll (models.ClassRequestPoll): O objeto da enquete a ser verificado.

        Parâmetros de saída:
            Nenhum.
        """
        from datetime import datetime
        if poll.status == "Open" and poll.voting_deadline and datetime.utcnow() > poll.voting_deadline:
            poll.status = "Closed"
            self.db.commit()

    def create_poll(self, poll: schemas.PollCreate) -> models.ClassRequestPoll:
        """
        Cria uma nova enquete de solicitação de turma se o estudante for elegível,
        o formato dos slots de horário estiver correto e corresponder à carga horária da disciplina.

        Parâmetros de entrada:
            poll (schemas.PollCreate): Esquema de criação contendo as informações da enquete e slots sugeridos.

        Parâmetros de saída:
            models.ClassRequestPoll: O objeto da enquete criada e registrada no banco de dados.
        """
        student = self._get_student_or_404(poll.creator_student_id)
        course = self._get_course_or_404(poll.course_id)

        if not self._is_eligible(student, course):
            raise HTTPException(
                status_code=400,
                detail="Estudante não é elegível para criar enquete para esta disciplina"
            )

        # expected number of suggested slots depends on course credits (2->1,4->2,6->3)
        expected_slots = max(1, course.credits // 2)

        if not getattr(poll, 'suggested_slots', None) or not isinstance(poll.suggested_slots, list):
            raise HTTPException(status_code=400, detail="É necessário informar os intervalos de horário sugeridos")

        if len(poll.suggested_slots) != expected_slots:
            raise HTTPException(status_code=400, detail=f"Esta disciplina requer {expected_slots} intervalo(s) de horário (baseado em {course.credits} créditos)")

        # Validate each suggested slot is an allowed slot
        allowed_slots = {
            ('08:30', '10:10'),
            ('10:30', '12:10'),
            ('13:30', '15:10'),
            ('15:30', '17:10'),
            ('18:30', '20:10'),
            ('20:30', '22:10')
        }
        slot_tuples = []
        for slot in poll.suggested_slots:
            s_start = slot.suggested_start_time.strftime('%H:%M')
            s_end = slot.suggested_end_time.strftime('%H:%M')
            if (s_start, s_end) not in allowed_slots:
                raise HTTPException(status_code=400, detail=f"Intervalo de horário inválido: {s_start}-{s_end}")
            slot_tuples.append((slot.suggested_day_of_week, s_start, s_end))

        if len(set(slot_tuples)) != len(slot_tuples):
            raise HTTPException(status_code=400, detail="Não é permitido sugerir o mesmo dia e horário para múltiplos intervalos")

        from datetime import datetime, timedelta
        # voting_deadline is always 14 days after creation
        voting_deadline = datetime.utcnow() + timedelta(days=14)

        # Prepare data for DB: serialize suggested_slots as JSON string, and keep legacy single fields from first slot
        import json
        payload = poll.model_dump(exclude={'voting_deadline'})
        payload['voting_deadline'] = voting_deadline
        # set first slot legacy fields for backward compatibility
        first = poll.suggested_slots[0]
        payload['suggested_day_of_week'] = first.suggested_day_of_week
        payload['suggested_start_time'] = first.suggested_start_time
        payload['suggested_end_time'] = first.suggested_end_time
        payload['suggested_slots'] = json.dumps([
            {
                'suggested_day_of_week': s.suggested_day_of_week,
                'suggested_start_time': s.suggested_start_time.strftime('%H:%M'),
                'suggested_end_time': s.suggested_end_time.strftime('%H:%M')
            }
            for s in poll.suggested_slots
        ])

        db_poll = models.ClassRequestPoll(**payload, status="Open")
        self.db.add(db_poll)
        self.db.commit()
        self.db.refresh(db_poll)
        # expose parsed suggested_slots for response_model serialization
        try:
            import json
            if getattr(db_poll, 'suggested_slots', None):
                db_poll.suggested_slots = json.loads(db_poll.suggested_slots)
        except Exception:
            pass
        return db_poll

    def get_polls(self, student_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        Retorna as enquetes nas quais o estudante é elegível para participar.
        Verifica o prazo de cada enquete e a encerra se necessário.

        Parâmetros de entrada:
            student_id (int): O ID do usuário estudante que consulta.
            skip (int): Quantidade de registros a pular para paginação.
            limit (int): Número máximo de registros a retornar.

        Parâmetros de saída:
            List[dict]: Uma lista de dicionários contendo os dados das enquetes elegíveis.
        """
        student = self._get_student_or_404(student_id)
        all_polls = self.db.query(models.ClassRequestPoll).offset(skip).limit(limit).all()
        result = []
        import json
        for poll in all_polls:
            self._check_and_close_expired_poll(poll)
            course = self._get_course_or_404(poll.course_id)
            if self._is_eligible(student, course):
                entry = {
                    **{c.name: getattr(poll, c.name) for c in poll.__table__.columns},
                    "vote_count": len(poll.votes),
                    "voted_student_ids": poll.voted_student_ids
                }
                if entry.get('suggested_slots'):
                    try:
                        entry['suggested_slots'] = json.loads(entry['suggested_slots'])
                    except Exception:
                        pass
                result.append(entry)
        return result

    def get_poll(self, poll_id: int, student_id: int) -> dict:
        """
        Retorna os detalhes de uma enquete específica se o estudante for elegível para consultá-la.

        Parâmetros de entrada:
            poll_id (int): O ID da enquete.
            student_id (int): O ID do usuário estudante que consulta.

        Parâmetros de saída:
            dict: Um dicionário com os detalhes da enquete, contagem de votos e IDs dos estudantes votantes.
        """
        student = self._get_student_or_404(student_id)
        poll = self._get_poll_or_404(poll_id)
        self._check_and_close_expired_poll(poll)
        course = self._get_course_or_404(poll.course_id)

        if not self._is_eligible(student, course):
            raise HTTPException(
                status_code=403,
                detail="Estudante não é elegível para consultar esta enquete"
            )

        import json
        entry = {
            **{c.name: getattr(poll, c.name) for c in poll.__table__.columns},
            "vote_count": len(poll.votes),
            "voted_student_ids": poll.voted_student_ids
        }
        if entry.get('suggested_slots'):
            try:
                entry['suggested_slots'] = json.loads(entry['suggested_slots'])
            except Exception:
                pass
        return entry

    def add_vote(self, poll_id: int, vote: schemas.PollVoteCreate) -> models.PollVote:
        """
        Adiciona o voto de um estudante em uma enquete aberta se ele for elegível e ainda não tiver votado nela.

        Parâmetros de entrada:
            poll_id (int): O ID da enquete.
            vote (schemas.PollVoteCreate): Esquema contendo o ID do estudante que está votando.

        Parâmetros de saída:
            models.PollVote: O objeto de voto adicionado e persistido no banco de dados.
        """
        student = self._get_student_or_404(vote.student_id)
        poll = self._get_poll_or_404(poll_id)
        self._check_and_close_expired_poll(poll)

        if poll.status != "Open":
            raise HTTPException(status_code=400, detail="Enquete não está aberta para votação")

        course = self._get_course_or_404(poll.course_id)
        if not self._is_eligible(student, course):
            raise HTTPException(
                status_code=400,
                detail="Estudante não é elegível para votar nesta enquete"
            )

        existing = self.db.query(models.PollVote).filter(
            models.PollVote.poll_id == poll_id,
            models.PollVote.student_id == vote.student_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Estudante já votou nesta enquete")

        db_vote = models.PollVote(poll_id=poll_id, student_id=vote.student_id)
        self.db.add(db_vote)
        self.db.commit()
        self.db.refresh(db_vote)
        return db_vote

    def remove_vote(self, poll_id: int, student_id: int) -> bool:
        """
        Remove o voto de um estudante em uma enquete aberta.

        Parâmetros de entrada:
            poll_id (int): O ID da enquete.
            student_id (int): O ID do usuário estudante cujos votos serão removidos.

        Parâmetros de saída:
            bool: True se o voto foi removido com sucesso, False se o voto não foi encontrado.
        """
        self._get_student_or_404(student_id)
        poll = self._get_poll_or_404(poll_id)
        self._check_and_close_expired_poll(poll)

        if poll.status != "Open":
            raise HTTPException(status_code=400, detail="Enquete não está aberta para votação")

        db_vote = self.db.query(models.PollVote).filter(
            models.PollVote.poll_id == poll_id,
            models.PollVote.student_id == student_id
        ).first()
        if not db_vote:
            return False

        self.db.delete(db_vote)
        self.db.commit()
        return True

    def get_all_polls(self) -> List[dict]:
        """
        Retorna todas as enquetes cadastradas (sem filtrar por elegibilidade), útil para a visão de admin/comgrad.

        Parâmetros de entrada:
            Nenhum.

        Parâmetros de saída:
            List[dict]: Uma lista de dicionários contendo os dados de todas as enquetes.
        """
        all_polls = self.db.query(models.ClassRequestPoll).all()
        result = []
        import json
        for poll in all_polls:
            self._check_and_close_expired_poll(poll)
            entry = {
                **{c.name: getattr(poll, c.name) for c in poll.__table__.columns},
                "vote_count": len(poll.votes),
                "voted_student_ids": poll.voted_student_ids
            }
            if entry.get('suggested_slots'):
                try:
                    entry['suggested_slots'] = json.loads(entry['suggested_slots'])
                except Exception:
                    pass
            result.append(entry)
        return result

    def get_summary(self) -> dict:
        """
        Retorna um sumário com o número total de enquetes criadas, aprovadas e encerradas/negadas.

        Parâmetros de entrada:
            Nenhum.

        Parâmetros de saída:
            dict: Um dicionário com as contagens ("total_polls", "approved_polls", "denied_polls").
        """
        total_polls = self.db.query(models.ClassRequestPoll).count()
        approved_polls = self.db.query(models.ClassRequestPoll).filter(
            models.ClassRequestPoll.status == "Approved"
        ).count()
        denied_polls = self.db.query(models.ClassRequestPoll).filter(
            models.ClassRequestPoll.status == "Closed"
        ).count()
        return {
            "total_polls": total_polls,
            "approved_polls": approved_polls,
            "denied_polls": denied_polls,
        }

    def review_poll(self, poll_id: int, review: schemas.PollReview) -> models.ClassRequestPoll:
        """
        Registra a decisão/revisão da comissão (Comgrad/Admin) sobre uma determinada enquete,
        atualizando seu status, parecer e data de resposta.

        Parâmetros de entrada:
            poll_id (int): O ID da enquete a ser revisada.
            review (schemas.PollReview): Esquema contendo a resposta da comissão, status da revisão e ID do revisor.

        Parâmetros de saída:
            models.ClassRequestPoll: O objeto da enquete atualizado.
        """
        poll = self._get_poll_or_404(poll_id)
        poll.committee_response = review.committee_response
        poll.status = review.status
        poll.committee_member_id = review.committee_member_id
        from datetime import datetime
        poll.response_date = datetime.utcnow()
        self.db.commit()
        self.db.refresh(poll)

        import json
        if getattr(poll, 'suggested_slots', None):
            try:
                poll.suggested_slots = json.loads(poll.suggested_slots)
            except Exception:
                pass

        return poll
