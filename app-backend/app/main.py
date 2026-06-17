from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine, ensure_schema_compatibility
from .routers import courses, students, sections, restrictions, scheduler, polls, auth, admin
from .schemas.enums import DayOfWeek

# Create database tables
models.Base.metadata.create_all(bind=engine)
ensure_schema_compatibility()

# Seed default curricula if missing (needed for first-run setup)
from .database import SessionLocal
db = SessionLocal()
try:
    cc = db.query(models.Curriculum).filter(models.Curriculum.id == 1).first()
    if not cc:
        db.add(models.Curriculum(id=1, name="Ciência da Computação"))
    ec = db.query(models.Curriculum).filter(models.Curriculum.id == 2).first()
    if not ec:
        db.add(models.Curriculum(id=2, name="Engenharia de Computação"))
    db.commit()
except Exception as e:
    print(f"Erro ao inicializar currículos padrão: {e}")
    db.rollback()
finally:
    db.close()

from .config import DEBUG
app = FastAPI(
    title="Schedule Generator API",
    description="API for managing courses, students and generating schedules",
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None
)

# Enable CORS for frontend requests during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(courses.router)
app.include_router(students.router)
app.include_router(sections.router)
app.include_router(restrictions.router)
app.include_router(scheduler.router)
app.include_router(polls.router)

@app.get("/")
def root():
    """
    Rota raiz da API. Retorna uma mensagem de boas-vindas.

    Parâmetros de entrada:
        Nenhum.

    Parâmetros de saída:
        dict: Um dicionário contendo a mensagem de boas-vindas ("message": "Welcome to the Schedule Generator API").
    """
    return {"message": "Welcome to the Schedule Generator API"}


@app.get("/days-of-week/")
def list_days_of_week():
    """
    Retorna a lista de dias da semana disponíveis no sistema com base no enum DayOfWeek.

    Parâmetros de entrada:
        Nenhum.

    Parâmetros de saída:
        list: Uma lista de strings representando os dias da semana.
    """
    return [day.value for day in DayOfWeek]
