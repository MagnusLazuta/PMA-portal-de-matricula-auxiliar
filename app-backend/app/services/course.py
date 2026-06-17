from typing import List
from .. import models, schemas
from .base import BaseService

class CourseService(BaseService):
    def create_course(self, course: schemas.CourseCreate) -> models.Course:
        """
        Cria uma nova disciplina (Course) e associa seus pré-requisitos cadastrados no banco de dados.

        Parâmetros de entrada:
            course (schemas.CourseCreate): Esquema contendo os dados da disciplina e os IDs dos pré-requisitos.

        Parâmetros de saída:
            models.Course: O objeto da disciplina criada e registrada no banco de dados.
        """
        course_data = course.model_dump(exclude={"prerequisite_ids"})
        db_course = models.Course(**course_data)
        
        if course.prerequisite_ids:
            prereqs = self.db.query(models.Course).filter(models.Course.id.in_(course.prerequisite_ids)).all()
            db_course.prerequisites = prereqs
            
        self.db.add(db_course)
        self.db.commit()
        self.db.refresh(db_course)
        return db_course

    def create_courses_bulk(self, courses: List[schemas.CourseCreate]) -> List[models.Course]:
        """
        Cria múltiplas disciplinas em lote (bulk) chamando consecutivamente o método 'create_course'.

        Parâmetros de entrada:
            courses (List[schemas.CourseCreate]): Lista de esquemas de criação de disciplinas.

        Parâmetros de saída:
            List[models.Course]: Lista de objetos das disciplinas criadas.
        """
        created_courses = []
        for course_schema in courses:
            created_courses.append(self.create_course(course_schema))
        return created_courses

    def get_curricula(self) -> List[models.Curriculum]:
        """
        Retorna a lista de todos os currículos (cursos/grades curriculares) cadastrados no banco de dados.

        Parâmetros de entrada:
            Nenhum.

        Parâmetros de saída:
            List[models.Curriculum]: Lista de currículos encontrados.
        """
        return self.db.query(models.Curriculum).all()

    def get_courses(self, curriculum_id: int | None = None, skip: int = 0, limit: int = 100) -> List[models.Course]:
        """
        Retorna a lista de disciplinas cadastradas, podendo ser filtrada por um currículo específico.
        Se filtrada por currículo, anexa metadados sobre obrigatoriedade (mandatory) e semestre de cada disciplina.

        Parâmetros de entrada:
            curriculum_id (int | None): O ID do currículo para filtrar as disciplinas (opcional).
            skip (int): Quantidade de disciplinas a pular para paginação.
            limit (int): Limite máximo de disciplinas a retornar.

        Parâmetros de saída:
            List[models.Course]: Lista das disciplinas encontradas com seus metadados de semestre e obrigatoriedade.
        """
        if curriculum_id is not None:
            curriculum_courses = (
                self.db.query(models.CurriculumCourse)
                .filter(models.CurriculumCourse.curriculum_id == curriculum_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
            courses = []
            for cc in curriculum_courses:
                course = cc.course
                if course:
                    course.semester = cc.semester
                    course.mandatory = cc.mandatory
                    courses.append(course)
            return courses

        db_courses = self.db.query(models.Course).offset(skip).limit(limit).all()
        for course in db_courses:
            first_assoc = self.db.query(models.CurriculumCourse).filter(models.CurriculumCourse.course_id == course.id).first()
            if first_assoc:
                course.semester = first_assoc.semester
                course.mandatory = first_assoc.mandatory
            else:
                course.semester = None
                course.mandatory = False
        return db_courses
