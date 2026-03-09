const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');

/**
 * Fetch latest Taiwan Economic Development Indicator (景氣對策信號)
 * Strategy:
 *   1. Try scraping from macromicro.me (not behind Cloudflare)
 *   2. Fallback to config.json ndc_light_current value
 * @returns {number|null} Score (e.g., 17 for Blue light, 39 for Red light)
 */
async function getNDCLightScore() {
  // Strategy 1: Try web scraping from alternative sources
  const scraped = await tryScrapeMacroMicro();
  if (scraped !== null) return scraped;

  // Strategy 2: Fallback to config.json
  return getFromConfig();
}

async function tryScrapeMacroMicro() {
  try {
    const res = await fetch('https://www.macromicro.me/charts/55843/taiwan-business-indicator', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
      },
      timeout: 10000
    });

    if (!res.ok) return null;
    const html = await res.text();

    // Try to find the latest score in the page content
    // MacroMicro often embeds data as JSON within script tags
    const $ = cheerio.load(html);

    // Look for the score in various patterns
    const patterns = [
      /景氣對策信號.*?(\d{1,2})分/,
      /composite.*?score.*?[:\s]+(\d{1,2})/i,
      /"value"\s*:\s*(\d{1,2})\s*[,}]/
    ];

    const bodyText = $('body').text();
    for (const pattern of patterns) {
      const match = bodyText.match(pattern);
      if (match) {
        const val = parseInt(match[1], 10);
        if (val >= 9 && val <= 45) {
          console.log(`✅ [NDC] Scraped score from macromicro: ${val}`);
          return val;
        }
      }
    }

    return null;
  } catch (e) {
    console.warn('⚠️  [NDC] MacroMicro scrape failed:', e.message);
    return null;
  }
}

function getFromConfig() {
  try {
    const configPath = path.join(__dirname, '..', 'config.json');
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      if (config.tw0050 && config.tw0050.ndc_light_current !== undefined) {
        console.log(`📋 [NDC] Using config.json value: ${config.tw0050.ndc_light_current}`);
        return config.tw0050.ndc_light_current;
      }
    }
  } catch (e) {
    console.error('❌ [NDC] Config read failed:', e.message);
  }
  return null;
}

module.exports = { getNDCLightScore };
