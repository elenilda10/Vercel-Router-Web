# Ficheiro: app.py | Motor Próprio Blindado (TLS Chrome + Cookies Ativos + Raio-X)

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob
import traceback

# 🛡️ IMPORTAÇÃO OFICIAL PARA CAMUFLAGEM TLS:
# Evita o AssertionError transformando a string 'chrome' no objeto correto do yt-dlp
from yt_dlp.networking.impersonate import ImpersonateTarget

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
    # 1. Verifica se a biblioteca de camuflagem CFFI está ativa
    try:
        import curl_cffi
        status_cffi = f"✅ Ativo (Versão {curl_cffi.__version__})"
    except ImportError as err:
        status_cffi = f"❌ NÃO INSTALADO. Motivo: {repr(err)}"

    # 2. Verifica se você enviou o ficheiro cookies.txt para o GitHub
    caminho_cookie = os.path.abspath("cookies.txt")
    status_cookie = "✅ DETETADO E ATIVO! (O YouTube verá uma conta autenticada)" if os.path.exists(caminho_cookie) else "⚠️ NÃO ENCONTRADO (A rodar em modo anónimo)"

    return {
        "status": "online",
        "versao_deploy": "BLINDAGEM MÁXIMA 4.0 (Chrome TLS + Cookies)",
        "motor_tls_cffi": status_cffi,
        "ficheiro_cookies": status_cookie,
        "plataformas_clientes": "tv_embedded, android, ios, web",
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

    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    output_template = f"{pasta_tmp}/%(id)s.%(ext)s"

    # Configuração Base do Extrator
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writethumbnail': True,
        
        # 🛡️ PILAR 1: Camuflagem de Navegador (Impersonate Chrome)
        'impersonate': ImpersonateTarget.from_str('chrome'),
        
        # 🛡️ PILAR 2: Sistema de Clientes Múltiplos (Fallback inteligente)
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'android', 'ios', 'tv', 'web'],
                'player_skip': ['webpage', 'configs', 'js'],
            }
        },
        
        # 🛡️ PILAR 3: Conversão FFmpeg para MP3 a 192kbps com Capa do Vídeo
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

    # 🛡️ PILAR 4: INJEÇÃO AUTOMÁTICA DE COOKIES
    # Se o ficheiro cookies.txt estiver no servidor, nós entregamos ao yt-dlp!
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"
        print("🍪 Ficheiro de cookies carregado para esta requisição!")

    try:
        print(f"⚡ Iniciando download blindado (Chrome TLS + Cookies) para: {url_limpa}...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_limpa, download=True)
            video_id = info.get('id')
            caminho_base = f"{pasta_tmp}/{video_id}"
            arquivo_mp3 = f"{caminho_base}.{formato}"

            if not os.path.exists(arquivo_mp3):
                raise Exception("O ficheiro não foi gerado após o processamento do FFmpeg.")

            print("🏆 SUCESSO! Barreira de IP da Amazon rompida com sucesso via Cookies + TLS!")
            background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)

            return FileResponse(
                path=arquivo_mp3,
                filename=f"{info.get('title', 'Audio')}.{formato}",
                media_type=f"audio/{formato}"
            )

    except Exception as e:
        if 'caminho_base' in locals():
            limpar_ficheiros_temporarios(caminho_base)
            
        erro_completo = traceback.format_exc()
        print(f"❌ Falha capturada no terminal:\n{erro_completo}")
        
        # O Raio-X que nos salvou no passo anterior!
        return JSONResponse(
            status_code=500,
            content={
                "sucesso": False,
                "nome_exato_do_erro": repr(e), 
                "resumo_do_erro": str(e),
                "raio_x_detalhado": erro_completo.split("\n")[-6:], 
                "dica_tecnica": "Se o erro persistir mesmo com cookies, significa que essa conta secundária precisa de assistir a 1 ou 2 vídeos no navegador antes de exportar o cookie para validar a sessão."
            }
        )
