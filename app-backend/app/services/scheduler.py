import heapq
from dataclasses import dataclass
from datetime import time
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from .restriction import TimeRestrictionService
from .section import ClassSectionService
from .student import StudentService


@dataclass
class RankedScheduleResult:
    score: float
    selected_course_count: int
    total_course_priority: int
    matched_preference_count: int
    active_days: int
    total_gap_minutes: int
    schedule: List[dict]


class ScheduleGenerator:
    """
    Classe responsável por gerar e ranquear grades de horários (schedules) para os estudantes,
    considerando restrições rígidas (hard restrictions) e preferências (soft restrictions)
    como janelas de horários preferidas, prioridade de disciplinas e professores preferidos.
    """
    def __init__(self, db: Session):
        """
        Inicializa o gerador de cronogramas.

        Parâmetros de entrada:
            db (Session): Sessão ativa do banco de dados do SQLAlchemy.

        Parâmetros de saída:
            Nenhum.
        """
        self.db = db
        self.section_service = ClassSectionService(db)
        self.restriction_service = TimeRestrictionService(db)
        self.student_service = StudentService(db)

    def _to_minutes(self, t: time) -> int:
        """
        Converte um objeto datetime.time em minutos passados desde a meia-noite.

        Parâmetros de entrada:
            t (time): O objeto de hora a ser convertido.

        Parâmetros de saída:
            int: Representação da hora em minutos.
        """
        return t.hour * 60 + t.minute

    def _time_conflict(self, start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
        """
        Verifica se dois intervalos de tempo possuem sobreposição.

        Parâmetros de entrada:
            start_a (time): Início do intervalo A.
            end_a (time): Fim do intervalo A.
            start_b (time): Início do intervalo B.
            end_b (time): Fim do intervalo B.

        Parâmetros de saída:
            bool: True se houver sobreposição de horários, False caso contrário.
        """
        return self._to_minutes(start_a) < self._to_minutes(end_b) and self._to_minutes(start_b) < self._to_minutes(end_a)

    def _schedules_conflict(self, sched_a, sched_b) -> bool:
        """
        Verifica se dois registros de horário de aula conflitam no mesmo dia da semana e horário.

        Parâmetros de entrada:
            sched_a: Objeto de horário da primeira aula.
            sched_b: Objeto de horário da segunda aula.

        Parâmetros de saída:
            bool: True se houver conflito de horário no mesmo dia, False caso contrário.
        """
        if sched_a.day_of_week != sched_b.day_of_week:
            return False
        return self._time_conflict(sched_a.start_time, sched_a.end_time, sched_b.start_time, sched_b.end_time)

    def _section_conflicts_restrictions(self, section, restrictions) -> bool:
        """
        Verifica se uma determinada turma conflita com alguma restrição rígida (hard restriction).

        Parâmetros de entrada:
            section: Objeto da turma (class section).
            restrictions: Lista de restrições rígidas a serem validadas.

        Parâmetros de saída:
            bool: True se a turma violar alguma restrição de horário do aluno, False caso contrário.
        """
        for sched in section.schedules:
            for restriction in restrictions:
                if restriction.day_of_week is None or restriction.start_time is None or restriction.end_time is None:
                    continue
                if sched.day_of_week == restriction.day_of_week and self._time_conflict(
                    sched.start_time,
                    sched.end_time,
                    restriction.start_time,
                    restriction.end_time,
                ):
                    return True
        return False

    def _section_conflicts_section(self, section_a, section_b) -> bool:
        """
        Verifica se há conflito de horários entre duas turmas diferentes.

        Parâmetros de entrada:
            section_a: Objeto da primeira turma.
            section_b: Objeto da segunda turma.

        Parâmetros de saída:
            bool: True se houver conflito de horários entre as turmas, False caso contrário.
        """
        for sched_a in section_a.schedules:
            for sched_b in section_b.schedules:
                if self._schedules_conflict(sched_a, sched_b):
                    return True
        return False

    def _normalize_name(self, value: Optional[str]) -> str:
        """
        Normaliza uma string de texto removendo espaços em branco extras nas extremidades
        e convertendo para minúsculas (casefold).

        Parâmetros de entrada:
            value (Optional[str]): String a ser normalizada.

        Parâmetros de saída:
            str: String normalizada.
        """
        return (value or "").strip().casefold()

    def _importance_weight(self, importance_level: Optional[str]) -> int:
        """
        Mapeia o nível de importância de uma disciplina para uma pontuação numérica.

        Parâmetros de entrada:
            importance_level (Optional[str]): Nível de importância ("LOW", "MEDIUM", "HIGH").

        Parâmetros de saída:
            int: Peso numérico correspondente (LOW=1, MEDIUM=3, HIGH=6).
        """
        mapping = {
            schemas.CourseImportanceLevel.LOW.value: 1,
            schemas.CourseImportanceLevel.MEDIUM.value: 3,
            schemas.CourseImportanceLevel.HIGH.value: 6,
        }
        return mapping.get((importance_level or schemas.CourseImportanceLevel.MEDIUM.value), 3)

    def _section_to_dict(self, section) -> dict:
        """
        Converte um objeto de turma (ClassSection) em um dicionário para resposta serializada.

        Parâmetros de entrada:
            section: Objeto da turma.

        Parâmetros de saída:
            dict: Dicionário contendo os dados essenciais da turma e seus horários estruturados.
        """
        return {
            "section_id": section.id,
            "section_code": section.section_code or "",
            "course_name": section.course.name if section.course else "",
            "course_code": section.course.code if section.course else "",
            "professor_name": section.professor_name,
            "schedules": [
                {
                    "id": schedule.id,
                    "class_section_id": schedule.class_section_id,
                    "day_of_week": schedule.day_of_week,
                    "start_time": schedule.start_time,
                    "end_time": schedule.end_time,
                    "room": schedule.room,
                }
                for schedule in section.schedules
            ],
        }

    def _load_student_context(self, student_id: int, semester: Optional[str] = None) -> Optional[dict]:
        """
        Carrega as informações contextuais do estudante necessárias para geração de grade de horários,
        filtrando disciplinas da lista de desejos (wishlist) que já foram cursadas, que violam
        requisitos de créditos ou pré-requisitos, e lê suas restrições e preferências.

        Parâmetros de entrada:
            student_id (int): O ID do usuário estudante.
            semester (Optional[str]): O semestre acadêmico a ser consultado para as turmas.

        Parâmetros de saída:
            Optional[dict]: Um dicionário contendo o contexto mapeado ou None se nenhuma disciplina válida for encontrada.
        """
        student = self.student_service.get_student(student_id)
        if student is None:
            return None

        # Get passed courses IDs
        completed_courses = self.db.query(models.CompletedCourse).filter(
            models.CompletedCourse.student_id == student_id
        ).all()
        passed_course_ids = {c.course_id for c in completed_courses}
        
        # Calculate total credits using a join query for robustness
        total_credits = self.db.query(func.sum(models.Course.credits)).join(
            models.CompletedCourse, models.Course.id == models.CompletedCourse.course_id
        ).filter(
            models.CompletedCourse.student_id == student_id
        ).scalar() or 0

        wishlist_course_ids = [
            wishlist_item.course_id
            for wishlist_item in self.db.query(models.CourseWishlist).filter(
                models.CourseWishlist.student_id == student_id
            ).all()
        ]
        if not wishlist_course_ids:
            return None

        valid_course_ids = []
        for course_id in wishlist_course_ids:
            course = self.db.query(models.Course).filter(models.Course.id == course_id).first()
            if course is None or course_id in passed_course_ids:
                continue

            if total_credits < (course.min_credits_required or 0):
                continue

            prereq_ids = [prereq.id for prereq in course.prerequisites]
            if not all(prereq_id in passed_course_ids for prereq_id in prereq_ids):
                continue

            valid_course_ids.append(course_id)

        if not valid_course_ids:
            return None

        restrictions = self.restriction_service.get_student_restrictions(student_id)
        hard_restrictions = []
        preferred_windows = []
        course_priority_map = {course_id: self._importance_weight(None) for course_id in valid_course_ids}
        professor_preferences: Dict[int, Dict[str, int]] = {}

        for restriction in restrictions:
            restriction_type = restriction.restriction_type or schemas.RestrictionType.HARD_BLOCK.value

            if restriction_type == schemas.RestrictionType.HARD_BLOCK.value:
                hard_restrictions.append(restriction)
                continue

            if restriction_type == schemas.RestrictionType.PREFERRED_WINDOW.value:
                preferred_windows.append(restriction)
                continue

            if restriction_type == schemas.RestrictionType.COURSE_IMPORTANCE.value and restriction.course_id in course_priority_map:
                course_priority_map[restriction.course_id] = max(
                    course_priority_map[restriction.course_id],
                    restriction.score_weight or self._importance_weight(restriction.importance_level),
                )
                continue

            if restriction_type == schemas.RestrictionType.PROFESSOR_PREFERENCE.value and restriction.course_id in valid_course_ids:
                professor_preferences.setdefault(restriction.course_id, {})
                professor_preferences[restriction.course_id][self._normalize_name(restriction.preferred_professor)] = (
                    restriction.preference_order or 1
                )

        sections = self.section_service.get_all_sections(semester=semester)
        filtered_sections = [
            section for section in sections
            if section.course_id in valid_course_ids and not self._section_conflicts_restrictions(section, hard_restrictions)
        ]

        sections_by_course = {
            course_id: [section for section in filtered_sections if section.course_id == course_id]
            for course_id in valid_course_ids
        }

        final_course_ids = [course_id for course_id in valid_course_ids if sections_by_course[course_id]]
        if not final_course_ids:
            return None

        return {
            "course_ids": final_course_ids,
            "sections_by_course": sections_by_course,
            "course_priority_map": course_priority_map,
            "preferred_windows": preferred_windows,
            "professor_preferences": professor_preferences,
        }

    def _professor_bonus(self, section, professor_preferences: Dict[int, Dict[str, int]]) -> tuple[float, int]:
        """
        Calcula o bônus de pontuação para uma turma com base na preferência de professor cadastrada pelo aluno.

        Parâmetros de entrada:
            section: Objeto da turma.
            professor_preferences (Dict[int, Dict[str, int]]): Mapeamento de preferências de professores do aluno.

        Parâmetros de saída:
            tuple[float, int]: Uma tupla (valor_do_bonus, quantidade_de_matches).
        """
        section_preferences = professor_preferences.get(section.course_id)
        normalized_professor = self._normalize_name(section.professor_name)
        if not section_preferences or not normalized_professor:
            return 0.0, 0

        rank = section_preferences.get(normalized_professor)
        if rank is None:
            return 0.0, 0

        return float(max(1, 4 - rank)), 1

    def _preferred_window_bonus(self, section, preferred_windows) -> tuple[float, int]:
        """
        Calcula o bônus de pontuação para uma turma com base nas janelas de horário preferidas do aluno.

        Parâmetros de entrada:
            section: Objeto da turma.
            preferred_windows: Lista de janelas de horários preferidas do estudante.

        Parâmetros de saída:
            tuple[float, int]: Uma tupla (valor_do_bonus, quantidade_de_matches).
        """
        total_bonus = 0.0
        match_count = 0

        for schedule in section.schedules:
            for preferred_window in preferred_windows:
                if (
                    preferred_window.day_of_week is None
                    or preferred_window.start_time is None
                    or preferred_window.end_time is None
                    or schedule.day_of_week != preferred_window.day_of_week
                ):
                    continue

                if (
                    self._to_minutes(schedule.start_time) >= self._to_minutes(preferred_window.start_time)
                    and self._to_minutes(schedule.end_time) <= self._to_minutes(preferred_window.end_time)
                ):
                    total_bonus += float(preferred_window.score_weight or 2)
                    match_count += 1
                elif self._time_conflict(
                    schedule.start_time,
                    schedule.end_time,
                    preferred_window.start_time,
                    preferred_window.end_time,
                ):
                    total_bonus += float((preferred_window.score_weight or 2) * 0.5)

        return total_bonus, match_count

    def _section_positive_score(
        self,
        section,
        course_priority_map: Dict[int, int],
        professor_preferences: Dict[int, Dict[str, int]],
        preferred_windows,
    ) -> tuple[float, int, int]:
        """
        Calcula a pontuação positiva bruta obtida ao incluir uma turma na grade de horários,
        somando a prioridade da disciplina aos bônus de professor e janela preferida.

        Parâmetros de entrada:
            section: Objeto da turma.
            course_priority_map (Dict[int, int]): Mapeamento de prioridades por disciplina.
            professor_preferences (Dict[int, Dict[str, int]]): Mapeamento de preferências de professores.
            preferred_windows: Lista de janelas de horários preferidas.

        Parâmetros de saída:
            tuple[float, int, int]: Uma tupla contendo (pontuacao_positiva, prioridade_da_disciplina, matches_preferencia_totais).
        """
        course_priority = course_priority_map.get(section.course_id, self._importance_weight(None))
        professor_bonus, professor_matches = self._professor_bonus(section, professor_preferences)
        preferred_window_bonus, preferred_window_matches = self._preferred_window_bonus(section, preferred_windows)

        return (
            float(course_priority) + professor_bonus + preferred_window_bonus,
            course_priority,
            professor_matches + preferred_window_matches,
        )

    def _schedule_penalties(self, sections) -> tuple[float, int, int]:
        """
        Calcula as penalidades da grade de horários com base no número de dias ativos de aula
        e quantidade de minutos de janela livre ("gaps" ou horários vagos) entre aulas no mesmo dia.

        Parâmetros de entrada:
            sections: Lista de turmas que compõem a grade candidata.

        Parâmetros de saída:
            tuple[float, int, int]: Uma tupla contendo (penalidade_calculada, dias_ativos, total_minutos_janela_livre).
        """
        grouped_by_day = {}
        for section in sections:
            for schedule in section.schedules:
                grouped_by_day.setdefault(schedule.day_of_week, []).append(
                    (self._to_minutes(schedule.start_time), self._to_minutes(schedule.end_time))
                )

        active_days = len(grouped_by_day)
        total_gap_minutes = 0
        for intervals in grouped_by_day.values():
            intervals.sort()
            for index in range(1, len(intervals)):
                gap = max(0, intervals[index][0] - intervals[index - 1][1])
                total_gap_minutes += gap

        day_penalty = max(0, active_days - 1) * 0.35
        gap_penalty = (total_gap_minutes / 60.0) * 0.08
        return day_penalty + gap_penalty, active_days, total_gap_minutes

    def _result_sort_key(self, result: RankedScheduleResult) -> tuple:
        """
        Gera a chave de ordenação utilizada para ranquear os resultados de grades geradas.
        Prioriza grades com maior pontuação final, maior prioridade de disciplinas, maior correspondência
        de preferências, menor quantidade de dias ativos de aula e menor tempo de janelas livres.

        Parâmetros de entrada:
            result (RankedScheduleResult): O objeto do resultado da grade avaliada.

        Parâmetros de saída:
            tuple: Uma tupla de ordenação multidimensional.
        """
        return (
            round(result.score, 5),
            result.total_course_priority,
            result.selected_course_count,
            result.matched_preference_count,
            -result.active_days,
            -result.total_gap_minutes,
        )

    def generate_ranked_schedules(self, student_id: int, limit: int = 5, semester: Optional[str] = None) -> List[dict]:
        """
        Gera até 'limit' opções de grades de horários otimizadas e ordenadas por relevância para o estudante,
        usando um algoritmo de busca com retrocesso (backtracking) e poda por limite superior de pontuação.

        Parâmetros de entrada:
            student_id (int): O ID do usuário estudante.
            limit (int): Número máximo de opções de grades a retornar.
            semester (Optional[str]): O semestre acadêmico das turmas.

        Parâmetros de saída:
            List[dict]: Uma lista de dicionários contendo os dados das melhores opções de grades de horários encontradas.
        """
        context = self._load_student_context(student_id, semester)
        if context is None:
            return []

        course_priority_map = context["course_priority_map"]
        preferred_windows = context["preferred_windows"]
        professor_preferences = context["professor_preferences"]
        sections_by_course = context["sections_by_course"]

        ordered_course_ids = sorted(
            context["course_ids"],
            key=lambda course_id: (-course_priority_map.get(course_id, 0), len(sections_by_course[course_id])),
        )

        max_positive_per_course = {
            course_id: max(
                self._section_positive_score(
                    section,
                    course_priority_map,
                    professor_preferences,
                    preferred_windows,
                )[0]
                for section in sections_by_course[course_id]
            )
            for course_id in ordered_course_ids
        }

        suffix_upper_bounds = [0.0] * (len(ordered_course_ids) + 1)
        for index in range(len(ordered_course_ids) - 1, -1, -1):
            suffix_upper_bounds[index] = (
                suffix_upper_bounds[index + 1] + max_positive_per_course[ordered_course_ids[index]]
            )

        top_results = []
        sequence = 0
        current_schedule = []

        def push_result(result: RankedScheduleResult):
            nonlocal sequence
            key = self._result_sort_key(result)
            item = (key, sequence, result)
            sequence += 1

            if len(top_results) < limit:
                heapq.heappush(top_results, item)
                return

            if key > top_results[0][0]:
                heapq.heapreplace(top_results, item)

        def backtrack(index: int, positive_score: float, selected_priority: int, matched_preferences: int):
            if index == len(ordered_course_ids):
                if not current_schedule:
                    return

                penalties, active_days, total_gap_minutes = self._schedule_penalties(current_schedule)
                result = RankedScheduleResult(
                    score=positive_score - penalties,
                    selected_course_count=len(current_schedule),
                    total_course_priority=selected_priority,
                    matched_preference_count=matched_preferences,
                    active_days=active_days,
                    total_gap_minutes=total_gap_minutes,
                    schedule=[self._section_to_dict(section) for section in current_schedule],
                )
                push_result(result)
                return

            optimistic_score = positive_score + suffix_upper_bounds[index]
            if len(top_results) >= limit and optimistic_score < top_results[0][2].score:
                return

            course_id = ordered_course_ids[index]

            for section in sections_by_course[course_id]:
                if any(self._section_conflicts_section(section, existing) for existing in current_schedule):
                    continue

                section_positive_score, section_priority, section_matches = self._section_positive_score(
                    section,
                    course_priority_map,
                    professor_preferences,
                    preferred_windows,
                )
                current_schedule.append(section)
                backtrack(
                    index + 1,
                    positive_score + section_positive_score,
                    selected_priority + section_priority,
                    matched_preferences + section_matches,
                )
                current_schedule.pop()

            backtrack(index + 1, positive_score, selected_priority, matched_preferences)

        backtrack(0, 0.0, 0, 0)

        ranked_results = [
            result
            for _, _, result in sorted(top_results, key=lambda item: item[0], reverse=True)
        ]

        return [
            {
                "score": round(result.score, 3),
                "selected_course_count": result.selected_course_count,
                "total_course_priority": result.total_course_priority,
                "matched_preference_count": result.matched_preference_count,
                "schedule": result.schedule,
            }
            for result in ranked_results
        ]

    def generate_possible_schedules(self, student_id: int, limit: int = 5, semester: Optional[str] = None) -> list[list[dict]]:
        """
        Retorna apenas as grades geradas (sem metadados de score), no formato de uma lista de opções de grades.

        Parâmetros de entrada:
            student_id (int): O ID do usuário estudante.
            limit (int): Número máximo de opções de grades a retornar.
            semester (Optional[str]): O semestre acadêmico.

        Parâmetros de saída:
            list[list[dict]]: Uma lista de opções de grades candidatas, em que cada opção é uma lista de turmas no formato dict.
        """
        ranked = self.generate_ranked_schedules(student_id=student_id, limit=limit, semester=semester)
        return [option["schedule"] for option in ranked]
