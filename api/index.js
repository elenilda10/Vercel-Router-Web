// api/index.js
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  // Pega o token seguro das variáveis de ambiente da Vercel
  const token = process.env.BOT_TOKEN;
  const { url, chat_id } = req.query;

  // Verifica se todos os dados necessários estão presentes
  if (!url || !chat_id) {
    return res.status(400).json({ 
      ok: false, 
      error: "Os parâmetros url e chat_id são obrigatórios na chamada!" 
    });
  }

  if (!token) {
    return res.status(500).json({ 
      ok: false, 
      error: "A variável BOT_TOKEN não foi configurada nas configurações da Vercel!" 
    });
  }

  const fileName = `track_${Date.now()}.mp3`;
  const filePath = path.join('/tmp', fileName);

  try {
    // 1. Consulta a API para pegar o stream
    const apiUrl = `https://go-api-six.vercel.app/youtube/stream?url=${encodeURIComponent(url)}`;
    const apiRes = await axios.get(apiUrl, { timeout: 15000 });

    if (!apiRes.data || (!apiRes.data.url && (!apiRes.data.formats || apiRes.data.formats.length === 0))) {
      return res.status(404).json({ ok: false, error: "Link de áudio não encontrado ou bloqueado." });
    }

    const streamUrl = apiRes.data.url || apiRes.data.formats[0].url;
    const title = apiRes.data.title || "Áudio Extraído";
    const author = apiRes.data.author || "YouTube";

    // 2. Baixa o arquivo na pasta /tmp do servidor alemão
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

    // 3. Envia para o chat_id específico do usuário no Telegram
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

    return res.status(200).json({ ok: true, result: tgResponse.data });

  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message || "Erro interno no processamento" });
  } finally {
    // 4. Limpeza imediata para não encher o servidor
    if (fs.existsSync(filePath)) {
      try {
        fs.unlinkSync(filePath);
        console.log("Arquivo temporário removido:", filePath);
      } catch (e) {
        console.error("Erro ao limpar arquivo:", e);
      }
    }
  }
};
