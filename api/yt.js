export const config = {
  runtime: 'edge', // Mantém a velocidade extrema da Vercel
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

  // 1. Limpa parâmetros de rastreamento do YouTube que causam bloqueios (&si=)
  const cleanUrl = targetUrl.split("&si=")[0].split("?si=")[0];

  // 2. Payload Híbrido: Prepara os dados para serem compatíveis com versões antigas e novas da API
  const cobaltBody = {
    url: cleanUrl,
    downloadMode: "audio", // Parâmetro novo
    audioFormat: "mp3",    // Parâmetro novo
    isAudioOnly: true,     // Parâmetro antigo
    aFormat: "mp3"         // Parâmetro antigo
  };

  // 3. A MÁGICA: Lista de servidores comunitários (Mirrors) que não bloqueiam a Vercel
  const apis = [
    "https://api.cobalt.best/",
    "https://api.cobalt.best/api/json",
    "https://cobalt-api.kwiatekmiki.com/",
    "https://cobalt-api.kwiatekmiki.com/api/json",
    "https://api.cobalt.tools/", // Oficial como último recurso
    "https://api.cobalt.tools/api/json"
  ];

  let errorLogs = [];

  // 4. Inicia a caçada: Testa servidor por servidor de forma hiper-rápida
  for (const apiUrl of apis) {
    try {
      const origin = new URL(apiUrl).origin;
      const req = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json",
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
          "Origin": origin,
          "Referer": origin + "/"
        },
        body: JSON.stringify(cobaltBody)
      });

      if (!req.ok) {
        errorLogs.push(`${apiUrl} falhou (Status ${req.status})`);
        continue; // Passa para o próximo servidor da lista
      }

      const data = await req.json();

      // Se achou o link final, converte para o formato que o seu bot já sabe ler!
      if (data && (data.url || data.stream)) {
        return new Response(JSON.stringify({
          success: true,
          data: {
            title: "Áudio do YouTube",
            downloadUrl: data.url || data.stream
          }
        }), {
          status: 200,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
        });
      } else {
        errorLogs.push(`${apiUrl} não enviou o link.`);
      }
    } catch (e) {
      errorLogs.push(`${apiUrl} deu erro: ${e.message}`);
    }
  }

  // Se TODOS os servidores falharem, envia um log detalhado para podermos investigar
  return new Response(JSON.stringify({ 
    success: false, 
    error: "Todos os servidores de extração falharam.",
    logs: errorLogs
  }), {
    status: 500,
    headers: { "Content-Type": "application/json" }
  });
}
