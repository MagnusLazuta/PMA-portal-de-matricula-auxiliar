from typing import List, Optional
from .. import models, schemas
from .base import BaseService

class StudentService(BaseService):
    def create_student(self, student: schemas.StudentCreate) -> models.Student:
        """
        Cria um novo usuário (User) no banco de dados e cria o perfil de estudante (Student) associado a ele.

        Parâmetros de entrada:
            student (schemas.StudentCreate): Esquema contendo dados do usuário e do estudante.

        Parâmetros de saída:
            models.Student: O perfil de estudante criado.
        """
        # First create the user
        db_user = models.User(**student.user.model_dump())
        self.db.add(db_user)
        self.db.flush() # To get the user ID before the final commit

        # Then create the student
        student_data = student.model_dump(exclude={"user"})
        db_student = models.Student(**student_data, user_id=db_user.id)
        self.db.add(db_student)
        
        self.db.commit()
        self.db.refresh(db_student)
        return db_student

    def get_students(self, skip: int = 0, limit: int = 100) -> List[models.Student]:
        """
        Retorna uma lista paginada de todos os estudantes cadastrados.

        Parâmetros de entrada:
            skip (int): Quantidade de estudantes a pular.
            limit (int): Número máximo de estudantes a retornar.

        Parâmetros de saída:
            List[models.Student]: Lista de estudantes encontrados.
        """
        return self.db.query(models.Student).offset(skip).limit(limit).all()

    def get_student(self, student_id: int) -> Optional[models.Student]:
        """
        Recupera o perfil de estudante pelo ID do seu usuário.

        Parâmetros de entrada:
            student_id (int): O ID do usuário associado ao estudante.

        Parâmetros de saída:
            Optional[models.Student]: O objeto correspondente ao estudante ou None se não encontrado.
        """
        return self.db.query(models.Student).filter(models.Student.user_id == student_id).first()

    def update_wishlist(self, student_id: int, course_ids: List[int]) -> Optional[models.Student]:
        """
        Atualiza a lista de desejos (wishlist) de disciplinas do estudante,
        substituindo todas as seleções anteriores pelas novas informadas.

        Parâmetros de entrada:
            student_id (int): ID do estudante.
            course_ids (List[int]): Lista de IDs das disciplinas que serão salvas na lista de desejos.

        Parâmetros de saída:
            Optional[models.Student]: O perfil de estudante atualizado, ou None se o estudante não for encontrado.
        """
        student = self.get_student(student_id)
        if student is None:
            return None

        self.db.query(models.CourseWishlist).filter(models.CourseWishlist.student_id == student_id).delete()
        
        for c_id in course_ids:
            wish = models.CourseWishlist(student_id=student_id, course_id=c_id)
            self.db.add(wish)
        
        self.db.commit()
        self.db.refresh(student)
        return student

    def get_wishlist_courses(self, student_id: int) -> List[models.Course]:
        """
        Retorna a lista de disciplinas presentes na lista de desejos (wishlist) do estudante.

        Parâmetros de entrada:
            student_id (int): O ID do usuário estudante.

        Parâmetros de saída:
            List[models.Course]: Lista das disciplinas salvas na lista de desejos.
        """
        student = self.get_student(student_id)
        if student is None:
            return []

        return [
            wishlist_item.course
            for wishlist_item in student.wishlist
            if wishlist_item.course is not None
        ]

    def get_eligible_courses(self, student_id: int) -> Optional[List[models.Course]]:
        """
        Identifica todas as disciplinas que o estudante é elegível para cursar, com base
        no seu currículo, pré-requisitos cumpridos e créditos mínimos requeridos.

        Parâmetros de entrada:
            student_id (int): O ID do estudante.

        Parâmetros de saída:
            Optional[List[models.Course]]: Lista das disciplinas para as quais o aluno é elegível, ou None se o estudante não for encontrado.
        """
        student = self.get_student(student_id)
        if student is None:
            return None

        completed_course_ids = {cc.course_id for cc in student.completed_courses if cc.course_id is not None}
        completed_credits = sum(cc.course.credits for cc in student.completed_courses if cc.course is not None)

        # Filter courses by the student's curriculum
        curriculum = student.curriculum_obj
        if not curriculum:
            curriculum = self.db.query(models.Curriculum).filter(models.Curriculum.name == student.course).first()

        if curriculum:
            all_courses = [cc.course for cc in curriculum.curriculum_courses if cc.course is not None]
        else:
            all_courses = self.db.query(models.Course).all()

        eligible_courses = []
        for course in all_courses:
            if course.id in completed_course_ids:
                continue

            if course.min_credits_required and completed_credits < course.min_credits_required:
                continue

            prereqs_met = True
            curriculum_course_ids = {c.id for c in all_courses}
            for prereq in course.prerequisites:
                if prereq.id in curriculum_course_ids and prereq.id not in completed_course_ids:
                    prereqs_met = False
                    break

            if prereqs_met:
                eligible_courses.append(course)

        return eligible_courses

    def get_student_curriculum(self, student_id: int) -> Optional[List[models.Course]]:
        """
        Retorna a grade curricular do curso do estudante, incluindo metadados como
        semestre recomendado e obrigatoriedade de cada disciplina.

        Parâmetros de entrada:
            student_id (int): O ID do estudante.

        Parâmetros de saída:
            Optional[List[models.Course]]: Lista das disciplinas do currículo, ou None se o estudante não for encontrado.
        """
        student = self.get_student(student_id)
        if student is None:
            return None

        curriculum = student.curriculum_obj
        if not curriculum:
            curriculum = self.db.query(models.Curriculum).filter(models.Curriculum.name == student.course).first()

        if not curriculum:
            return []

        results = []
        for cc in curriculum.curriculum_courses:
            course = cc.course
            if course:
                course.semester = cc.semester
                course.mandatory = cc.mandatory
                results.append(course)
        return results

    def update_completed_courses(self, student_id: int, course_ids: List[int]) -> Optional[models.Student]:
        """
        Atualiza a lista de disciplinas já concluídas (aprovadas/dispensadas) do estudante
        usando diretamente uma lista de IDs de disciplinas.

        Parâmetros de entrada:
            student_id (int): O ID do estudante.
            course_ids (List[int]): Lista com os novos IDs das disciplinas concluídas.

        Parâmetros de saída:
            Optional[models.Student]: O perfil de estudante atualizado, ou None se o estudante não for encontrado.
        """
        student = self.get_student(student_id)
        if student is None:
            return None

        # Remove all existing completed courses for this student
        self.db.query(models.CompletedCourse).filter(models.CompletedCourse.student_id == student_id).delete()

        # Add the new completed courses
        for c_id in course_ids:
            comp = models.CompletedCourse(student_id=student_id, course_id=c_id)
            self.db.add(comp)

        self.db.commit()
        self.db.refresh(student)
        return student

    def update_completed_courses_from_codes(self, student_id: int, codes: List[str]) -> Optional[List[models.Course]]:
        """
        Atualiza a lista de disciplinas já concluídas do estudante a partir de uma lista de códigos de disciplinas.
        Mapeia códigos genéricos (como "TCC" ou vazio) para correspondentes reais no banco de dados.

        Parâmetros de entrada:
            student_id (int): O ID do estudante.
            codes (List[str]): Lista com códigos textuais das disciplinas concluídas.

        Parâmetros de saída:
            Optional[List[models.Course]]: Lista das disciplinas associadas como concluídas ao perfil, ou None se o estudante não for encontrado.
        """
        student = self.get_student(student_id)
        if student is None:
            return None

        # Fetch all courses matching these codes
        # Map "TCC" or empty strings back to the actual database TCC/TG codes
        db_codes = []
        for code in codes:
            if code in ("TCC", ""):
                db_codes.extend(["TCC-CIC", "TG-I-ECP", "TG-II-ECP"])
            else:
                db_codes.append(code)
        courses = self.db.query(models.Course).filter(models.Course.code.in_(db_codes)).all()

        # Remove all existing completed courses for this student
        self.db.query(models.CompletedCourse).filter(models.CompletedCourse.student_id == student_id).delete()

        # Add the new completed courses
        for course in courses:
            comp = models.CompletedCourse(student_id=student_id, course_id=course.id)
            self.db.add(comp)

        self.db.commit()
        self.db.refresh(student)
        return [cc.course for cc in student.completed_courses if cc.course is not None]
