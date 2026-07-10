// File: api/ig.js | Status: Extrator de Instagram compatível com ig_success

export const config = {
  runtime: 'edge', // Máxima velocidade e sem limite de tempo
};

export default async function handler(request) {
  const url = new URL(request.url);
  const targetUrl = url.searchParams.get("url");

  if (!targetUrl) {
    return new Response(JSON.stringify({ success: false, error: "URL do Instagram não fornecida" }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  }

  // Limpa parâmetros de rastreamento do Insta (?igsh=...)
  const cleanUrl = targetUrl.split("?")[0];
  const encodedUrl = encodeURIComponent(cleanUrl);

  // Lista de APIs Comunitárias Bot-Friendly para Instagram
  const apis = [
    {
      url: `https://api.vreden.my.id/api/igdownload?url=${encodedUrl}`,
      parse: (data) => {
        let list = data?.result?.data || [];
        return list.map(item => ({
          type: item.url.includes(".mp4") || item.type === "video" ? "video" : "photo",
          url: item.url,
          thumbnail: item.thumbnail || "https://i.imgur.com/1Dq56qS.png"
        }));
      }
    },
    {
      url: `https://api.siputzx.my.id/api/d/igdl?url=${encodedUrl}`,
      parse: (data) => {
        let list = data?.data || [];
        return list.map(item => ({
          type: item.url.includes(".mp4") || item.type === "video" ? "video" : "photo",
          url: item.url,
          thumbnail: item.thumbnail || "https://i.imgur.com/1Dq56qS.png"
        }));
      }
    }
  ];

  let errorLogs = [];

  for (const api of apis) {
    try {
      const req = await fetch(api.url, {
        headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" }
      });

      if (!req.ok) {
        errorLogs.push(`${api.url.split('?')[0]} falhou (${req.status})`);
        continue;
      }

      const data = await req.json();
      const sources = api.parse(data);

      if (sources && sources.length > 0) {
        // 💡 Devolve EXATAMENTE no formato que o seu comando ig_success do bot precisa!
        return new Response(JSON.stringify({
          success: true,
          data: {
            caption: data?.result?.caption || data?.data?.[0]?.caption || "📸 Reel do Instagram",
            source: sources
          }
        }), {
          status: 200,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
        });
      }
    } catch (e) {
      errorLogs.push(`Erro: ${e.message}`);
    }
  }

  return new Response(JSON.stringify({ success: false, error: "Falha em todas as APIs de Instagram", logs: errorLogs }), {
    status: 500,
    headers: { "Content-Type": "application/json" }
  });
}
