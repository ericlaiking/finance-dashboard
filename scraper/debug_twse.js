const fetch = require('node-fetch');

async function debugTWSE() {
    const res = await fetch("https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json");
    const json = await res.json();
    console.log("TWSE Data:");
    json.data.forEach(row => {
        console.log(row[0], row[3]);
    });
}
debugTWSE();
