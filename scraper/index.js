const fs = require('fs');
const path = require('path');

// Fetchers
const { getFearAndGreed } = require('./fetchers/cnn');
const { getQuotes, getMADeviation, getHistoricalPrices, getNews } = require('./fetchers/yahoo');
const { getForeignNetBuy } = require('./fetchers/twse');
const { getNDCLightScore } = require('./fetchers/ndc');

// Engines
const { evaluateVOO } = require('./decision/voo-engine');
const { evaluateQQQ } = require('./decision/qqq-engine');
const { evaluateTW0050 } = require('./decision/tw0050-engine');
const { evaluateDefense00713 } = require('./decision/defense-engine');

async function main() {
    console.log("🚀 開始執行 Node.js 金融數據爬蟲...");

    // 1. Load config
    const configPath = path.join(__dirname, 'config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

    // 2. Fetch all raw data concurrently
    console.log("📥 Fetching raw data...");
    
    // Symbols to fetch: VOO, QQQ, 0050.TW, 00713.TW, VIX, US10Y (^TNX), Gold (GC=F), USD/TWD (TWD=X)
    const quoteSymbols = ["VOO", "QQQ", "0050.TW", "00713.TW", "^VIX", "^TNX", "GC=F", "TWD=X"];
    
    const [
        fearGreed,
        quotes,
        sp500Deviation,
        ndxDeviation,
        foreignBuy,
        ndcLight,
        newsData
    ] = await Promise.all([
        getFearAndGreed(),
        getQuotes(quoteSymbols),
        getMADeviation("^GSPC", 120),
        getMADeviation("^NDX", 120),
        getForeignNetBuy(),
        getNDCLightScore(),
        getNews("finance")
    ]);

    // 2b. Fetch historical chart data for all 4 funds (180 trading days)
    console.log("📈 Fetching 180-day chart data...");
    const [vooHistory, qqqHistory, tw0050History, tw00713History] = await Promise.all([
        getHistoricalPrices('VOO', 180),
        getHistoricalPrices('QQQ', 180),
        getHistoricalPrices('0050.TW', 180),
        getHistoricalPrices('00713.TW', 180)
    ]);
    console.log(`📊 Chart data: VOO=${vooHistory.length} days, QQQ=${qqqHistory.length} days, 0050=${tw0050History.length} days, 00713=${tw00713History.length} days`);

    // 3. Extract and normalize data points
    const now = new Date();
    // Format to Asia/Taipei implicitly by locale or just use ISO string + 8 hours
    const tzOffset = 8 * 60 * 60 * 1000;
    const updatedAt = new Date(now.getTime() + tzOffset).toISOString().replace('T', ' ').substring(0, 16);

    const dataPack = {
        voo_price: quotes["VOO"]?.price || null,
        voo_change: quotes["VOO"]?.changePercent || 0,
        qqq_price: quotes["QQQ"]?.price || null,
        qqq_change: quotes["QQQ"]?.changePercent || 0,
        tw0050_price: quotes["0050.TW"]?.price || null,
        tw0050_change: quotes["0050.TW"]?.changePercent || 0,
        tw00713_price: quotes["00713.TW"]?.price || null,
        tw00713_change: quotes["00713.TW"]?.changePercent || 0,
        vix: quotes["^VIX"]?.price || null,
        us10y: quotes["^TNX"]?.price || null,
        gold: quotes["GC=F"]?.price || null,
        usdTwd: quotes["TWD=X"]?.price || null,
        fearGreed,
        sp500Deviation,
        ndxDeviation,
        foreignBuy,
        ndcLight
    };

    console.log("✅ Data extracted:", JSON.stringify(dataPack, null, 2));

    // 4. Run Decision Engines
    const vooEngineData = { fearGreed, sp500Deviation, vix: dataPack.vix, us10y: dataPack.us10y };
    const vooResult = evaluateVOO(vooEngineData, config);

    const qqqEngineData = { fearGreed, ndxDeviation, vix: dataPack.vix, us10y: dataPack.us10y };
    const qqqResult = evaluateQQQ(qqqEngineData, config);

    const tw0050EngineData = { ndcLight, usdTwd: dataPack.usdTwd, foreignBuy };
    const tw0050Result = evaluateTW0050(tw0050EngineData, config);

    const defenseEngineData = { price: dataPack.tw00713_price, us10y: dataPack.us10y, vix: dataPack.vix, fearGreed };
    const defenseResult = evaluateDefense00713(defenseEngineData, config);

    // 5. Build Output JSON Files
    
    // VOO Output
    const vooJSON = {
      updated_at: updatedAt,
      fund: { name: "VOO", price: dataPack.voo_price, change_pct: parseFloat(dataPack.voo_change.toFixed(2)) },
      signal: { action: vooResult.action, label: vooResult.label, confidence: vooResult.confidence, reasons: vooResult.reasons },
      indicators: [
        { id: "fear_greed", name: "Fear & Greed Index", value: fearGreed },
        { id: "us_10y", name: "10Y 美債殖利率", value: parseFloat(dataPack.us10y?.toFixed(2) || 0), unit: "%" },
        { id: "sp500_deviation", name: "S&P 500 乖離率", value: sp500Deviation, unit: "%" },
        { id: "vix", name: "VIX 恐慌指數", value: parseFloat(dataPack.vix?.toFixed(2) || 0) }
      ],
      chart: vooHistory
    };

    // QQQ Output
    const qqqJSON = {
        updated_at: updatedAt,
        fund: { name: "QQQ", price: dataPack.qqq_price, change_pct: parseFloat(dataPack.qqq_change.toFixed(2)) },
        signal: { action: qqqResult.action, label: qqqResult.label, confidence: qqqResult.confidence, reasons: qqqResult.reasons },
        indicators: [
          { id: "fear_greed", name: "Fear & Greed Index", value: fearGreed },
          { id: "us_10y", name: "10Y 美債殖利率", value: parseFloat(dataPack.us10y?.toFixed(2) || 0), unit: "%" },
          { id: "ndx_deviation", name: "Nasdaq 100 乖離率", value: ndxDeviation, unit: "%" },
          { id: "vix", name: "VIX 恐慌指數", value: parseFloat(dataPack.vix?.toFixed(2) || 0) }
        ],
        chart: qqqHistory
    };

    // 0050 Output
    const tw0050JSON = {
      updated_at: updatedAt,
      fund: { name: "0050", price: dataPack.tw0050_price, change_pct: parseFloat(dataPack.tw0050_change.toFixed(2)) },
      signal: { action: tw0050Result.action, label: tw0050Result.label, confidence: tw0050Result.confidence, reasons: tw0050Result.reasons },
      indicators: [
        { id: "ndc_light", name: "景氣對策燈號", value: ndcLight, unit: "分" },
        { id: "usd_twd", name: "台幣匯率", value: parseFloat(dataPack.usdTwd?.toFixed(2) || 0) },
        { id: "foreign_buy", name: "外資買賣超", value: foreignBuy, unit: "億" }
      ],
      chart: tw0050History
    };

    // 00713 Defense Output
    const defense00713JSON = {
      updated_at: updatedAt,
      fund: { name: "00713", price: dataPack.tw00713_price, change_pct: parseFloat(dataPack.tw00713_change.toFixed(2)) },
      signal: { action: defenseResult.action, label: defenseResult.label, confidence: defenseResult.confidence, reasons: defenseResult.reasons },
      compositeSignal: defenseResult.compositeSignal || null,
      indicators: [
        { id: "estimated_yield", name: "預估殖利率", value: defenseResult.estimatedYield, unit: "%" },
        { id: "vix", name: "VIX 恐慌指數", value: parseFloat(dataPack.vix?.toFixed(2) || 0) },
        { id: "gold", name: "黃金避險價格", value: parseFloat(dataPack.gold?.toFixed(2) || 0), unit: "USD" }
      ],
      chart: tw00713History
    };

    // 6. Save to disk
    const dataDir = path.join(__dirname, '..', 'data');
    if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir);

    fs.writeFileSync(path.join(dataDir, 'voo.json'), JSON.stringify(vooJSON, null, 2));
    fs.writeFileSync(path.join(dataDir, 'qqq.json'), JSON.stringify(qqqJSON, null, 2));
    fs.writeFileSync(path.join(dataDir, 'tw0050.json'), JSON.stringify(tw0050JSON, null, 2));
    fs.writeFileSync(path.join(dataDir, 'defense00713.json'), JSON.stringify(defense00713JSON, null, 2));
    fs.writeFileSync(path.join(dataDir, 'news.json'), JSON.stringify({ updated_at: updatedAt, items: newsData }, null, 2));

    console.log("✅ JSON Outputs written successfully!");
}

main().catch(err => {
    console.error("❌ Fatal Error in scraper:", err);
    process.exit(1);
});
