// api/index.js - Versao Estavel para Download no Navegador
const axios = require('axios');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  const { url } = req.query;

  if (!url) {
    return res.status(400).json({ ok: false, error: "O parametro url e obrigatorio!" });
  }

  try {
    // 1. Busca o link de audio na API externa
    const apiUrl = `https://go-api-six.vercel.app/youtube/stream?url=${encodeURIComponent(url)}`;
    const apiRes = await axios.get(apiUrl, { timeout: 15000 });

    if (!apiRes.data || (!apiRes.data.url && (!apiRes.data.formats || apiRes.data.formats.length === 0))) {
      return res.status(404).json({ ok: false, error: "Stream nao encontrado na fonte." });
    }

    const streamUrl = apiRes.data.url || apiRes.data.formats[0].url;

    // 2. Baixamos como ARRAYBUFFER (arquivo completo) em vez de stream para evitar crash na Vercel!
    const responseFile = await axios({
      method: 'GET',
      url: streamUrl,
      responseType: 'arraybuffer',
      timeout: 35000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.youtube.com/',
        'Origin': 'https://www.youtube.com',
        'Accept': '*/*'
      }
    });

    // 3. Avisamos ao navegador que e um arquivo MP3 para download
    res.setHeader('Content-Disposition', 'attachment; filename="musica_extraida.mp3"');
    res.setHeader('Content-Type', 'audio/mpeg');
    res.setHeader('Content-Length', responseFile.data.length);

    // 4. Enviamos o arquivo limpo para o seu navegador
    return res.status(200).send(responseFile.data);

  } catch (error) {
    let msgErro = error.message;
    if (error.response) {
      // Se der erro HTTP, transformamos o buffer de erro em texto legivel
      if (Buffer.isBuffer(error.response.data)) {
        msgErro = `Erro HTTP ${error.response.status}: ` + error.response.data.toString('utf8');
      } else {
        msgErro = `Erro HTTP ${error.response.status}: ` + JSON.stringify(error.response.data);
      }
    }
    return res.status(500).json({ ok: false, error: msgErro });
  }
};
