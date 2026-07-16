/* File: api/transcribe.ts | Fixed: Added custom 'prompt' parameter to guide Whisper's punctuation and natural style */
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

    // 2. Prepara o formulário binário compatível com o padrão OpenAI usado pela Groq
    const formData = new FormData();
    const audioBlob = new Blob([buffer], { type: "audio/ogg" });
    
    formData.append("file", audioBlob, "audio.ogg");
    formData.append("model", "whisper-large-v3");
    formData.append("language", "pt");
    
    // 💡 O TRUQUE: O prompt ensina o Whisper a pontuar, quebrar frases e aceitar expressões espontâneas como "pra", "né", "tava"
    formData.append(
      "prompt", 
      "Hum, peraí, olha só. Mas enfim, vamos lá, né, pra gente ver o que aconteceu de verdade. O texto transcrito deve conter pontuação impecável, uso coerente de vírgulas, pontos finais, começos de frase em maiúsculo e expressões naturais da fala brasileira."
    );

    // 3. Dispara a chamada de transcrição (ASR) para a Groq
    const response = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorText = await response.text();
      let detailMsg = errorText;

      try {
        const parsed = JSON.parse(errorText);
        detailMsg = parsed.error?.message || errorText;
      } catch (e) {}

      return res.status(200).json({ 
        ok: false, 
        error: `Erro na Groq (Status ${response.status})`,
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
