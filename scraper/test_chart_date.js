const yf = require('yahoo-finance2').default;
const yahooFinance = new yf();

async function run() {
    // Current approach in yahoo.js
    const period1 = new Date(Date.now() - (10) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const period2 = new Date().toISOString().split('T')[0];
    
    console.log("Current Period2: ", period2);

    const result = await yahooFinance.chart('VOO', {
      period1,
      period2,
      interval: '1d'
    });
    
    console.log("Current Setup Results: ");
    console.log(result.quotes.map(q => ({ date: new Date(q.date).toISOString().split('T')[0], close: q.close })));

    // Try without period2 (gets latest automatically?)
    const result2 = await yahooFinance.chart('VOO', {
      period1,
      interval: '1d'
    });
    
    console.log("\nWithout period2 Results: ");
    console.log(result2.quotes.map(q => ({ date: new Date(q.date).toISOString().split('T')[0], close: q.close })));
}
run();
