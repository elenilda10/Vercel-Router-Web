# Ficheiro: app.py | Motor Próprio com TLS Impersonation (Burlou a AWS/Render!)

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob

app = FastAPI(title="Krust Audio API - Anti-Bot Shield")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def limpar_ficheiros_temporarios(caminho_base: str):
    try:
        ficheiros = glob.glob(f"{caminho_base}*")
        for f in ficheiros:
            if os.path.exists(f):
                os.remove(f)
                print(f"🗑️ Faxina: Ficheiro {f} removido com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao limpar ficheiros temporários: {str(e)}")

@app.get("/")
def home():
    return {
        "status": "online",
        "blindagem": "TLS Fingerprinting ativado (impersonate: chrome)",
        "plataformas_clientes": "Android, iOS, TV, Web",
        "mensagem": "API Própria de Manipulação de Áudio a correr no Render! 🚀"
    }

@app.get("/api/audio")
def extrair_e_manipular(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="Link do vídeo ou música do YouTube"),
    formato: str = Query("mp3", description="Formato desejado (mp3 ou m4a)")
):
    if not url:
        raise HTTPException(status_code=400, detail="URL não fornecida.")

    # Limpeza de parâmetros de rastreamento do link
    url_limpa = url.split("?si=")[0].split("&si=")[0].split("?is=")[0].strip()

    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    output_template = f"{pasta_tmp}/%(id)s.%(ext)s"

    # 🛡️ O SETUP PERFEITO (Baseado na sua pesquisa do repositório oficial):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writethumbnail': True, # Baixa a capa da música
        
        # 1. BURLAR TLS FINGERPRINTING:
        # Força o servidor Linux a usar a rede com a assinatura digital do Chrome
        'impersonate': 'chrome',
        
        # 2. SISTEMA DE CLIENTES MÚLTIPLOS (Fallback):
        # Tenta os clientes mais difíceis de bloquear primeiro (Android/iOS/TV)
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'tv', 'web'],
                'player_skip': ['webpage', 'configs', 'js'],
            }
        },
        
        # 3. PÓS-PROCESSAMENTO VIA FFMPEG (MP3 com Capa embutida):
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': formato,
                'preferredquality': '192',
            },
            {'key': 'FFmpegMetadata'},
            {'key': 'EmbedThumbnail'}
        ],
    }

    try:
        print(f"⚡ Iniciando download blindado com assinatura Chrome TLS para: {url_limpa}...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Baixa e converte diretamente na AWS sem erro 403!
            info = ydl.extract_info(url_limpa, download=True)
            video_id = info.get('id')
            caminho_base = f"{pasta_tmp}/{video_id}"
            arquivo_mp3 = f"{caminho_base}.{formato}"

            if not os.path.exists(arquivo_mp3):
                raise Exception("O arquivo não foi gerado após a extração.")

            print("🏆 SUCESSO! A barreira de IP e TLS da Amazon foi rompida!")
            
            # Agenda a faxina após o envio para o Telegram
            background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)

            return FileResponse(
                path=arquivo_mp3,
                filename=f"{info.get('title', 'Audio')}.{formato}",
                media_type=f"audio/{formato}"
            )

    except Exception as e:
        if 'caminho_base' in locals():
            limpar_ficheiros_temporarios(caminho_base)
            
        return JSONResponse(
            status_code=500,
            content={
                "sucesso": False,
                "erro": str(e),
                "dica": "Se o erro persistir, verifique nos logs do Render se o pacote curl-cffi foi compilado com sucesso."
            }
        )
