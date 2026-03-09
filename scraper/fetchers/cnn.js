const fetch = require('node-fetch');

const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'application/json, text/plain, */*',
  'Origin': 'https://edition.cnn.com',
  'Referer': 'https://edition.cnn.com/'
};

async function getFearAndGreed() {
  try {
    const response = await fetch('https://production.dataviz.cnn.io/index/fearandgreed/graphdata', { headers: HEADERS });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (data && data.fear_and_greed && data.fear_and_greed.score) {
      return Math.round(data.fear_and_greed.score);
    }
    return null;
  } catch (error) {
    console.error('❌ [CNN Fetcher] Failed to get Fear & Greed:', error.message);
    return null;
  }
}

module.exports = {
  getFearAndGreed
};
