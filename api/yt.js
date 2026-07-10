// File: api/yt.js | Status: Motor de Extração de YouTube para MP3

export const config = {
  runtime: 'edge', // Garante velocidade e sem limites de tempo na Vercel
};

export default async function handler(request) {
  const url = new URL(request.url);
  const targetUrl = url.searchParams.get("url");

  if (!targetUrl) {
    return new Response(JSON.stringify({ success: false, error: "URL não fornecida" }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  }

  try {
    // Usamos o motor público do Cobalt silenciosamente e de forma gratuita
    const req = await fetch("https://api.cobalt.tools/api/json", {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        url: targetUrl,
        isAudioOnly: true // Força a extração de áudio
      })
    });

    const data = await req.json();

    if (data.status === "error" || !data.url) {
      throw new Error("O motor não conseguiu extrair este link.");
    }

    // 💡 A MÁGICA: Devolvemos os dados no MESMO formato que a SocialKit usava!
    return new Response(JSON.stringify({
      success: true,
      data: {
        title: "Áudio do YouTube", // O Cobalt não envia título, então usamos um genérico
        downloadUrl: data.url
      }
    }), {
      status: 200,
      headers: { 
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });

  } catch (error) {
    return new Response(JSON.stringify({ success: false, error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}
