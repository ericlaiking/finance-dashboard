const fetch = require('node-fetch');

const URL = "https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json";
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
};

/**
 * Fetch latest Foreign Investor Net Buy/Sell amount
 * @returns {number|null} Net Buy/Sell in Billion NTD (億)
 */
async function getForeignNetBuy() {
  try {
    const res = await fetch(URL, { headers: HEADERS });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const json = await res.json();
    
    if (json && json.data) {
        const foreignRow = json.data.find(row => row[0].trim() === '外資及陸資(不含外資自營商)');
        if (foreignRow) {
            // value is a string with commas like "-12,345,678,901"
            const rawVal = foreignRow[3].replace(/,/g, '');
            const valueNTD = parseFloat(rawVal);
            // Convert to billions (億)
            return Math.round(valueNTD / 100000000);
        }
    }
    return null;
  } catch (error) {
    console.error('❌ [TWSE Fetcher] Failed getting foreign buy:', error.message);
    return null;
  }
}

module.exports = {
  getForeignNetBuy
};
