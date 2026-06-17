from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from ..database import get_db
from .. import models
from ..utils.security import hash_password, verify_password


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

class LoginRequest(BaseModel):
    card_number: str = Field(..., description="Matrícula de 8 dígitos")
    password: str

class LoginResponse(BaseModel):
    user_id: int
    name: str
    role: str
    student_id: int | None = None
    must_change_password: bool = False

class ForgotPasswordRequest(BaseModel):
    card_number: int

class ResetPasswordRequest(BaseModel):
    card_number: int
    new_password: str

class ChangePasswordRequest(BaseModel):
    user_id: int
    new_password: str

class ProfileResponse(BaseModel):
    user_id: int
    name: str
    email: str
    card_number: int
    role: str
    # student fields
    course: str | None = None
    current_semester: int | None = None
    curriculum_name: str | None = None
    # comgrad fields
    comgrad_role: str | None = None

class UpdateEmailRequest(BaseModel):
    email: str

class SetupStatusResponse(BaseModel):
    setup_required: bool

class SetupAdminRequest(BaseModel):
    name: str
    email: str
    card_number: str
    password: str




@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Realiza a autenticação do usuário por meio de sua matrícula e senha.
    Retorna os dados cadastrais básicos e o papel do usuário (student, admin, comgrad, etc).

    Parâmetros de entrada:
        req (LoginRequest): Dados do login contendo a matrícula de 8 dígitos e senha.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        LoginResponse: Dicionário com dados básicos do usuário logado (id, nome, role, student_id, se precisa alterar senha).
    """
    if not (req.card_number.isdigit() and len(req.card_number) == 8):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A matrícula deve conter exatamente 8 dígitos numéricos."
        )
    
    try:
        card_num_int = int(req.card_number)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A matrícula deve ser numérica."
        )
        
    user = db.query(models.User).filter(models.User.card_number == card_num_int).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Matrícula ou senha incorreta."
        )
        
    if not getattr(user, 'is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este usuário foi desativado pelo administrador."
        )
        
    role = "student"
    student_id = None
    if user.admin is not None and user.comgrad is not None:
        role = "comgrad_admin"
    elif user.admin is not None:
        role = "admin"
    elif user.comgrad is not None:
        role = "comgrad"
    elif user.student is not None:
        role = "student"
        student_id = user.student.user_id

    return {
        "user_id": user.id,
        "name": user.name,
        "role": role,
        "student_id": student_id,
        "must_change_password": user.must_change_password or False
    }

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Simula uma requisição de 'esqueci minha senha' enviando email de recuperação.

    Parâmetros de entrada:
        req (ForgotPasswordRequest): Contém o número de matrícula do usuário.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso, o email para onde foi enviado e uma mensagem explicativa.
    """
    user = db.query(models.User).filter(models.User.card_number == req.card_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada.")
    return {
        "status": "success",
        "email": user.email,
        "message": f"E-mail de recuperação enviado para {user.email}"
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Redefine a senha de um usuário pelo número de matrícula (utilizado pelo fluxo de recuperação).

    Parâmetros de entrada:
        req (ResetPasswordRequest): Contém a matrícula e a nova senha em texto plano.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem.
    """
    user = db.query(models.User).filter(models.User.card_number == req.card_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    user.password = hash_password(req.new_password)
    user.must_change_password = False
    db.commit()
    return {"status": "success", "message": "Senha redefinida com sucesso!"}

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, db: Session = Depends(get_db)):
    """
    Permite a um usuário logado alterar sua senha atual.

    Parâmetros de entrada:
        req (ChangePasswordRequest): Contém o ID do usuário e a nova senha.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem.
    """
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    user.password = hash_password(req.new_password)
    user.must_change_password = False
    db.commit()
    return {"status": "success", "message": "Senha alterada com sucesso!"}



@router.get("/profile/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Consulta o perfil completo de um usuário contendo suas informações acadêmicas correspondentes.

    Parâmetros de entrada:
        user_id (int): O ID do usuário.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        ProfileResponse: Dicionário com informações detalhadas do perfil do usuário.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    
    role = "student"
    course = None
    current_semester = None
    curriculum_name = None
    comgrad_role = None
    
    if user.admin is not None and user.comgrad is not None:
        role = "comgrad_admin"
        comgrad_role = user.comgrad.role
    elif user.admin is not None:
        role = "admin"
    elif user.comgrad is not None:
        role = "comgrad"
        comgrad_role = user.comgrad.role
    elif user.student is not None:
        role = "student"
        course = user.student.course
        current_semester = user.student.current_semester
        if user.student.curriculum_obj is not None:
            curriculum_name = user.student.curriculum_obj.name
            
    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "card_number": user.card_number,
        "role": role,
        "course": course,
        "current_semester": current_semester,
        "curriculum_name": curriculum_name,
        "comgrad_role": comgrad_role
    }

@router.put("/profile/{user_id}/email")
def update_email(user_id: int, req: UpdateEmailRequest, db: Session = Depends(get_db)):
    """
    Permite ao usuário atualizar o seu endereço de email cadastrado.

    Parâmetros de entrada:
        user_id (int): O ID do usuário.
        req (UpdateEmailRequest): Contém o novo endereço de email.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem.
    """
    import re
    
    email = req.email.strip()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail não pode ser vazio."
        )
        
    email_regex = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    if not email_regex.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de e-mail inválido."
        )
        
    # Check if duplicate email exists for other users
    existing = db.query(models.User).filter(
        models.User.email == email,
        models.User.id != user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já está sendo utilizado por outro usuário."
        )
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
        
    user.email = email
    db.commit()
    return {"status": "success", "message": "E-mail atualizado com sucesso!"}

@router.get("/setup-status", response_model=SetupStatusResponse)
def get_setup_status(db: Session = Depends(get_db)):
    """
    Verifica se o sistema precisa passar pela configuração inicial (setup) devido à ausência de administradores cadastrados.

    Parâmetros de entrada:
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        SetupStatusResponse: Objeto indicando se a configuração é requerida (setup_required: bool).
    """
    has_admin = db.query(models.User).join(models.Admin).count() > 0
    return {"setup_required": not has_admin}

@router.post("/setup-admin")
def setup_admin(req: SetupAdminRequest, db: Session = Depends(get_db)):
    """
    Cadastra o primeiro administrador (primary admin) do sistema no primeiro acesso.

    Parâmetros de entrada:
        req (SetupAdminRequest): Dados do administrador a ser cadastrado.
        db (Session): Sessão do banco de dados (injetada).

    Parâmetros de saída:
        dict: Status de sucesso e mensagem.
    """
    import re
    has_admin = db.query(models.User).join(models.Admin).count() > 0
    if has_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O administrador primário já foi cadastrado."
        )
        
    email = req.email.strip()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail não pode ser vazio."
        )
        
    email_regex = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    if not email_regex.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de e-mail inválido."
        )
        
    if not (req.card_number.isdigit() and len(req.card_number) == 8):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A matrícula deve conter exatamente 8 dígitos numéricos."
        )
        
    card_num_int = int(req.card_number)
    # Check duplicate email or card number
    existing = db.query(models.User).filter(
        (models.User.email == email) | (models.User.card_number == card_num_int)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail ou matrícula já cadastrados."
        )
        
    new_user = models.User(
        name=req.name,
        email=email,
        card_number=card_num_int,
        password=hash_password(req.password),
        must_change_password=False
    )
    db.add(new_user)
    db.flush()
    
    new_admin = models.Admin(user_id=new_user.id)
    db.add(new_admin)
    db.commit()
    
    return {"status": "success", "message": "Administrador primário cadastrado com sucesso!"}
