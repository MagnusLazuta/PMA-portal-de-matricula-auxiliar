FROM python:3.11-slim

WORKDIR /app

# Instala dependências de compilação essenciais para o Python e poppler-utils (pdftotext)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos
COPY requirements.txt .

# Instala dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos do backend
COPY . .

# Expõe a porta do FastAPI
EXPOSE 8000

# Executa o servidor Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
