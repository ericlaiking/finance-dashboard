const { getFearAndGreed } = require('./fetchers/cnn');
const { getQuotes, getMADeviation } = require('./fetchers/yahoo');
const { getForeignNetBuy } = require('./fetchers/twse');
const { getNDCLightScore } = require('./fetchers/ndc');

async function testAll() {
    console.log("=== Testing Fetchers ===");
    
    const cnnScore = await getFearAndGreed();
    console.log("Fear & Greed:", cnnScore);
    
    const quotes = await getQuotes(["VOO", "0050.TW", "00713.TW", "^VIX", "^TNX", "GC=F", "TWD=X"]);
    console.log("Quotes (snippet):");
    Object.keys(quotes).forEach(sym => {
      console.log(`  ${sym}: ${quotes[sym].price}`);
    });
    
    const dev = await getMADeviation("^GSPC", 120);
    console.log("S&P 500 120MA Dev:", dev, "%");
    
    const twseBuy = await getForeignNetBuy();
    console.log("Foreign Net Buy (億):", twseBuy);
    
    const ndcScore = await getNDCLightScore();
    console.log("NDC Light Score:", ndcScore);
}

testAll();
