const yf = require('yahoo-finance2').default;

async function testNews() {
  try {
    const result = await yf.search('AAPL');
    console.log(JSON.stringify(result.news, null, 2));
  } catch (err) {
    console.error(err);
  }
}
testNews();
