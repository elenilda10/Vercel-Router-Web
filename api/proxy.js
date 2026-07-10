// File: api/proxy.js

export const config = {
  runtime: 'edge', // Tecnologia Edge para processar streams sem limite de tempo/tamanho
};

export default async function handler(request) {
  const url = new URL(request.url);
  const targetUrl = url.searchParams.get("url");

  if (!targetUrl) {
    return new Response(JSON.stringify({ error: "Falta o parâmetro URL" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const ytResponse = await fetch(targetUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
      },
    });

    if (!ytResponse.ok) {
      return new Response("Falha ao baixar do YouTube", { status: ytResponse.status });
    }

    // Proxy stream: entrega o áudio diretamente do YouTube para o Telegram
    return new Response(ytResponse.body, {
      status: 200,
      headers: {
        "Content-Type": "audio/mp4",
        "Content-Disposition": 'attachment; filename="musica.m4a"',
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, max-age=3600"
      },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: "Erro no Proxy", details: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
