from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import csv
import io
from ..utils.security import hash_password

DAY_MAPPING = {
    "Segunda": "Monday",
    "Terça": "Tuesday",
    "Quarta": "Wednesday",
    "Quinta": "Thursday",
    "Sexta": "Friday",
    "Sábado": "Saturday",
    "Domingo": "Sunday"
}


from ..database import get_db
from .. import models

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

class StudentDetails(BaseModel):
    current_semester: int
    course: str
    curriculum_id: int

class UserRegisterRequest(BaseModel):
    role: str  # "student", "comgrad", "admin"
    name: str
    email: str
    card_number: int
    password: str
    student_details: Optional[StudentDetails] = None
    comgrad_role: Optional[str] = None

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    """
    Retorna uma lista contendo todos os usuários cadastrados e seus respectivos papéis e status de atividade.

    Parâmetros de entrada:
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        list: Lista de dicionários contendo os dados básicos de cada usuário (id, name, email, card_number, role, is_active).
    """
    users = db.query(models.User).all()
    res = []
    for user in users:
        role = "student"
        if user.admin is not None and user.comgrad is not None:
            role = "comgrad_admin"
        elif user.admin is not None:
            role = "admin"
        elif user.comgrad is not None:
            role = "comgrad"
        
        res.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "card_number": user.card_number,
            "role": role,
            "is_active": getattr(user, 'is_active', True)
        })
    return res

@router.post("/users")
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Cadastra um novo usuário no sistema com o papel especificado (student, comgrad, ou admin).

    Parâmetros de entrada:
        req (UserRegisterRequest): Dados do usuário a ser cadastrado e detalhes do papel se for estudante/comgrad.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem informativa ("status": "success", "message": "Usuário criado com sucesso!").
    """
    # Check duplicate
    existing = db.query(models.User).filter(
        (models.User.card_number == req.card_number) | (models.User.email == req.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail ou matrícula já cadastrados.")

    # Create User
    must_change = False
    if req.role == "student":
        must_change = True

    new_user = models.User(
        name=req.name,
        email=req.email,
        card_number=req.card_number,
        password=hash_password(req.password),
        must_change_password=must_change
    )
    db.add(new_user)
    db.flush()

    if req.role == "student":
        if not req.student_details:
            raise HTTPException(status_code=400, detail="Detalhes do estudante são obrigatórios.")
        
        student = models.Student(
            user_id=new_user.id,
            current_semester=req.student_details.current_semester,
            course=req.student_details.course,
            curriculum_id=req.student_details.curriculum_id
        )
        db.add(student)
    elif req.role == "comgrad":
        comgrad = models.COMGRAD(
            user_id=new_user.id,
            role=req.comgrad_role or "Membro"
        )
        db.add(comgrad)
    elif req.role == "admin":
        admin = models.Admin(
            user_id=new_user.id
        )
        db.add(admin)
    else:
        raise HTTPException(status_code=400, detail="Papel inválido.")

    db.commit()
    return {"status": "success", "message": "Usuário criado com sucesso!"}

@router.post("/users/{user_id}/upgrade-to-admin")
def upgrade_to_admin(user_id: int, db: Session = Depends(get_db)):
    """
    Promove um membro existente da COMGRAD para o papel de administrador.

    Parâmetros de entrada:
        user_id (int): O ID do usuário a ser promovido.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem informativa.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    if user.student is not None:
        raise HTTPException(status_code=400, detail="Alunos não podem receber acesso de administrador.")
    
    if user.comgrad is None:
        raise HTTPException(status_code=400, detail="Apenas membros da COMGRAD podem ser promovidos a administradores.")

    # Check if already admin
    if user.admin is not None:
        return {"status": "success", "message": "Usuário já possui acesso de administrador."}

    new_admin = models.Admin(user_id=user.id)
    db.add(new_admin)
    db.commit()
    return {"status": "success", "message": "Membro da COMGRAD promovido a administrador com sucesso!"}

@router.post("/users/batch")
async def batch_register(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Cadastra em lote múltiplos usuários de um arquivo CSV.

    Parâmetros de entrada:
        file (UploadFile): Arquivo CSV com as colunas de dados dos usuários (name, email, card_number, password, role, etc).
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status do cadastro com número de criados e lista de possíveis erros encontrados por linha.
    """
    content = await file.read()
    text = content.decode("utf-8")
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    
    success_count = 0
    errors = []
    
    for row_idx, row in enumerate(reader, start=1):
        try:
            role = row.get("role", "").strip().lower()
            name = row.get("name", "").strip()
            email = row.get("email", "").strip()
            card_number_str = row.get("card_number", "").strip()
            password = row.get("password", "").strip()
            
            if not role or not name or not email or not card_number_str or not password:
                errors.append(f"Linha {row_idx}: Campos obrigatórios ausentes.")
                continue
                
            try:
                card_number = int(card_number_str)
            except ValueError:
                errors.append(f"Linha {row_idx}: Matrícula inválida.")
                continue
                
            # Check duplicate
            existing = db.query(models.User).filter(
                (models.User.card_number == card_number) | (models.User.email == email)
            ).first()
            if existing:
                errors.append(f"Linha {row_idx}: E-mail ou matrícula já cadastrados ({email} / {card_number}).")
                continue
                
            must_change = False
            if role == "student":
                must_change = True
                
            new_user = models.User(
                name=name,
                email=email,
                card_number=card_number,
                password=hash_password(password),
                must_change_password=must_change
            )
            db.add(new_user)
            db.flush()
            
            if role == "student":
                course = row.get("course", "").strip()
                curr_semester_str = row.get("current_semester", "").strip()
                curriculum_id_str = row.get("curriculum_id", "").strip()
                
                if not course or not curr_semester_str:
                    db.rollback()
                    errors.append(f"Linha {row_idx}: Estudante precisa de curso e semestre.")
                    continue
                    
                try:
                    curr_semester = int(curr_semester_str)
                except ValueError:
                    db.rollback()
                    errors.append(f"Linha {row_idx}: Semestre do estudante inválido.")
                    continue
                    
                curriculum_id = None
                if curriculum_id_str:
                    try:
                        curriculum_id = int(curriculum_id_str)
                    except ValueError:
                        pass
                if not curriculum_id:
                    # Fallback based on course name
                    if "engenharia" in course.lower():
                        curriculum_id = 2
                    else:
                        curriculum_id = 1
                
                student = models.Student(
                    user_id=new_user.id,
                    current_semester=curr_semester,
                    course=course,
                    curriculum_id=curriculum_id
                )
                db.add(student)
            elif role == "comgrad":
                comgrad_role = row.get("comgrad_role", "").strip() or "Membro"
                comgrad = models.COMGRAD(
                    user_id=new_user.id,
                    role=comgrad_role
                )
                db.add(comgrad)
            elif role == "admin":
                admin = models.Admin(
                    user_id=new_user.id
                )
                db.add(admin)
            else:
                db.rollback()
                errors.append(f"Linha {row_idx}: Papel '{role}' inválido.")
                continue
                
            db.commit()
            success_count += 1
        except Exception as e:
            db.rollback()
            errors.append(f"Linha {row_idx}: Erro inesperado: {str(e)}")
            
    return {
        "status": "success",
        "created": success_count,
        "errors": errors
    }

@router.post("/users/{user_id}/toggle-status")
def toggle_user_status(user_id: int, db: Session = Depends(get_db)):
    """
    Alterna o status de atividade (ativo/inativo) de um usuário. Administradores não podem ser desabilitados.

    Parâmetros de entrada:
        user_id (int): O ID do usuário a ter o status alterado.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem indicando o novo status (habilitado/desabilitado).
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Check if the user is an admin
    if user.admin is not None:
        raise HTTPException(status_code=400, detail="Administradores não podem ser desabilitados.")
        
    user.is_active = not getattr(user, 'is_active', True)
    db.commit()
    db.refresh(user)
    status_str = "habilitado" if user.is_active else "desabilitado"
    return {"status": "success", "message": f"Usuário {status_str} com sucesso!"}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Remove definitivamente um usuário do sistema (com exceção de administradores).
    Remove também perfis dependentes (student/comgrad) vinculados a este usuário.

    Parâmetros de entrada:
        user_id (int): O ID do usuário a ser excluído.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem confirmativa.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Check if the user is an admin
    if user.admin is not None:
        raise HTTPException(status_code=400, detail="Administradores não podem ser removidos.")
    
    # Delete associations manually to avoid integrity constraint violations
    if user.student is not None:
        db.delete(user.student)
    if user.comgrad is not None:
        db.delete(user.comgrad)
        
    db.delete(user)
    db.commit()
    return {"status": "success", "message": "Usuário removido com sucesso!"}

@router.get("/curricula")
def get_curricula(db: Session = Depends(get_db)):
    """
    Retorna todos os currículos (grades curriculares) cadastrados na plataforma.

    Parâmetros de entrada:
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        list: Lista contendo dicionários com ID e nome de cada currículo.
    """
    curricula = db.query(models.Curriculum).all()
    return [{"id": c.id, "name": c.name} for c in curricula]

class CourseCreateRequest(BaseModel):
    code: str
    name: str
    credits: int
    min_credits_required: int = 0
    prerequisites: List[str] = []

@router.post("/courses")
def create_course(req: CourseCreateRequest, db: Session = Depends(get_db)):
    """
    Cria uma nova disciplina no banco de dados e mapeia seus pré-requisitos através de seus códigos.

    Parâmetros de entrada:
        req (CourseCreateRequest): Dados da disciplina (código, nome, créditos, pré-requisitos).
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem.
    """
    existing = db.query(models.Course).filter(models.Course.code == req.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Disciplina com este código já existe.")
        
    course = models.Course(
        code=req.code,
        name=req.name,
        credits=req.credits,
        min_credits_required=req.min_credits_required
    )
    db.add(course)
    db.flush()
    
    for pre_code in req.prerequisites:
        pre = db.query(models.Course).filter(models.Course.code == pre_code).first()
        if pre:
            course.prerequisites.append(pre)
            
    db.commit()
    return {"status": "success", "message": "Disciplina criada com sucesso!"}

@router.post("/courses/batch")
async def batch_create_courses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Cria em lote múltiplas disciplinas por meio de um arquivo CSV.

    Parâmetros de entrada:
        file (UploadFile): Arquivo CSV contendo os dados das disciplinas (code, name, credits, prerequisites, etc).
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status do cadastro com número de criados e lista de possíveis erros por linha.
    """
    content = await file.read()
    text = content.decode("utf-8")
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    
    success_count = 0
    errors = []
    
    for row_idx, row in enumerate(reader, start=1):
        try:
            code = row.get("code", "").strip()
            name = row.get("name", "").strip()
            credits_str = row.get("credits", "").strip()
            min_credits_str = row.get("min_credits_required", "").strip() or "0"
            prereqs_str = row.get("prerequisites", "").strip()
            
            if not code or not name or not credits_str:
                errors.append(f"Linha {row_idx}: Código, nome e créditos são obrigatórios.")
                continue
                
            try:
                credits = int(credits_str)
                min_credits = int(min_credits_str)
            except ValueError:
                errors.append(f"Linha {row_idx}: Créditos ou créditos mínimos inválidos.")
                continue
                
            existing = db.query(models.Course).filter(models.Course.code == code).first()
            if existing:
                errors.append(f"Linha {row_idx}: Disciplina com código '{code}' já existe.")
                continue
                
            course = models.Course(
                code=code,
                name=name,
                credits=credits,
                min_credits_required=min_credits
            )
            db.add(course)
            db.flush()
            
            if prereqs_str:
                for pre_code in prereqs_str.split(";"):
                    pre_code = pre_code.strip()
                    if not pre_code:
                        continue
                    pre = db.query(models.Course).filter(models.Course.code == pre_code).first()
                    if pre:
                        course.prerequisites.append(pre)
                        
            db.commit()
            success_count += 1
        except Exception as e:
            db.rollback()
            errors.append(f"Linha {row_idx}: Erro inesperado: {str(e)}")
            
    return {
        "status": "success",
        "created": success_count,
        "errors": errors
    }

class ScheduleItem(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str
    room: str

class SectionCreateRequest(BaseModel):
    course_id: int
    section_code: str
    semester: str
    capacity: int
    professor_name: str
    schedules: List[ScheduleItem]

@router.post("/sections")
def create_section(req: SectionCreateRequest, db: Session = Depends(get_db)):
    """
    Cria uma nova turma e associa seus respectivos dias, horários e salas.

    Parâmetros de entrada:
        req (SectionCreateRequest): Dados da turma a ser criada (ID da disciplina, código, semestre, vagas, horários).
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem.
    """
    course = db.query(models.Course).filter(models.Course.id == req.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada.")
        
    section = models.ClassSection(
        course_id=req.course_id,
        section_code=req.section_code,
        semester=req.semester,
        capacity=req.capacity,
        professor_name=req.professor_name
    )
    db.add(section)
    db.flush()
    
    from datetime import datetime
    for sched in req.schedules:
        try:
            start_t = datetime.strptime(sched.start_time, "%H:%M").time()
            end_t = datetime.strptime(sched.end_time, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Horário inválido: {sched.start_time}-{sched.end_time}")
            
        schedule = models.ClassSchedule(
            class_section_id=section.id,
            day_of_week=sched.day_of_week,
            start_time=start_t,
            end_time=end_t,
            room=sched.room
        )
        db.add(schedule)
        
    db.commit()
    return {"status": "success", "message": "Turma criada com sucesso!"}

@router.post("/sections/batch")
async def batch_create_sections(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Cria em lote múltiplas turmas por meio do envio de um arquivo CSV. Mapeia dias em português para inglês.

    Parâmetros de entrada:
        file (UploadFile): Arquivo CSV com colunas de dados das turmas e strings de horários formatados.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status com número de turmas criadas e lista de erros por linha.
    """
    content = await file.read()
    text = content.decode("utf-8")
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    
    success_count = 0
    errors = []
    from datetime import datetime
    
    for row_idx, row in enumerate(reader, start=1):
        try:
            course_code = row.get("course_code", "").strip()
            section_code = row.get("section_code", "").strip()
            semester = row.get("semester", "").strip()
            capacity_str = row.get("capacity", "").strip()
            professor_name = row.get("professor_name", "").strip()
            schedules_str = row.get("schedules", "").strip()
            
            if not course_code or not section_code or not semester or not capacity_str:
                errors.append(f"Linha {row_idx}: Disciplina, turma, semestre e vagas são obrigatórios.")
                continue
                
            try:
                capacity = int(capacity_str)
            except ValueError:
                errors.append(f"Linha {row_idx}: Vagas inválidas.")
                continue
                
            course = db.query(models.Course).filter(models.Course.code == course_code).first()
            if not course:
                errors.append(f"Linha {row_idx}: Disciplina com código '{course_code}' não existe.")
                continue
                
            section = models.ClassSection(
                course_id=course.id,
                section_code=section_code,
                semester=semester,
                capacity=capacity,
                professor_name=professor_name
            )
            db.add(section)
            db.flush()
            
            if schedules_str:
                parts = schedules_str.split(";")
                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    p_parts = p.split()
                    if len(p_parts) < 3:
                        errors.append(f"Linha {row_idx}: Horário '{p}' em formato inválido.")
                        continue
                        
                    day_input = p_parts[0]
                    day_en = DAY_MAPPING.get(day_input, day_input)
                    time_range = p_parts[1]
                    room = " ".join(p_parts[2:])
                    
                    try:
                        start_str, end_str = time_range.split("-")
                        start_t = datetime.strptime(start_str.strip(), "%H:%M").time()
                        end_t = datetime.strptime(end_str.strip(), "%H:%M").time()
                    except Exception:
                        errors.append(f"Linha {row_idx}: Intervalo de horário '{time_range}' inválido.")
                        continue
                        
                    schedule = models.ClassSchedule(
                        class_section_id=section.id,
                        day_of_week=day_en,
                        start_time=start_t,
                        end_time=end_t,
                        room=room
                    )
                    db.add(schedule)
                    
            db.commit()
            success_count += 1
        except Exception as e:
            db.rollback()
            errors.append(f"Linha {row_idx}: Erro inesperado: {str(e)}")
            
    return {
        "status": "success",
        "created": success_count,
        "errors": errors
    }

@router.post("/curriculum/{curriculum_id}/update")
async def update_curriculum(curriculum_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Atualiza as disciplinas vinculadas a um determinado currículo a partir do upload de um arquivo CSV.
    Remove todos os vínculos anteriores antes de inserir as novas disciplinas.

    Parâmetros de entrada:
        curriculum_id (int): ID do currículo a ser atualizado.
        file (UploadFile): Arquivo CSV com colunas indicando código da disciplina, semestre etapa e obrigatoriedade.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status indicando sucesso ou erro com lista de erros encontrados no arquivo.
    """
    curr = db.query(models.Curriculum).filter(models.Curriculum.id == curriculum_id).first()
    if not curr:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")
        
    content = await file.read()
    text = content.decode("utf-8")
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    
    errors = []
    success_entries = []
    
    for row_idx, row in enumerate(reader, start=1):
        course_code = row.get("course_code", "").strip()
        semester_str = row.get("semester", "").strip()
        mandatory_str = row.get("mandatory", "").strip() or "1"
        
        if not course_code or not semester_str:
            errors.append(f"Linha {row_idx}: Código da disciplina e etapa (semestre) são obrigatórios.")
            continue
            
        try:
            semester = int(semester_str)
            mandatory = mandatory_str.strip() in ("1", "True", "true", "Obrigatória")
        except ValueError:
            errors.append(f"Linha {row_idx}: Etapa ou obrigatoriedade inválidos.")
            continue
            
        course = db.query(models.Course).filter(models.Course.code == course_code).first()
        if not course:
            errors.append(f"Linha {row_idx}: Disciplina com código '{course_code}' não existe.")
            continue
            
        success_entries.append({
            "course_id": course.id,
            "semester": semester,
            "mandatory": mandatory
        })
        
    if errors:
        return {
            "status": "error",
            "message": "Erros encontrados no arquivo CSV. O currículo não foi modificado.",
            "errors": errors
        }
        
    db.query(models.CurriculumCourse).filter(models.CurriculumCourse.curriculum_id == curriculum_id).delete()
    
    for entry in success_entries:
        cc = models.CurriculumCourse(
            curriculum_id=curriculum_id,
            course_id=entry["course_id"],
            semester=entry["semester"],
            mandatory=entry["mandatory"]
        )
        db.add(cc)
        
    db.commit()
    return {
        "status": "success",
        "message": f"Currículo de '{curr.name}' atualizado com sucesso! {len(success_entries)} disciplinas vinculadas."
    }
