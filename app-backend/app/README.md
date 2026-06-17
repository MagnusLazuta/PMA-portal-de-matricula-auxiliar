# Schedule Generator API

Esta é uma API FastAPI para gerenciamento de cursos, estudantes e geração automática de horários.

## Requisitos

- Python 3.9+
- Pip

## Como Rodar a Aplicação

1. **Instale as dependências:**
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic httpx pytest
   ```

2. **Inicie o servidor (a partir da raiz do backend):**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Como Popular o Banco de Dados (a partir da raiz do backend):**
   Para popular o banco de dados SQLite (`app/schedule.db`) com as disciplinas, pré-requisitos e turmas/horários da UFRGS a partir do arquivo `ufrgs_data.json`:
   ```bash
   .venv/bin/python populate_db.py
   ```
   *Opções disponíveis:*
   - `--json <caminho>`: Caminho personalizado para o arquivo JSON (padrão: `../ufrgs_data.json`).
   - `--semester <semestre>`: Especificar o semestre das turmas a serem inseridas (padrão: `2026/1`).
   - `--no-clean`: Não limpa o banco de dados antes de realizar a inserção.

4. **Acesse a documentação interativa (Swagger UI):**
   Abra o seu navegador em: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Como Rodar os Testes

Para rodar a suíte de testes automatizados:

```bash
pytest app/tests/
```

Os testes utilizam um banco de dados SQLite em memória, portanto, não afetam os seus dados locais.

## Estrutura do Projeto

- `app/main.py`: Ponto de entrada da aplicação.
- `app/models/`: Modelos de banco de dados (SQLAlchemy).
- `app/routers/`: Definições de rotas da API.
- `app/services/`: Lógica de negócio e persistência.
- `app/schemas.py`: Esquemas de validação de dados (Pydantic).
- `app/tests/`: Testes automatizados.
