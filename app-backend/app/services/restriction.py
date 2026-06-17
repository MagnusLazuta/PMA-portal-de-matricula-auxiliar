from typing import List
from .. import models, schemas
from .base import BaseService

class TimeRestrictionService(BaseService):
    def create_restriction(self, restriction: schemas.TimeRestrictionCreate) -> models.TimeRestriction:
        """
        Cria uma nova restrição de horário ou preferência para o estudante no banco de dados,
        definindo valores padrão para 'is_mandatory' e 'score_weight' caso não informados.

        Parâmetros de entrada:
            restriction (schemas.TimeRestrictionCreate): Esquema contendo os dados da restrição/preferência.

        Parâmetros de saída:
            models.TimeRestriction: O objeto de restrição criado e salvo no banco de dados.
        """
        payload = restriction.model_dump()

        if payload["is_mandatory"] is None:
            payload["is_mandatory"] = (
                payload["restriction_type"] == schemas.RestrictionType.HARD_BLOCK
            )

        if payload["score_weight"] is None:
            payload["score_weight"] = self._default_score_weight(
                payload["restriction_type"],
                payload.get("importance_level"),
                payload.get("preference_order"),
            )

        db_restriction = models.TimeRestriction(**payload)
        self.db.add(db_restriction)
        self.db.commit()
        self.db.refresh(db_restriction)
        return db_restriction

    def get_all_restrictions(self, student_id: int | None = None) -> List[models.TimeRestriction]:
        """
        Consulta todas as restrições cadastradas, opcionalmente filtrando por um estudante específico.

        Parâmetros de entrada:
            student_id (int | None): ID do usuário do estudante para filtrar (opcional).

        Parâmetros de saída:
            List[models.TimeRestriction]: Lista de objetos de restrições de horários encontrados.
        """
        query = self.db.query(models.TimeRestriction)
        if student_id is not None:
            query = query.filter(models.TimeRestriction.student_id == student_id)
        return query.all()

    def get_student_restrictions(self, student_id: int) -> List[models.TimeRestriction]:
        """
        Consulta todas as restrições de horário e preferências associadas a um estudante específico.

        Parâmetros de entrada:
            student_id (int): O ID do usuário estudante.

        Parâmetros de saída:
            List[models.TimeRestriction]: Lista de objetos das restrições do estudante.
        """
        return self.db.query(models.TimeRestriction).filter(models.TimeRestriction.student_id == student_id).all()

    def delete_restriction(self, restriction_id: int) -> bool:
        """
        Remove uma restrição de horário específica do banco de dados pelo seu ID.

        Parâmetros de entrada:
            restriction_id (int): O ID da restrição a ser excluída.

        Parâmetros de saída:
            bool: True se a exclusão foi bem-sucedida, False se a restrição não foi encontrada.
        """
        restriction = self.db.query(models.TimeRestriction).filter(
            models.TimeRestriction.id == restriction_id
        ).first()
        if restriction is None:
            return False

        self.db.delete(restriction)
        self.db.commit()
        return True

    def _default_score_weight(
        self,
        restriction_type: schemas.RestrictionType,
        importance_level: schemas.CourseImportanceLevel | None,
        preference_order: int | None,
    ) -> int:
        """
        Calcula o peso de pontuação padrão (score_weight) para uma restrição ou preferência
        com base no seu tipo, nível de importância e ordem de preferência.

        Parâmetros de entrada:
            restriction_type (schemas.RestrictionType): Tipo de restrição (ex: HARD_BLOCK, PREFERRED_WINDOW).
            importance_level (schemas.CourseImportanceLevel | None): Nível de importância para a disciplina.
            preference_order (int | None): Ordem de preferência de professor informada pelo aluno.

        Parâmetros de saída:
            int: O valor inteiro correspondente ao peso da pontuação.
        """
        if restriction_type == schemas.RestrictionType.PREFERRED_WINDOW:
            return 2
        if restriction_type == schemas.RestrictionType.PROFESSOR_PREFERENCE:
            if preference_order is None:
                return 3
            return max(1, 4 - preference_order)
        if restriction_type == schemas.RestrictionType.COURSE_IMPORTANCE:
            mapping = {
                schemas.CourseImportanceLevel.LOW: 1,
                schemas.CourseImportanceLevel.MEDIUM: 3,
                schemas.CourseImportanceLevel.HIGH: 6,
            }
            return mapping.get(importance_level, 3)
        return 0
