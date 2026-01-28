import requests
import json
import os
import time
from datetime import datetime

# 設定偽裝 Headers，讓網站以為我們是真實瀏覽器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
    'Referer': 'https://www.google.com/'
}

def get_fear_and_greed():
    # 嘗試抓取 CNN 資料
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status() # 如果 403/404 會報錯
        data = r.json()
        
        # 解析資料
        score = int(data['fear_and_greed']['score'])
        rating = data['fear_and_greed']['rating']
        
        # 簡單翻譯評級
        rating_map = {
            "Extreme Fear": "極度恐懼", "Fear": "恐懼", 
            "Neutral": "中立", 
            "Greed": "貪婪", "Extreme Greed": "極度貪婪"
        }
        rating_zh = rating_map.get(rating, rating)
        
        print(f"✅ CNN 成功: {score} ({rating_zh})")
        return {"score": score, "rating": rating_zh}
        
    except Exception as e:
        print(f"❌ CNN 失敗: {e}")
        # 如果 API 改版或失敗，回傳錯誤狀態
        return {"score": 0, "rating": "連線失敗"}

def get_tw_stock_data():
    # 使用證交所 OpenAPI 抓取個股日本益比
    # 為了範例穩定，我們抓取 "2330 台積電" 代表
    url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_d"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        
        # 搜尋代碼為 2330 的資料
        target_stock = None
        for stock in data:
            if stock['Code'] == "2330":
                target_stock = stock
                break
        
        if target_stock:
            pe = target_stock['PE']
            yield_rate = target_stock['Yield'] # 證交所欄位名稱有時是 Yield 或 Yield_PB
            print(f"✅ 台股成功 (2330): PE {pe}, Yield {yield_rate}")
            return {"pe": pe, "yield": yield_rate}
        else:
            print("❌ 台股失敗: 找不到 2330 資料")
            
    except Exception as e:
        print(f"❌ 台股 API 失敗: {e}")
        
    return {"pe": "N/A", "yield": "N/A"}

def get_business_signal():
    # 這裡維持模擬數據，因為國發會 API 需要解析 XML 較複雜
    # 您可以手動每個月改這裡，或之後再寫進階爬蟲
    return {"light": "紅燈", "score": 38} 

if __name__ == "__main__":
    print("🚀 開始執行爬蟲...")
    
    result = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fear_greed": get_fear_and_greed(),
        "tw_market": get_tw_stock_data(), # 這裡改抓台積電
        "business_signal": get_business_signal()
    }
    
    # 確保資料夾存在
    os.makedirs("data", exist_ok=True)
    
    with open("data/dashboard.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print("💾 資料已儲存至 data/dashboard.json")
