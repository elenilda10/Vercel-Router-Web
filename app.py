# Ficheiro: app.py | Motor Próprio Conectado à API Vercel + FFmpeg MP3

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob
import urllib.request
import urllib.parse
import json

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

# 🌐 CONSULTA A SUA API DA VERCEL: Extrai o link direto do melhor áudio no JSON
def consultar_sua_api_vercel(url_youtube: str):
    try:
        # Codifica a URL corretamente para não quebrar na Vercel
        url_codificada = urllib.parse.quote(url_youtube, safe='')
        url_api = f"https://go-api-six.vercel.app/youtube/stream?url={url_codificada}"
        
        print(f"🔍 Consultando a sua API Vercel: {url_api}...")
        req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            
            titulo = dados.get('title', 'Audio Vercel').replace("/", "_").replace("\\", "_")
            
            # Pega a melhor imagem de capa disponível no JSON
            capa_url = ""
            if 'thumbnail' in dados and len(dados['thumbnail']) > 0:
                capa_url = dados['thumbnail'][-1].get('url', '')
                
            # Procura o melhor áudio dentro de "adaptiveFormats" (exatamente onde estava no seu log!)
            melhor_audio_url = None
            maior_bitrate = 0
            
            if 'adaptiveFormats' in dados:
                for fmt in dados['adaptiveFormats']:
                    mime = fmt.get('mimeType', '')
                    # Filtra apenas os streams de áudio (opus ou mp4a)
                    if 'audio' in mime:
                        bitrate = fmt.get('bitrate', 0)
                        if bitrate > maior_bitrate:
                            maior_bitrate = bitrate
                            melhor_audio_url = fmt.get('url')
                            
            if melhor_audio_url:
                print(f"✅ Áudio de alta qualidade ({maior_bitrate} bps) encontrado na sua API!")
                return {"url": melhor_audio_url, "titulo": titulo, "capa": capa_url}
            else:
                print("⚠️ Nenhum stream de áudio encontrado dentro de adaptiveFormats.")
                return None
                
    except Exception as e:
        print(f"❌ Erro ao ler a API da Vercel: {str(e)}")
        return None

@app.get("/")
def home():
    return {
        "status": "online",
        "motor": "Integrado com go-api-six.vercel.app + FFmpeg MP3 Engine",
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

    # Limpa a URL do YouTube (remove parâmetros lixo como ?is=... ou &si=...)
    url_limpa = url.split("?si=")[0].split("&si=")[0].split("?is=")[0].strip()
    
    # 1. Chama a sua API da Vercel para pegar os dados limpos
    dados_vercel = consultar_sua_api_vercel(url_limpa)
    
    if not dados_vercel:
        return JSONResponse(
            status_code=500,
            content={
                "sucesso": False,
                "erro": "A API go-api-six.vercel.app não conseguiu retornar o stream de áudio para este link."
            }
        )

    pasta_tmp = "/tmp/downloads"
    os.makedirs(pasta_tmp, exist_ok=True)
    
    # Criamos um ID temporário seguro baseado no nome do arquivo
    id_seguro = str(abs(hash(dados_vercel['url'])))[:10]
    caminho_base = f"{pasta_tmp}/{id_seguro}"
    output_template = f"{caminho_base}.%(ext)s"

    # 2. Configura o FFmpeg no Render para converter o stream bruto em MP3 com Capa
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': formato,
                'preferredquality': '192', # Qualidade do MP3
            }
        ]
    }

    try:
        print("🔄 Baixando o áudio da Vercel e convertendo para MP3 no FFmpeg...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Mandamos o yt-dlp baixar DIRETAMENTE o link bruto do áudio que a Vercel entregou!
            ydl.download([dados_vercel['url']])
            
            ficheiro_final = f"{caminho_base}.{formato}"

            if os.path.exists(ficheiro_final):
                print("🏆 SUCESSO! MP3 gerado com perfeição a partir dos dados da Vercel!")
                background_tasks.add_task(limpar_ficheiros_temporarios, caminho_base)
                
                return FileResponse(
                    path=ficheiro_final,
                    filename=f"{dados_vercel['titulo']}.{formato}",
                    media_type=f"audio/{formato}"
                )
            else:
                raise Exception("O FFmpeg não conseguiu gerar o arquivo MP3 final.")
                
    except Exception as e:
        if 'caminho_base' in locals():
            limpar_ficheiros_temporarios(caminho_base)
            
        return JSONResponse(
            status_code=500,
            content={
                "sucesso": False,
                "erro_ffmpeg": str(e),
                "api_vercel_respondeu": True
            }
        )
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
