# Ficheiro: app.py | Motor Próprio com Roteamento Proxy Automático (Anti-AWS)

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob
import urllib.request

app = FastAPI(title="Krust Audio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💡 OPÇÃO VIP: Se um dia você criar uma conta gratuita em sites como Webshare.io 
# (que dá 10 proxies residenciais grátis), você pode colar seu proxy aqui abaixo 
# para ter 10x mais velocidade sem precisar caçar na internet!
# Exemplo: PROXY_FIXO = "http://usuario:senha@ip:porta"
PROXY_FIXO = ""

def limpar_ficheiros_temporarios(caminho_base: str):
    try:
        ficheiros = glob.glob(f"{caminho_base}*")
        for f in ficheiros:
            if os.path.exists(f):
                os.remove(f)
                print(f"🗑️ Faxina: Ficheiro {f} removido com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao limpar ficheiros temporários: {str(e)}")

# 🌐 CAÇADOR DE PROXIES: Busca IPs anônimos em tempo real caso a Amazon seja bloqueada
def buscar_proxies_gratuitos():
    if PROXY_FIXO:
        return [PROXY_FIXO]
    try:
        print("🌐 A buscar lista de proxies anônimos frescos na internet...")
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=yes&anonymity=elite"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as response:
            lista = response.read().decode('utf-8').strip().split('\n')
            proxies = [f"http://{p.strip()}" for p in lista if p.strip()]
            print(f"✅ {len(proxies)} proxies encontrados! Selecionando os 5 melhores...")
            return proxies[:5]
    except Exception as e:
        print(f"⚠️ Falha ao buscar proxies gratuitos: {e}")
        return []

@app.get("/")
def home():
    return {
        "status": "online",
        "motor": "Caçador de Proxies Ativo (Otimizado para contornar AWS/Render)",
        "proxy_fixo_configurado": bool(PROXY_FIXO),
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

    # 🚀 TENTATIVA 1: Conexão Direta (Sem proxy, velocidade máxima da Amazon)
    try:
        print("⚡ Tentando download direto...")
        with yt_dlp.YoutubeDL(ydl_opts_base) as ydl:
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
    except Exception as e1:
        print(f"⚠️ Conexão direta bloqueada pela AWS ({str(e1)[:60]}...). Ativando Roteamento Proxy!")

    # 🛡️ TENTATIVA 2: O Motor de Roteamento via Proxy
    proxies = buscar_proxies_gratuitos()
    erros_proxy = []

    for idx, proxy_url in enumerate(proxies, 1):
        try:
            print(f"🔄 [Proxy {idx}/{len(proxies)}] Tentando camuflar conexão via: {proxy_url}...")
            ydl_opts_proxy = ydl_opts_base.copy()
            ydl_opts_proxy['proxy'] = proxy_url
            
            with yt_dlp.YoutubeDL(ydl_opts_proxy) as ydl:
                info = ydl.extract_info(url_limpa, download=True)
                video_id = info.get('id')
                caminho_base = f"{pasta_tmp}/{video_id}"
                ficheiro_final = f"{caminho_base}.{formato}"

                if os.path.exists(ficheiro_final):
                    print(f"🏆 SUCESSO! Áudio baixado perfeitamente através do proxy {proxy_url}")
                    background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)
                    return FileResponse(
                        path=ficheiro_final,
                        filename=f"{info.get('title', 'Audio')}.{formato}",
                        media_type=f"audio/{formato}"
                    )
        except Exception as ep:
            print(f"❌ Proxy {proxy_url} falhou ou é lento demais. Saltando para o próximo...")
            erros_proxy.append(f"Proxy {idx} falhou: {str(ep)[:40]}")
            continue

    # Se todos os proxies falharem no momento da caçada:
    return JSONResponse(
        status_code=500,
        content={
            "sucesso": False,
            "erro": "O IP da Amazon foi bloqueado e os proxies públicos gratuitos testados estavam lentos ou offline no momento.",
            "solucao_pro": "Para 100% de estabilidade e velocidade sem gastar nada, crie uma conta grátis em sites como Webshare.io (dá 10 proxies grátis permanentes) e cole o link na variável PROXY_FIXO no topo do arquivo app.py!",
            "historico_tentativas": erros_proxy
        }
    )
