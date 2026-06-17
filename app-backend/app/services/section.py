from typing import List
from .. import models, schemas
from .base import BaseService

class ClassSectionService(BaseService):
    def create_section(self, section: schemas.ClassSectionCreate) -> models.ClassSection:
        """
        Cria uma nova turma (ClassSection) com seus respectivos horários (ClassSchedule) no banco de dados.

        Parâmetros de entrada:
            section (schemas.ClassSectionCreate): Esquema contendo dados da turma e a lista de horários.

        Parâmetros de saída:
            models.ClassSection: O objeto da turma criada e salva no banco de dados.
        """
        db_section = models.ClassSection(
            course_id=section.course_id,
            section_code=section.section_code,
            semester=section.semester,
            capacity=section.capacity,
            professor_name=section.professor_name,
        )
        self.db.add(db_section)
        self.db.flush()

        for sched in section.schedules:
            db_sched = models.ClassSchedule(**sched.model_dump(), class_section_id=db_section.id)
            self.db.add(db_sched)
        
        self.db.commit()
        self.db.refresh(db_section)
        return db_section

    def get_sections(self, skip: int = 0, limit: int = 100) -> List[models.ClassSection]:
        """
        Consulta uma lista paginada de turmas cadastradas no banco de dados.

        Parâmetros de entrada:
            skip (int): Quantidade de turmas a pular para paginação.
            limit (int): Limite máximo de turmas a retornar.

        Parâmetros de saída:
            List[models.ClassSection]: Lista de objetos das turmas encontradas.
        """
        return self.db.query(models.ClassSection).offset(skip).limit(limit).all()

    def get_all_sections(self, semester: str | None = None) -> List[models.ClassSection]:
        """
        Consulta todas as turmas cadastradas, opcionalmente filtrando por um semestre acadêmico específico.

        Parâmetros de entrada:
            semester (str | None): O semestre acadêmico a ser filtrado (opcional).

        Parâmetros de saída:
            List[models.ClassSection]: Lista de objetos das turmas correspondentes.
        """
        query = self.db.query(models.ClassSection)
        if semester is not None:
            query = query.filter(models.ClassSection.semester == semester)
        return query.all()
