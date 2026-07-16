/* File: api/transcribe.ts | Standalone Transcription Bridge for ElevenLabs Scribe */
import type { VercelRequest, VercelResponse } from "@vercel/node";

function sendJson(res: VercelResponse, status: number, data: any): void {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(data));
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    if (req.method !== "POST") {
      return sendJson(res, 405, { ok: false, error: "Method not allowed" });
    }

    const { fileUrl, apiKey } = req.body;

    if (!fileUrl || !apiKey) {
      return sendJson(res, 400, { ok: false, error: "Missing 'fileUrl' or 'apiKey' parameter" });
    }

    // 1. Fetch the binary file from Telegram's servers
    const fileRes = await fetch(fileUrl);
    if (!fileRes.ok) {
      return sendJson(res, 500, { ok: false, error: "Failed to download file from Telegram" });
    }

    const arrayBuffer = await fileRes.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // 2. Prepare the multipart FormData payload
    const formData = new FormData();
    const audioBlob = new Blob([buffer], { type: "audio/ogg" }); // Telegram voice notes default to OGG/OPUS
    
    formData.append("file", audioBlob, "audio.ogg");
    formData.append("model_id", "scribe_v1"); // Scribe V1 engine
    formData.append("language_code", "pt");   // Pre-sets transcription language to Portuguese

    // 3. Post to ElevenLabs Speech-To-Text Endpoint
    const response = await fetch("https://api.elevenlabs.io/v1/speech-to-text", {
      method: "POST",
      headers: {
        "xi-api-key": apiKey
      },
      body: formData
    });

    if (!response.ok) {
      const errorText = await response.text();
      return sendJson(res, response.status, { 
        ok: false, 
        error: "ElevenLabs API Error", 
        detail: errorText 
      });
    }

    const result: any = await response.json();
    
    return sendJson(res, 200, { 
      ok: true, 
      text: result.text || "" 
    });

  } catch (e: any) {
    console.error("Transcription error:", e);
    return sendJson(res, 500, { ok: false, error: "Internal Server Error: " + e.message });
  }
}
