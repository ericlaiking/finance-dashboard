const yf = require('yahoo-finance2').default;
console.log(typeof yf);
try {
  const instance = new yf();
  instance.quote('AAPL').then(console.log).catch(console.error);
} catch(e) {
  console.log("Error logic:", e.message);
}
