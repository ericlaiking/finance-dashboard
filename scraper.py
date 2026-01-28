import requests
import json
import os
import yfinance as yf
from datetime import datetime, timedelta, timezone

# 設定偽裝 Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_fear_and_greed():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        score = int(data['fear_and_greed']['score'])
        return score
    except Exception as e:
        print(f"❌ CNN 失敗: {e}")
        return None # 回傳 None 代表失敗

def get_tw_stock_pe():
    # 改用 yfinance 抓取台積電 (2330.TW) 作為參考
    # 因為 Yahoo Finance 資料比證交所 API 穩定
    try:
        stock = yf.Ticker("2330.TW")
        # 嘗試取得本益比 (Trailing PE)
        pe = stock.info.get('trailingPE')
        if pe is None:
            # 如果抓不到，嘗試用當下股價除以 EPS (假設 EPS 為 40, 概略估算)
            # 這只是 fallback，通常上面都抓得到
            pe = stock.info.get('currentPrice', 1000) / 42.0 
        
        print(f"✅ 台股 PE 成功: {pe}")
        return round(pe, 2)
    except Exception as e:
        print(f"❌ 台股 yfinance 失敗: {e}")
        return None

def get_business_signal():
    # 這裡維持模擬數據
    return {"light": "紅燈", "score": 38}

if __name__ == "__main__":
    print("🚀 開始執行爬蟲...")

    # 1. 設定台灣時間
    utc_now = datetime.now(timezone.utc)
    tw_time = utc_now + timedelta(hours=8)
    date_str = tw_time.strftime("%Y-%m-%d %H:%M") # 格式化時間 (不含秒，圖表比較好看)

    # 2. 抓取新資料
    new_data = {
        "date": date_str,
        "cnn_score": get_fear_and_greed(),
        "tw_pe": get_tw_stock_pe(),
        "biz_score": get_business_signal()['score'] # 只存分數方便畫圖
    }

    # 3. 讀取舊資料 (關鍵步驟：累積歷史)
    file_path = "data/history.json" # 我們改存成 history.json
    history = []
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

    # 4. 處理資料填補 (如果某個抓失敗，就沿用上一筆資料，避免圖表斷掉)
    if history:
        last_entry = history[-1]
        if new_data['cnn_score'] is None: new_data['cnn_score'] = last_entry.get('cnn_score', 0)
        if new_data['tw_pe'] is None: new_data['tw_pe'] = last_entry.get('tw_pe', 0)
    else:
        # 如果是第一筆且失敗，給預設值
        if new_data['cnn_score'] is None: new_data['cnn_score'] = 50
        if new_data['tw_pe'] is None: new_data['tw_pe'] = 20

    # 5. 加入新資料並限制長度 (只留最後 30 筆)
    history.append(new_data)
    history = history[-30:] # List Slicing

    # 6. 存檔
    os.makedirs("data", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        
    print(f"💾 歷史資料已更新，目前共有 {len(history)} 筆")
