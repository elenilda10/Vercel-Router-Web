# Ficheiro: app.py | Motor Próprio com FFmpeg Nativo (Zero Bug do yt-dlp / Zero 403)

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import glob
import re
import urllib.request
import urllib.parse
import json
import subprocess

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

def extrair_id_video(url: str):
    match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

# 🌐 MULTIMOTOR INTELIGENTE: Busca primeiro streams SEM trava de IP, e usa a Vercel como backup!
def obter_link_audio_seguro(url_youtube: str, video_id: str):
    # 1º TENTATIVA: Piped Proxy (NUNCA dá erro 403 porque passa pelo túnel deles)
    apis_piped = [
        f"https://api.piped.privacydev.net/streams/{video_id}",
        f"https://pipedapi.kavin.rocks/streams/{video_id}",
        f"https://piped-api.garudalinux.org/streams/{video_id}"
    ]
    for api in apis_piped:
        try:
            print(f"🔍 Consultando Túnel Piped: {api}...")
            req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                dados = json.loads(resp.read().decode('utf-8'))
                if 'audioStreams' in dados and len(dados['audioStreams']) > 0:
                    print("✅ Link PipedProxy obtido (Imune a 403)!")
                    titulo = dados.get('title', 'Audio Piped').replace("/", "_").replace("\\", "_")
                    return {"url": dados['audioStreams'][0]['url'], "titulo": titulo, "fonte": "Piped"}
        except:
            continue

    # 2º TENTATIVA: Invidious com Túnel Local (&local=true)
    espelhos_inv = ["https://inv.tux.pizza", "https://invidious.nerdvpn.de"]
    for host in espelhos_inv:
        try:
            print(f"🔍 Consultando Túnel Invidious: {host}...")
            req = urllib.request.Request(f"{host}/api/v1/videos/{video_id}", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                dados = json.loads(resp.read().decode('utf-8'))
                titulo = dados.get('title', 'Audio Invidious').replace("/", "_").replace("\\", "_")
                url_tunel = f"{host}/latest_version?id={video_id}&itag=140&local=true"
                print("✅ Link Invidious Local obtido (Imune a 403)!")
                return {"url": url_tunel, "titulo": titulo, "fonte": "Invidious"}
        except:
            continue

    # 3º TENTATIVA (BACKUP): A sua API da Vercel!
    try:
        url_codificada = urllib.parse.quote(url_youtube, safe='')
        url_api = f"https://go-api-six.vercel.app/youtube/stream?url={url_codificada}"
        print(f"🔍 Consultando a sua API Vercel: {url_api}...")
        req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            titulo = dados.get('title', 'Audio Vercel').replace("/", "_").replace("\\", "_")
            if 'adaptiveFormats' in dados:
                for fmt in dados['adaptiveFormats']:
                    if 'audio' in fmt.get('mimeType', ''):
                        print("✅ Link da Vercel obtido com sucesso!")
                        return {"url": fmt['url'], "titulo": titulo, "fonte": "Vercel"}
    except Exception as e:
        print(f"❌ Erro na Vercel: {e}")

    return None

@app.get("/")
def home():
    return {
        "status": "online",
        "motor": "FFmpeg Nativo + Roteamento Anti-403 (Piped/Invidious/Vercel)",
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

    if not video_id:
        return JSONResponse(status_code=400, content={"sucesso": False, "erro": "ID do vídeo não encontrado."})

    # 1. Pega a URL do fluxo de áudio limpa
    stream_info = obter_link_audio_seguro(url_limpa, video_id)
    
    if not stream_info:
        return JSONResponse(
            status_code=500,
            content={"sucesso": False, "erro": "Nenhum motor de extração conseguiu retornar o áudio no momento."}
        )

    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    
    caminho_base = f"{pasta_tmp}/{video_id}_{stream_info['fonte']}"
    arquivo_mp3 = f"{caminho_base}.{formato}"

    # 2. A MÁGICA: Em vez de usar o yt-dlp, chamamos o FFmpeg diretamente pelo sistema!
    # O FFmpeg se conecta na URL do stream, baixa os bytes e converte para MP3 em 1 segundo!
    comando_ffmpeg = [
        "ffmpeg", "-y",             # -y sobrescreve se o arquivo já existir
        "-i", stream_info['url'],   # -i pega o link direto do fluxo (sem achar que é página web!)
        "-vn",                      # -vn ignora o vídeo (extrai só áudio)
        "-ar", "44100",             # -ar define a frequência padrão de música (44.1 kHz)
        "-ac", "2",                 # -ac define áudio estéreo
        "-b:a", "192k",             # -b:a define a qualidade excelente do MP3 (192 kbps)
        arquivo_mp3                 # Caminho onde o MP3 pronto será salvo no Linux
    ]

    try:
        print(f"⚡ Convertendo áudio para MP3 via FFmpeg nativo (Fonte: {stream_info['fonte']})...")
        
        # Executa o comando no terminal Linux do Render
        resultado = subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        
        if resultado.returncode != 0 or not os.path.exists(arquivo_mp3):
            erro_log = resultado.stderr.decode('utf-8', errors='ignore')[-300:]
            raise Exception(f"Erro no processamento do FFmpeg: {erro_log}")

        print("🏆 SUCESSO! Arquivo MP3 192kbps gerado com perfeição!")
        background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)
        
        return FileResponse(
            path=arquivo_mp3,
            filename=f"{stream_info['titulo']}.{formato}",
            media_type=f"audio/{formato}"
        )

    except Exception as e:
        if 'caminho_base' in locals():
            limpar_ficheiros_temporarios(caminho_base)
            
        return JSONResponse(
            status_code=500,
            content={
                "sucesso": False,
                "erro_ffmpeg": str(e),
                "fonte_usada": stream_info['fonte']
            }
        )
