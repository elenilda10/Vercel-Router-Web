const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  // Recebe os dados enviados pelo seu bot TBL
  const { url, chat_id, token } = req.query;

  if (!url || !chat_id || !token) {
    return res.status(400).json({ ok: false, error: "Parâmetros url, chat_id e token são obrigatórios!" });
  }

  // Define um nome único para o arquivo temporário na pasta /tmp do servidor
  const fileName = `track_${Date.now()}.mp3`;
  const filePath = path.join('/tmp', fileName);

  try {
    // 1. Consulta a API go-api-six para extrair o link de stream
    const apiUrl = `https://go-api-six.vercel.app/youtube/stream?url=${encodeURIComponent(url)}`;
    const apiRes = await axios.get(apiUrl, { timeout: 15000 });

    if (!apiRes.data || (!apiRes.data.url && (!apiRes.data.formats || apiRes.data.formats.length === 0))) {
      return res.status(404).json({ ok: false, error: "A API não retornou um link de áudio válido ou há bloqueio restrito." });
    }

    const streamUrl = apiRes.data.url || apiRes.data.formats[0].url;
    const title = apiRes.data.title || "Áudio Extraído";
    const author = apiRes.data.author || "YouTube";

    // 2. Baixa o áudio do YouTube direto para o servidor da Alemanha (/tmp)
    const responseStream = await axios({
      method: 'GET',
      url: streamUrl,
      responseType: 'stream',
      timeout: 30000
    });

    const writeStream = fs.createWriteStream(filePath);
    responseStream.data.pipe(writeStream);

    await new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
      responseStream.data.on('error', reject);
    });

    // 3. Envia o arquivo MP3 fisicamente para o Telegram via Form-Data
    const formData = new FormData();
    formData.append('chat_id', chat_id);
    formData.append('caption', `*🎵 ${title}*\n*👤 ${author}*`, { parse_mode: 'Markdown' });
    formData.append('parse_mode', 'Markdown');
    formData.append('audio', fs.createReadStream(filePath), fileName);

    const tgResponse = await axios.post(
      `https://api.telegram.org/bot${token}/sendAudio`,
      formData,
      {
        headers: formData.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      }
    );

    // Retorna sucesso para o TeleBotHost saber que terminou
    return res.status(200).json({ ok: true, result: tgResponse.data });

  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message || "Erro interno no processamento" });
  } finally {
    // 4. LIMPEZA IMEDIATA: Executa sempre, dando certo ou errado
    if (fs.existsSync(filePath)) {
      try {
        fs.unlinkSync(filePath);
        console.log("Arquivo temporário apagado com sucesso:", filePath);
      } catch (e) {
        console.error("Erro ao apagar arquivo:", e);
      }
    }
  }
};
