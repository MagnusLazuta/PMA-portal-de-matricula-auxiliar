from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

SQLALCHEMY_DATABASE_URL = DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_compatibility():
    """
    Verifica e atualiza o esquema do banco de dados SQLite para garantir compatibilidade,
    adicionando colunas que possam estar faltando nas tabelas 'users', 'class_request_poll',
    'class_section' e 'time_restriction'.

    Parâmetros de entrada:
        Nenhum.

    Parâmetros de saída:
        Nenhum.
    """
    if engine.dialect.name != "sqlite":
        return

    column_updates = {
        "users": {
            "must_change_password": "ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0",
            "is_active": "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"
        },
        "class_request_poll": {
            "suggested_slots": "ALTER TABLE class_request_poll ADD COLUMN suggested_slots TEXT"
        },
        "class_section": {
            "professor_name": "ALTER TABLE class_section ADD COLUMN professor_name VARCHAR"
        },
        "time_restriction": {
            "restriction_type": "ALTER TABLE time_restriction ADD COLUMN restriction_type VARCHAR DEFAULT 'hard_block'",
            "course_id": "ALTER TABLE time_restriction ADD COLUMN course_id INTEGER",
            "preferred_professor": "ALTER TABLE time_restriction ADD COLUMN preferred_professor VARCHAR",
            "preference_order": "ALTER TABLE time_restriction ADD COLUMN preference_order INTEGER",
            "importance_level": "ALTER TABLE time_restriction ADD COLUMN importance_level VARCHAR",
            "score_weight": "ALTER TABLE time_restriction ADD COLUMN score_weight INTEGER DEFAULT 0",
            "is_mandatory": "ALTER TABLE time_restriction ADD COLUMN is_mandatory BOOLEAN DEFAULT 1",
        },
    }

    with engine.begin() as connection:
        for table_name, updates in column_updates.items():
            existing_columns = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }
            for column_name, statement in updates.items():
                if column_name not in existing_columns:
                    connection.execute(text(statement))

def get_db():
    """
    Gera uma sessão local de banco de dados (SQLAlchemy Session) e garante que ela seja
    fechada após o uso. Utilizado como dependência em rotas do FastAPI.

    Parâmetros de entrada:
        Nenhum.

    Parâmetros de saída:
        db (Session): Uma sessão do banco de dados (yielded).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
