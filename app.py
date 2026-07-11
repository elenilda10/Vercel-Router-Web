# Ficheiro: app.py | Motor Próprio de Download com Autenticação e Diagnóstico

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob

app = FastAPI(title="Krust Audio API")

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
    caminho = os.path.abspath("cookies.txt")
    has_cookie = os.path.exists(caminho)
    return {
        "status": "online",
        "cookie_ativo": has_cookie,
        "caminho_cookie": caminho if has_cookie else "Não encontrado",
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

    # Limpeza preventiva de parâmetros de rastreamento na URL (que causam bloqueio)
    url_limpa = url.split("?si=")[0].split("&si=")[0].strip()

    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    
    output_template = f"{pasta_tmp}/%(id)s.%(ext)s"
    
    # Busca o caminho absoluto do arquivo no servidor Linux
    caminho_cookie = os.path.abspath("cookies.txt")
    usar_cookies = os.path.exists(caminho_cookie)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': formato,
                'preferredquality': '192',
            },
            {
                'key': 'FFmpegMetadata',
            },
            {
                'key': 'EmbedThumbnail',
            }
        ],
    }

    # 🛡️ ESTRATÉGIA ANTI-BOT AVANÇADA:
    if usar_cookies:
        # Se temos o cookie, forçamos a leitura e usamos os clientes de Web/Mobile Web
        ydl_opts['cookiefile'] = caminho_cookie
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['web', 'mweb', 'tv'],
            }
        }
    else:
        # Sem cookie, tentamos usar os clientes de Music, iOS e VR para evitar o PO Token da AWS
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android_vr', 'web_music', 'tv_embedded', 'mweb'],
                'player_skip': ['webpage', 'configs', 'js'],
            }
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_limpa, download=True)
            video_id = info.get('id')
            caminho_base = f"{pasta_tmp}/{video_id}"
            
            ficheiro_final = f"{caminho_base}.{formato}"

            if not os.path.exists(ficheiro_final):
                raise Exception("O ficheiro não foi gerado após o processamento do FFmpeg.")

            background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)

            return FileResponse(
                path=ficheiro_final,
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
                "cookie_detectado_no_servidor": usar_cookies,
                "erro": f"Falha na manipulação do áudio: {str(e)}"
            }
        )
