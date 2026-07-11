# Ficheiro: app.py | Motor Próprio com Roteamento por Espelhos Invidious (Anti-AWS)

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob
import re

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

# Extrai o ID único do vídeo (ex: dQw4w9WgXcQ) a partir de qualquer link do YouTube
def extrair_id_video(url: str):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

@app.get("/")
def home():
    return {
        "status": "online",
        "motor": "Roteamento Descentralizado via Espelhos Invidious (Anti-AWS)",
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

    url_limpa = url.split("?si=")[0].split("&si=")[0].split("?is=")[0].strip()
    video_id = extrair_id_video(url_limpa)

    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    output_template = f"{pasta_tmp}/%(id)s.%(ext)s"

    ydl_opts_base = {
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
            {'key': 'FFmpegMetadata'},
            {'key': 'EmbedThumbnail'}
        ],
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_downgraded', 'android_vr', 'web_music', 'tv_embedded'],
            }
        }
    }

    # 🚀 TENTATIVA 1: Conexão Direta
    try:
        print("⚡ Tentando conexão direta com o YouTube...")
        with yt_dlp.YoutubeDL(ydl_opts_base) as ydl:
            info = ydl.extract_info(url_limpa, download=True)
            id_real = info.get('id', video_id)
            caminho_base = f"{pasta_tmp}/{id_real}"
            ficheiro_final = f"{caminho_base}.{formato}"

            if os.path.exists(ficheiro_final):
                background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)
                return FileResponse(
                    path=ficheiro_final,
                    filename=f"{info.get('title', 'Audio')}.{formato}",
                    media_type=f"audio/{formato}"
                )
    except Exception as e1:
        print(f"⚠️ AWS Bloqueada direto. Ativando Roteamento por Espelhos Invidious...")

    # 🪞 TENTATIVA 2: O Motor de Espelhos (Dribla 100% do bloqueio de IP da Amazon!)
    if not video_id:
        return JSONResponse(status_code=400, content={"sucesso": False, "erro": "ID do vídeo não identificado."})

    # Lista de servidores espelhos estáveis na Europa (Não rodam na AWS)
    espelhos = [
        f"https://yewtu.be/watch?v={video_id}",
        f"https://inv.tux.pizza/watch?v={video_id}",
        f"https://invidious.nerdvpn.de/watch?v={video_id}",
        f"https://invidious.flokinet.to/watch?v={video_id}"
    ]

    erros_espelho = []

    for idx, link_espelho in enumerate(espelhos, 1):
        try:
            print(f"🔄 [Espelho {idx}/{len(espelhos)}] Baixando via servidor descentralizado: {link_espelho}...")
            # Removemos restrições de cliente específicas do YouTube pois o Invidious entrega direto
            ydl_opts_espelho = ydl_opts_base.copy()
            if 'extractor_args' in ydl_opts_espelho:
                del ydl_opts_espelho['extractor_args']

            with yt_dlp.YoutubeDL(ydl_opts_espelho) as ydl:
                info = ydl.extract_info(link_espelho, download=True)
                caminho_base = f"{pasta_tmp}/{video_id}"
                ficheiro_final = f"{caminho_base}.{formato}"

                if os.path.exists(ficheiro_final):
                    print(f"🏆 SUCESSO! Áudio extraído perfeitamente do espelho {link_espelho}")
                    background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)
                    return FileResponse(
                        path=ficheiro_final,
                        filename=f"{info.get('title', 'Audio')}.{formato}",
                        media_type=f"audio/{formato}"
                    )
        except Exception as ee:
            print(f"❌ Espelho {idx} falhou. Tentando o próximo...")
            erros_espelho.append(f"Espelho {idx}: {str(ee)[:40]}")
            continue

    return JSONResponse(
        status_code=500,
        content={
            "sucesso": False,
            "erro": "Falha em todos os espelhos de roteamento.",
            "detalhes": erros_espelho
        }
    )
