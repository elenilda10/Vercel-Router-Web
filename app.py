# Ficheiro: app.py | Motor Próprio com Blindagem Anti-AWS (TV Downgraded + VR)

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
    return {
        "status": "online",
        "modo": "Anônimo Blindado (AWS/Render)",
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

    # 1. Limpeza rigorosa da URL para remover parâmetros de rastreamento do YouTube
    url_limpa = url.split("?si=")[0].split("&si=")[0].split("?is=")[0].strip()

    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    
    output_template = f"{pasta_tmp}/%(id)s.%(ext)s"

    # 2. Configuração do FFmpeg para converter e embutir a capa do álbum
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

    # 🛡️ A CHAVE DE PRATA PARA NUVEM AWS (RENDER):
    # Usamos 'tv_downgraded' (TV legada), 'android_vr' (Óculos VR) e 'web_music'.
    # Esses clientes ignoram a exigência de verificação em IPs de Data Center!
    # Nota importante: Removemos o 'player_skip' que acionava o Erro 152.
    ydl_opts['extractor_args'] = {
        'youtube': {
            'player_client': ['tv_downgraded', 'android_vr', 'web_music', 'tv_embedded'],
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_limpa, download=True)
            video_id = info.get('id')
            caminho_base = f"{pasta_tmp}/{video_id}"
            ficheiro_final = f"{caminho_base}.{formato}"

            if not os.path.exists(ficheiro_final):
                raise Exception("O ficheiro não foi gerado após o processamento.")

            background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)

            return FileResponse(
                path=ficheiro_final,
                filename=f"{info.get('title', 'Audio')}.{formato}",
                media_type=f"audio/{formato}"
            )

    except Exception as e1:
        erro_str = str(e1)
        
        # 🔄 FAILOVER DE EMERGÊNCIA (Caso a primeira lista falhe na Amazon):
        try:
            print(f"⚠️ Tentativa principal falhou. Ativando Failover iOS/Music...")
            ydl_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['ios', 'web_music', 'mweb'],
                }
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url_limpa, download=True)
                video_id = info.get('id')
                caminho_base = f"{pasta_tmp}/{video_id}"
                ficheiro_final = f"{caminho_base}.{formato}"

                if os.path.exists(ficheiro_final):
                    background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)
                    return FileResponse(
                        path=ficheiro_final,
                        filename=f"{info.get('title', 'Audio')}.{formato}",
                        media_type=f"audio/{formato}"
                    )
                else:
                    raise Exception("Falha no arquivo do Failover.")
        except Exception as e2:
            if 'caminho_base' in locals():
                limpar_ficheiros_temporarios(caminho_base)
                
            return JSONResponse(
                status_code=500,
                content={
                    "sucesso": False,
                    "erro_principal": erro_str,
                    "erro_secundario": str(e2),
                    "dica": "O YouTube bloqueou temporariamente a requisição deste IP. A configuração atual está otimizada para contornar bloqueios de Data Center sem cookies."
                }
            )
