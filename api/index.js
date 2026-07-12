// api/index.js
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');
const { HttpsProxyAgent } = require('https-proxy-agent');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  const token = process.env.BOT_TOKEN;
  const { url, chat_id } = req.query;

  // CONFIGURAÇÃO DO PROXY (Substitua pelos dados da FineData)
  // Exemplo: http://usuario:senha@168.119.153.216:8888
  const proxyUrl = 'http://168.119.153.216:8888'; 
  const agent = new HttpsProxyAgent(proxyUrl);

  if (!url || !chat_id || !token) {
    return res.status(400).json({ ok: false, error: "Parâmetros faltando!" });
  }

  const fileName = `track_${Date.now()}.mp3`;
  const filePath = path.join('/tmp', fileName);

  try {
    // 1. Obtém o stream via API externa
    const apiUrl = `https://go-api-six.vercel.app/youtube/stream?url=${encodeURIComponent(url)}`;
    const apiRes = await axios.get(apiUrl, { timeout: 15000 });

    if (!apiRes.data || !apiRes.data.url) {
      throw new Error("Não foi possível obter o stream.");
    }

    const streamUrl = apiRes.data.url;

    // 2. Download usando o Agente de Proxy (Resolve o 403 Forbidden)
    const responseStream = await axios({
      method: 'GET',
      url: streamUrl,
      responseType: 'stream',
      timeout: 30000,
      httpsAgent: agent, // O MÁGICO: Força o uso do Proxy
      httpAgent: agent,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
      }
    });

    const writeStream = fs.createWriteStream(filePath);
    responseStream.data.pipe(writeStream);

    await new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
      responseStream.data.on('error', reject);
    });

    // 3. Upload direto para o Telegram
    const formData = new FormData();
    formData.append('chat_id', chat_id);
    formData.append('audio', fs.createReadStream(filePath), fileName);

    await axios.post(`https://api.telegram.org/bot${token}/sendAudio`, formData, {
      headers: formData.getHeaders()
    });

    return res.status(200).json({ ok: true, message: "Enviado com sucesso!" });

  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  } finally {
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
  }
};
