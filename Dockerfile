# Usa a imagem oficial leve do Python
FROM python:3.11-slim

# Instala o FFmpeg nativamente no sistema operativo Linux
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Define a pasta de trabalho dentro do servidor
WORKDIR /app

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da API e o ficheiro cookies.txt (se existir)
COPY . .

# Expõe a porta dinâmica do Render e inicia o servidor Uvicorn
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
