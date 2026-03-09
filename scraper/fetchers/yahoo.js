const yf = require('yahoo-finance2').default;
const yahooFinance = new yf();

/**
 * Fetch latest quotes for a list of symbols
 * @param {string[]} symbols
 * @returns {Record<string, any>} Map of symbol to quote data
 */
async function getQuotes(symbols) {
  try {
    const results = await yahooFinance.quote(symbols);
    const quotesMap = {};
    results.forEach(quote => {
      quotesMap[quote.symbol] = {
        price: quote.regularMarketPrice,
        change: quote.regularMarketChange,
        changePercent: quote.regularMarketChangePercent,
        name: quote.shortName || quote.longName
      };
    });
    return quotesMap;
  } catch (error) {
    console.error('❌ [Yahoo Fetcher] Failed to get quotes:', error.message);
    return {};
  }
}

/**
 * Calculate Moving Average deviation for a given symbol
 * @param {string} symbol e.g., ^GSPC
 * @param {number} maDays e.g., 120 or 200
 * @returns {number|null} Deviation percentage, e.g., -8.5 means 8.5% below MA
 */
async function getMADeviation(symbol, maDays = 120) {
  try {
    const period1 = new Date(Date.now() - (maDays + 60) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const period2 = new Date().toISOString().split('T')[0];

    const result = await yahooFinance.chart(symbol, {
      period1,
      period2,
      interval: '1d'
    });

    if (result && result.quotes && result.quotes.length >= maDays) {
      const closes = result.quotes
        .filter(q => q.close !== null && q.close !== undefined)
        .map(q => q.close);

      if (closes.length >= maDays) {
        const recentData = closes.slice(-maDays);
        const sum = recentData.reduce((a, b) => a + b, 0);
        const ma = sum / maDays;
        const latestPrice = closes[closes.length - 1];

        const deviation = ((latestPrice - ma) / ma) * 100;
        return Math.round(deviation * 100) / 100;
      }
    }
    return null;
  } catch (error) {
    console.error(`❌ [Yahoo Fetcher] Failed to calculate MA deviation for ${symbol}:`, error.message);
    return null;
  }
}

/**
 * Fetch historical closing prices for a symbol (for chart rendering)
 * Uses chart() API which is the recommended replacement for historical()
 * @param {string} symbol
 * @param {number} days  Number of trading days to fetch
 * @returns {Array<{date: string, close: number}>}
 */
async function getHistoricalPrices(symbol, days = 250) {
  try {
    const period1 = new Date(Date.now() - (days + 60) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const period2 = new Date().toISOString().split('T')[0];

    const result = await yahooFinance.chart(symbol, {
      period1,
      period2,
      interval: '1d'
    });

    if (result && result.quotes && result.quotes.length > 0) {
      return result.quotes
        .filter(q => q.close !== null && q.close !== undefined)
        .map(q => ({
          date: new Date(q.date).toISOString().split('T')[0],
          close: parseFloat(q.close.toFixed(2))
        }))
        .slice(-days); // Keep only the most recent N days
    }
    return [];
  } catch (error) {
    console.error(`❌ [Yahoo Fetcher] Failed to get historical prices for ${symbol}:`, error.message);
    return [];
  }
}

module.exports = {
  getQuotes,
  getMADeviation,
  getHistoricalPrices
};
