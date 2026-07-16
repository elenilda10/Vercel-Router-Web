/* File: api/transcribe.ts | Fixed: Native Vercel JSON response helpers to prevent empty flushes */
import type { VercelRequest, VercelResponse } from "@vercel/node";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    if (req.method !== "POST") {
      return res.status(200).json({ ok: false, error: "Método não permitido. Use POST." });
    }

    const { fileUrl, apiKey } = req.body;

    if (!fileUrl || !apiKey) {
      return res.status(200).json({ ok: false, error: "Faltando parâmetros 'fileUrl' ou 'apiKey'." });
    }

    // 1. Baixa o arquivo de áudio temporariamente do Telegram
    const fileRes = await fetch(fileUrl);
    if (!fileRes.ok) {
      return res.status(200).json({ ok: false, error: "Não foi possível baixar o áudio dos servidores do Telegram." });
    }

    const arrayBuffer = await fileRes.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // 2. Prepara o formulário binário para a ElevenLabs
    const formData = new FormData();
    const audioBlob = new Blob([buffer], { type: "audio/ogg" });
    
    formData.append("file", audioBlob, "audio.ogg");
    formData.append("model_id", "scribe_v1");
    formData.append("language_code", "pt");

    // 3. Dispara a chamada de transcrição (ASR)
    const response = await fetch("https://api.elevenlabs.io/v1/speech-to-text", {
      method: "POST",
      headers: {
        "xi-api-key": apiKey
      },
      body: formData
    });

    if (!response.ok) {
      const errorText = await response.text();
      let detailMsg = errorText;

      try {
        const parsed = JSON.parse(errorText);
        detailMsg = parsed.detail?.message || parsed.message || errorText;
      } catch (e) {}

      return res.status(200).json({ 
        ok: false, 
        error: `Erro na ElevenLabs (Status ${response.status})`,
        detail: detailMsg
      });
    }

    const result: any = await response.json();
    
    return res.status(200).json({ 
      ok: true, 
      text: result.text || "" 
    });

  } catch (e: any) {
    console.error("Erro na rota de transcrição:", e);
    return res.status(200).json({ ok: false, error: "Erro interno no servidor: " + e.message });
  }
}
