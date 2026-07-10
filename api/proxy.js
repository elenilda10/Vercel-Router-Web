export const config = {
  runtime: "edge",
};

const API_BASE = "https://go-api-six.vercel.app";

export default async function handler(request) {
  const { searchParams } = new URL(request.url);
  const youtubeUrl = searchParams.get("url");

  if (!youtubeUrl) {
    return new Response(
      JSON.stringify({ error: "Falta o parâmetro url" }),
      {
        status: 400,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  }

  try {
    // Busca as informações do vídeo
    const apiResponse = await fetch(
      `${API_BASE}/youtube/stream?url=${encodeURIComponent(youtubeUrl)}`,
      {
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36",
          Accept: "application/json",
        },
      }
    );

    if (!apiResponse.ok) {
      return new Response(
        JSON.stringify({
          error: "Erro ao consultar API",
          status: apiResponse.status,
        }),
        {
          status: apiResponse.status,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
    }

    const data = await apiResponse.json();

    if (!Array.isArray(data.adaptiveFormats)) {
      return new Response(
        JSON.stringify({
          error: "adaptiveFormats não encontrado",
        }),
        {
          status: 500,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
    }

    const formats = data.adaptiveFormats;

    // Prioridade:
    // 140 = M4A
    // 251 = Opus 160 kbps
    // 250 = Opus 70 kbps
    // 249 = Opus 50 kbps

    let audio =
      formats.find(f => f.itag === 140) ||
      formats.find(f => f.itag === 251) ||
      formats.find(f => f.itag === 250) ||
      formats.find(f => f.itag === 249);

    // Caso nenhum desses exista, pega o maior bitrate de áudio
    if (!audio) {
      audio = formats
        .filter(f => f.mimeType?.startsWith("audio/"))
        .sort((a, b) => (b.bitrate || 0) - (a.bitrate || 0))[0];
    }

    if (!audio?.url) {
      return new Response(
        JSON.stringify({
          error: "Nenhum formato de áudio encontrado",
        }),
        {
          status: 404,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
    }

    // Faz o proxy do áudio
    const stream = await fetch(audio.url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36",
      },
    });

    if (!stream.ok) {
      return new Response("Falha ao baixar o áudio", {
        status: stream.status,
      });
    }

    return new Response(stream.body, {
      status: 200,
      headers: {
        "Content-Type":
          stream.headers.get("content-type") ||
          audio.mimeType?.split(";")[0] ||
          "audio/mp4",
        "Content-Length":
          stream.headers.get("content-length") || "",
        "Content-Disposition":
          audio.itag === 140
            ? 'attachment; filename="audio.m4a"'
            : 'attachment; filename="audio.webm"',
        "Cache-Control": "public, max-age=3600",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: "Erro interno",
        details: err.message,
      }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  }
}
