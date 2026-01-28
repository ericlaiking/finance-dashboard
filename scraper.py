import requests
import json
import os
import time
from datetime import datetime, timedelta, timezone # <--- 1. 引入必要的時間模組

# 設定偽裝 Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
    'Referer': 'https://www.google.com/'
}

def get_fear_and_greed():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        score = int(data['fear_and_greed']['score'])
        rating = data['fear_and_greed']['rating']
        
        rating_map = {
            "Extreme Fear": "極度恐懼", "Fear": "恐懼", 
            "Neutral": "中立", 
            "Greed": "貪婪", "Extreme Greed": "極度貪婪"
        }
        rating_zh = rating_map.get(rating, rating)
        print(f"✅ CNN 成功: {score}")
        return {"score": score, "rating": rating_zh}
    except Exception as e:
        print(f"❌ CNN 失敗: {e}")
        return {"score": 0, "rating": "連線失敗"}

def get_tw_stock_data():
    url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_d"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        target_stock = next((s for s in data if s['Code'] == "2330"), None)
        
        if target_stock:
            print(f"✅ 台股成功 (2330)")
            return {"pe": target_stock['PE'], "yield": target_stock['Yield']}
        else:
            print("❌ 台股失敗: 找不到 2330")
    except Exception as e:
        print(f"❌ 台股 API 失敗: {e}")
    return {"pe": "N/A", "yield": "N/A"}

def get_business_signal():
    return {"light": "紅燈", "score": 38} 

if __name__ == "__main__":
    print("🚀 開始執行爬蟲...")

    # --- 2. 這裡進行時區校正 ---
    # 取得目前的 UTC 時間
    utc_now = datetime.now(timezone.utc)
    # 強制加上 8 小時變成台灣時間
    tw_time = utc_now + timedelta(hours=8)
    # 格式化輸出
    tw_time_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")
    # -------------------------

    result = {
        "updated_at": tw_time_str, # 使用校正後的時間
        "fear_greed": get_fear_and_greed(),
        "tw_market": get_tw_stock_data(),
        "business_signal": get_business_signal()
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/dashboard.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"💾 資料已儲存 (台灣時間: {tw_time_str})")
