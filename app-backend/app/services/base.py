from sqlalchemy.orm import Session

class BaseService:
    def __init__(self, db: Session):
        """
        Inicializa o serviço base com uma sessão do banco de dados do SQLAlchemy.

        Parâmetros de entrada:
            db (Session): Sessão ativa do banco de dados.

        Parâmetros de saída:
            Nenhum.
        """
        self.db = db
