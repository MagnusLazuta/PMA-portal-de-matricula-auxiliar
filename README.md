# Trabalho Prático da cadeira de Engenharia de Software

## Configuração do Ambiente de Desenvolvimento

Este projeto é dividido em dois componentes principais: um frontend em Vue.js e um backend em FastAPI (Python). Siga as instruções abaixo para configurar cada um deles.

### Pré-requisitos

- [Node.js](https://nodejs.org/) (versão 20 ou superior)
- [Python](https://www.python.org/) (versão 3.10 ou superior)

---

### 1. Backend (FastAPI)

O backend está localizado no diretório `src/backend`.

1. **Acesse o diretório do backend:**
   ```bash
   cd src/backend
   ```

2. **Crie um ambiente virtual:**
   ```bash
   # Linux/macOS
   python3 -m venv .venv

   # Windows
   python -m venv .venv
   ```

3. **Ative o ambiente virtual:**
   ```bash
   # Linux/macOS
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

4. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Inicie o servidor de desenvolvimento:**
   ```bash
   uvicorn app.main:app --reload
   ```

O backend estará acessível em `http://127.0.0.1:8000`. Você pode acessar a documentação interativa da API (Swagger UI) em `http://127.0.0.1:8000/docs`.

---

### 2. Frontend (Vue.js)

O frontend está localizado no diretório `app-frontend`.

1. **Acesse o diretório do frontend:**
   ```bash
   cd app-frontend
   ```

2. **Instale as dependências:**
   ```bash
   npm install
   ```

3. **Inicie o servidor de desenvolvimento:**
   ```bash
   npm run dev
   ```

O frontend estará acessível em `http://localhost:5173` (ou na porta indicada no terminal).

