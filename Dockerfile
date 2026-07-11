# Usa a imagem oficial leve do Python
FROM python:3.11-slim

# Instala o FFmpeg e as dependências pra instalar o Deno (curl + unzip)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Instala o Deno (runtime JS exigido pelo yt-dlp desde a versão 2025.11.12
# para resolver os desafios de assinatura/token do YouTube)
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:${PATH}"
RUN deno --version

# Define a pasta de trabalho dentro do servidor
WORKDIR /app

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da API
# ⚠️ cookies.txt NÃO deve vir daqui: ele já entra via Secret File do Render
# em /etc/secrets/cookies.txt. Se ainda existir cookies.txt no repositório,
# remova e adicione ao .gitignore (o repo é público).
COPY . .

# Expõe a porta dinâmica do Render e inicia o servidor Uvicorn
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
