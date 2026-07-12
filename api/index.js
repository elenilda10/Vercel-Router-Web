// api/index.js
const axios = require('axios');

module.exports = async (req, res) => {
  // Permite acesso de qualquer navegador
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  const { url } = req.query;

  if (!url) {
    return res.status(400).json({ ok: false, error: "O parâmetro url é obrigatório para o teste!" });
  }

  try {
    // 1. Consulta a API externa para pegar o link de stream
    const apiUrl = `https://go-api-six.vercel.app/youtube/stream?url=${encodeURIComponent(url)}`;
    const apiRes = await axios.get(apiUrl, { timeout: 15000 });

    if (!apiRes.data || (!apiRes.data.url && (!apiRes.data.formats || apiRes.data.formats.length === 0))) {
      return res.status(404).json({ ok: false, error: "Stream não encontrado na API externa." });
    }

    const streamUrl = apiRes.data.url || apiRes.data.formats[0].url;

    // 2. Conecta no YouTube com cabeçalhos disfarçados
    const responseStream = await axios({
      method: 'GET',
      url: streamUrl,
      responseType: 'stream', // Importante para lidar com o áudio em tempo real
      timeout: 30000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.youtube.com/',
        'Origin': 'https://www.youtube.com',
        'Accept': '*/*'
      }
    });

    // 3. Força o navegador a entender que é o download de um arquivo MP3
    res.setHeader('Content-Disposition', 'attachment; filename="teste_download.mp3"');
    res.setHeader('Content-Type', 'audio/mpeg');

    // 4. Repassa o áudio do YouTube direto para o seu navegador!
    responseStream.data.pipe(res);

  } catch (error) {
    let msgErro = error.message;
    if (error.response) {
      msgErro = `Erro HTTP ${error.response.status}: ` + JSON.stringify(error.response.data);
    }
    return res.status(500).json({ ok: false, error: msgErro });
  }
};
