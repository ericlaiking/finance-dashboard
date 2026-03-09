# 📊 投資決策戰情室 (Finance Dashboard)

自動化、模組化且具備完整投資決策邏輯的金融儀表板，專為行動裝置體驗（Mobile-First）打造。此專案透過 GitHub Actions 與 Node.js 定期從各公開數據源提取即時資料，產生客製化的投資建議 (Buy / Hold / Wait)。

👉 **[查看即時戰情室首頁](https://ericlaiking.github.io/finance-dashboard/)**

## ✨ 核心特色

- **零伺服器架構**：完全基於 GitHub Actions (排程抓取) + GitHub Pages (靜態託管) 運作，零維護成本。
- **三大專屬面板**：
  - 🇺🇸 **美股核心 VOO**：基於 Fear & Greed, S&P 500 乖離率, VIX 等指標研判中長線買點。
  - 🇹🇼 **台股趨勢 0050**：基於國發會景氣對策信號, 台幣匯率, 外資買賣超研判景氣位階。
  - 🛡️ **避風防禦 00713**：基於預估殖利率與 10Y 美債之利差 (Yield Gap)，加上複合信號引擎提示最佳避風時機。
- **動態決策引擎**：從硬核數據中提煉出具體的「信心指數」與「行動建議」，並說明原因。
- **現代化 UI**：iOS-inspired 的深色毛玻璃 (Glassmorphism) 設計，支援底部切換導航。

## 🛠️ 技術棧

- **Data Fetching (Crawler)**: Node.js 20, `yahoo-finance2`, `node-fetch`, 台灣開放資料 API (TWSE, NDC).
- **Automation**: GitHub Actions (Hourly cron job)
- **Frontend Layer**: Vanilla JavaScript, Vanilla CSS, HTML5, Chart.js

## ⚙️ 參數設定與閾值修改

所有的買賣警示與權重閾值不需修改程式碼，統一管理於 `scraper/config.json`：

```json
{
  "defense00713": {
    "annual_dividend": 2.5, // 每年需手動更新宣告的股息
    "buyThresholds": {
      "yield_gap_min": 3.0
    },
    // 支援複合型信號引擎 (Pluggable Rules)
    "compositeRules": [
       {
         "id": "safe_haven_pick",
         "label": "🏆 資金避風港首選",
         "conditions": [ ... ]
       }
    ]
  }
}
```

## 🚀 開發與本地測試

如果您想在本地端進行開發或測試新指標：

1. **安裝依賴**:
   ```bash
   cd scraper
   npm install
   ```
2. **手動執行爬蟲與決策引擎**:
   ```bash
   node index.js
   ```
   > 執行成功後，將會於資料夾 `data/` 中產出最新的 `voo.json`, `tw0050.json`, `defense00713.json`。

3. **啟動預覽伺服器**:
   ```bash
   # 在專案根目錄下
   npx http-server -p 8080
   ```
   最後打開瀏覽器 `http://127.0.0.1:8080` 即可檢視效果。

---

> Disclaimer: 本專案代碼僅供學習與自動化流程研究使用，工具生成的任何信號不構成真實的投資建議。盈虧請自負。
