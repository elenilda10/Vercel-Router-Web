# Ficheiro: app.py | Motor Próprio com TLS Chrome + Raio-X Anti-Silêncio

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob
import traceback

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
    try:
        import curl_cffi
        status_cffi = f"✅ Instalado perfeitamente (Versão {curl_cffi.__version__})"
    except ImportError as err:
        status_cffi = f"❌ NÃO INSTALADO. Motivo real: {repr(err)}"

    return {
        "status": "online",
        "versao_deploy": "RAIO-X ATIVO 2.0 (Se vir isto, o Render atualizou!)",
        "motor_tls_cffi": status_cffi,
        "blindagem": "TLS Fingerprinting (impersonate: chrome)",
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

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writethumbnail': True,
        'impersonate': 'chrome',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'android', 'ios', 'tv', 'web'],
                'player_skip': ['webpage', 'configs', 'js'],
            }
        },
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
            info = ydl.extract_info(url_limpa, download=True)
            video_id = info.get('id')
            caminho_base = f"{pasta_tmp}/{video_id}"
            arquivo_mp3 = f"{caminho_base}.{formato}"

            if not os.path.exists(arquivo_mp3):
                raise Exception("O ficheiro não foi gerado após o processamento do FFmpeg.")

            print("🏆 SUCESSO! A barreira da AWS foi rompida com sucesso!")
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
        
        # O USO DO REPR(E) OBRIGA O PYTHON A ESCREVER O NOME DA CLASSE DO ERRO!
        return JSONResponse(
            status_code=500,
            content={
                "sucesso": False,
                "nome_exato_do_erro": repr(e), 
                "resumo_do_erro": str(e),
                "raio_x_detalhado": erro_completo.split("\n")[-6:], 
                "dica_tecnica": "A chave nome_exato_do_erro acima mostra a causa raiz sem ficar em branco."
            }
        )
