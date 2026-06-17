# Trabalho Prático de Engenharia de Software

Este projeto consiste em um sistema de gerenciamento acadêmico e geração de horários dividido em dois componentes principais:
- **Frontend**: Aplicação SPA construída com Vue.js, Vite e Vuetify.
- **Backend**: API RESTful construída com FastAPI, SQLAlchemy (SQLite) e Pydantic.

---

## 🚀 Instalação em Ambiente de Produção (Docker Compose)

Esta seção descreve a implantação simplificada e isolada de todos os serviços (frontend e backend) do sistema através do **Docker Compose**. Esta abordagem é a ideal para demonstrações rápidas e ambientes produtivos de homologação.

### Pré-requisitos
Para executar em ambiente de produção com Docker, a máquina hospedeira necessita apenas de:
- [Docker](https://www.docker.com/) instalado e em execução.
- [Docker Compose](https://docs.docker.com/compose/) instalado (ou Docker Desktop).
- Estar com o repositório clonado localmente.

*Nota: Não há a necessidade de instalar Python, Node.js ou gerenciadores locais de dependências na máquina hospedeira.*

### Passo a Passo
1. **Suba os serviços utilizando o docker compose:**
   ```bash
   docker compose up --build -d
   ```
   *Este comando irá buildar as imagens do frontend e do backend, inicializar os containers em segundo plano e expor as portas no seu host.*
2. **Acesso:**
   - **Frontend:** [http://localhost](http://localhost) (ou o endereço IP da máquina hospedeira).
   - **Backend (Documentação Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs) (se habilitado).

*Nota: O banco de dados SQLite (`schedule.db`) é criado automaticamente na primeira execução e persistido no volume local `./app-backend/app`.*

---

## 🛠️ Instalação em Ambiente de Desenvolvimento (Local / Sem Docker)

Esta seção descreve a configuração passo a passo necessária para configurar e executar o ambiente de desenvolvimento local diretamente no sistema operacional host, facilitando atividades de depuração e desenvolvimento ativo com *hot-reloading*.

### Pré-requisitos
Antes de iniciar, certifique-se de que sua máquina possui as ferramentas descritas abaixo instaladas e configuradas:
- [Node.js](https://nodejs.org/) versão 20 ou superior.
- [Python](https://www.python.org/) versão 3.10 ou superior.
- Estar com o repositório clonado localmente.

### 1. Configuração do Backend (FastAPI)
O backend está localizado no diretório `app-backend`.

1. **Acesse o diretório do backend:**
   ```bash
   cd app-backend
   ```

2. **Crie o arquivo de variáveis de ambiente `.env` a partir do modelo `env-examplo` fornecido:**
   - No **Linux ou macOS**:
     ```bash
     cp env-examplo .env
     ```
   - No **Windows (Prompt de Comando - cmd)**:
     ```cmd
     copy env-examplo .env
     ```
   - No **Windows (PowerShell)**:
     ```powershell
     Copy-Item env-examplo .env
     ```

   O arquivo `.env` gerado define parâmetros essenciais para a inicialização e comportamento do backend:
   - `DEBUG`: Booleano que define se a API rodará em modo de depuração. Se definido como `true`, o FastAPI disponibilizará a documentação interativa Swagger UI no endpoint `/docs` e a documentação estática ReDoc no endpoint `/redoc`. Em produção, deve ser configurado como `false` por segurança.
   - `DATABASE_URL`: String de conexão com o banco de dados. O padrão é `sqlite:///./app/schedule.db`, utilizando um arquivo SQLite local. Caso o sistema seja escalado para outro banco de dados (como PostgreSQL), esta variável deve conter a URI correspondente.

3. **Crie o ambiente virtual:**
   ```bash
   python -m venv .venv
   ```

4. **Ative o ambiente virtual:**
   - No **Linux ou macOS**:
     ```bash
     source .venv/bin/activate
     ```
   - No **Windows (Prompt de Comando - cmd)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - No **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```

5. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

6. **(Opcional) Popule o banco de dados com dados iniciais da UFRGS:**
   ```bash
   python convert_data_to_csv.py
   python populate_db.py
   ```

7. **Inicialize o backend:**
   ```bash
   uvicorn app.main:app --reload
   ```
   O backend estará disponível para acesso através do endereço [http://localhost:8000](http://localhost:8000). A documentação Swagger UI estará disponível em [http://localhost:8000/docs](http://localhost:8000/docs).

#### Execução de Testes Automatizados
Para validar se a instalação foi realizada de forma correta, execute a suíte de testes automatizados com o ambiente virtual ativo:
```bash
pytest app/tests/
```
*Nota: Os testes utilizam um banco de dados temporário em memória e não interferem nos dados locais de desenvolvimento.*

### 2. Configuração do Frontend (Vue.js)
O frontend está localizado no diretório `app-frontend`.

1. **Acesse o diretório do frontend:**
   ```bash
   cd app-frontend
   ```

2. **Instale as dependências:**
   ```bash
   npm install
   ```

3. **Inicialize o frontend:**
   ```bash
   npm run dev
   ```
   O frontend estará disponível para acesso através do endereço [http://localhost:5173](http://localhost:5173).


