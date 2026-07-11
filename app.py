# Ficheiro: app.py | Motor Próprio de Download e Manipulação com FFmpeg

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob

app = FastAPI(title="Krust Audio API")

# Permite que o Telegram ou qualquer painel aceda à API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧹 FUNÇÃO DE FAXINA: Apaga todos os ficheiros temporários após o envio
def limpar_ficheiros_temporarios(caminho_base: str):
    try:
        # Procura qualquer ficheiro gerado com aquele ID (.mp3, .jpg, .webm, etc.) e apaga
        ficheiros = glob.glob(f"{caminho_base}*")
        for f in ficheiros:
            if os.path.exists(f):
                os.remove(f)
                print(f"🗑️ Faxina: Ficheiro {f} removido com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao limpar ficheiros temporários: {str(e)}")

@app.get("/")
def home():
    has_cookie = os.path.exists("cookies.txt")
    return {
        "status": "online",
        "cookie_ativo": has_cookie,
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

    # Cria um diretório temporário no Linux para processar os ficheiros
    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    
    output_template = f"{pasta_tmp}/%(id)s.%(ext)s"
    caminho_cookie = "cookies.txt"
    usar_cookies = os.path.exists(caminho_cookie)

    # 🛠️ CONFIGURAÇÃO DO YT-DLP COM FFMPEG:
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writethumbnail': True, # Obrigatório: Baixa a imagem de capa do vídeo
        
        # Pós-processamento para converter e embutir metadados e imagem:
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': formato,
                'preferredquality': '192', # Qualidade em kbps (192 é excelente e leve)
            },
            {
                'key': 'FFmpegMetadata', # Adiciona o Título, Artista e Álbum nas tags ID3
            },
            {
                'key': 'EmbedThumbnail', # Embebe a foto do vídeo dentro do ficheiro MP3
            }
        ],
    }

    # Sistema de evasão anti-bot adaptativo
    if usar_cookies:
        ydl_opts['cookiefile'] = caminho_cookie
        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['web', 'mweb', 'tv']}}
    else:
        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['tv_embedded', 'mweb', 'tv']}}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Faz o download real para o servidor e processa no FFmpeg
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            caminho_base = f"{pasta_tmp}/{video_id}"
            
            # O ficheiro final manipulado terá a extensão do formato escolhido
            ficheiro_final = f"{caminho_base}.{formato}"

            if not os.path.exists(ficheiro_final):
                raise Exception("O ficheiro não foi gerado após o processamento do FFmpeg.")

            # 💡 AGENDA A FAXINA: O ficheiro só será apagado DEPOIS de ser enviado ao utilizador!
            background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)

            # Devolve o próprio ficheiro MP3 manipulado com a capa pronta!
            return FileResponse(
                path=ficheiro_final,
                filename=f"{info.get('title', 'Audio')}.{formato}",
                media_type=f"audio/{formato}"
            )

    except Exception as e:
        # Se ocorrer um erro durante o download, limpa os restos do disco
        if 'caminho_base' in locals():
            limpar_ficheiros_temporarios(caminho_base)
            
        return JSONResponse(
            status_code=500,
            content={"sucesso": False, "erro": f"Falha na manipulação do áudio: {str(e)}"}
        )
