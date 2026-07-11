# Ficheiro: app.py | Motor Próprio Blindado (TLS Chrome + Cookies Ativos + Deno + Raio-X)

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob
import shutil
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

# Caminhos possíveis para o ficheiro de cookies: Secret File do Render (Docker)
# ou raiz do projeto (serviço nativo / fallback local)
CAMINHOS_COOKIES = ["/etc/secrets/cookies.txt", "cookies.txt"]


def localizar_cookies():
    """Retorna o primeiro caminho de cookies.txt que existir no servidor, ou None."""
    for caminho in CAMINHOS_COOKIES:
        if os.path.exists(caminho):
            return caminho
    return None


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

    # 2. Verifica se o runtime JS (Deno) está disponível no servidor
    # Exigido pelo yt-dlp desde a versão 2025.11.12 para resolver os
    # desafios de assinatura/token que o YouTube usa contra bots
    caminho_deno = shutil.which("deno")
    status_deno = (
        f"✅ Ativo ({caminho_deno})"
        if caminho_deno
        else "❌ NÃO ENCONTRADO (extração do YouTube fica degradada/instável)"
    )

    # 3. Verifica se o ficheiro cookies.txt está disponível (Secret File ou raiz)
    caminho_cookie = localizar_cookies()
    status_cookie = (
        f"✅ DETETADO E ATIVO! ({caminho_cookie})"
        if caminho_cookie
        else "⚠️ NÃO ENCONTRADO (A rodar em modo anónimo)"
    )

    return {
        "status": "online",
        "versao_deploy": "BLINDAGEM MÁXIMA 5.0 (Chrome TLS + Cookies + Deno)",
        "motor_tls_cffi": status_cffi,
        "motor_js_deno": status_deno,
        "ficheiro_cookies": status_cookie,
        "plataformas_clientes": "tv_embedded, android, ios, tv, web",
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
                # 'js' REMOVIDO: sem baixar o player.js, o Deno (Pilar 5)
                # não tem o que executar para resolver os desafios do YouTube.
                'player_skip': ['webpage', 'configs'],
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
    # Procura em /etc/secrets/cookies.txt (Secret File do Render) e na raiz do projeto
    caminho_cookies = localizar_cookies()
    if caminho_cookies:
        ydl_opts['cookiefile'] = caminho_cookies
        print(f"🍪 Ficheiro de cookies carregado de '{caminho_cookies}' para esta requisição!")

    # 🛡️ PILAR 5: RUNTIME JAVASCRIPT (DENO)
    # Exigido pelo yt-dlp desde 2025.11.12 para resolver os desafios de
    # assinatura (nsig) e token que o YouTube usa para bloquear bots.
    if shutil.which("deno"):
        ydl_opts['js_runtimes'] = {'deno': {}}
        print("⚙️ Runtime Deno detetado e ativado para esta requisição!")
    else:
        print("⚠️ Deno não encontrado no servidor — extração do YouTube pode falhar ou vir degradada.")

    try:
        print(f"⚡ Iniciando download blindado (Chrome TLS + Cookies + Deno) para: {url_limpa}...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_limpa, download=True)
            video_id = info.get('id')
            caminho_base = f"{pasta_tmp}/{video_id}"
            arquivo_mp3 = f"{caminho_base}.{formato}"

            if not os.path.exists(arquivo_mp3):
                raise Exception("O ficheiro não foi gerado após o processamento do FFmpeg.")

            print("🏆 SUCESSO! Barreira de IP rompida com sucesso via Cookies + TLS + Deno!")
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
                "dica_tecnica": "Se o erro persistir mesmo com cookies e Deno ativos, confira em '/' se motor_js_deno e ficheiro_cookies estão mesmo ativos no servidor. Se algum estiver ausente, o problema está no deploy (Dockerfile/Secret Files), não no código."
            }
        )
