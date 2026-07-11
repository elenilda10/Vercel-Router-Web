# Ficheiro: app.py | Motor Próprio de Download com Evasão de Data Center (Sem Cookies)

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
        "modo": "Evasão Anônima (Otimizado para Nuvem AWS/Render)",
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

    # 1. Limpeza rigorosa da URL para remover rastreadores (?si=, &list=, etc)
    url_limpa = url.split("?si=")[0].split("&si=")[0].split("?is=")[0].strip()

    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    
    output_template = f"{pasta_tmp}/%(id)s.%(ext)s"

    # 2. Configuração Base do FFmpeg para converter para MP3 e embutir a capa do álbum
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

    # 🛡️ ESTRATÉGIA DE EVASÃO PARA SERVIDORES EM NUVEM (SEM COOKIES):
    # Usamos 'tv_downgraded', 'android_vr' e 'web_music' porque o Google
    # não exige testes de IP de navegadores nesses clientes de TV e VR!
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

            # Agenda a faxina para apagar o arquivo logo após o envio
            background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)

            return FileResponse(
                path=ficheiro_final,
                filename=f"{info.get('title', 'Audio')}.{formato}",
                media_type=f"audio/{formato}"
            )

    except Exception as e1:
        erro_str = str(e1)
        
        # 🔄 FAILOVER DE EMERGÊNCIA (Plano B silencioso caso a primeira lista falhe):
        try:
            print("⚠️ Tentativa principal falhou. Ativando Failover iOS/Music...")
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
                    "dica": "O YouTube rejeitou a requisição do IP da Amazon. A configuração atual está otimizada para evasão anônima de Data Center."
                }
            )
