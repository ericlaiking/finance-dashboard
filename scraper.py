import requests
import json
import os
from datetime import datetime

def get_fear_and_greed():
    # 這是 CNN 恐懼貪婪指數常用的非官方 API 端點
    # 如果失效，可能需要改用 Beautiful Soup 解析網頁
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # 取得最新一筆資料
            score = data['fear_and_greed']['score']
            rating = data['fear_and_greed']['rating']
            return {"score": score, "rating": rating}
    except Exception as e:
        print(f"Error fetching CNN: {e}")
    return {"score": 0, "rating": "Error"}

def get_twse_pe():
    # 台灣證交所 OpenAPI (取得大盤統計資訊)
    # BWIBBU_d = 本益比、殖利率及股價淨值比
    url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_d"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # 這是陣列，通常只有一筆最新的
            pe_ratio = data[0]['PE'] # 本益比
            yield_rate = data[0]['Yield_PB'] # 殖利率
            return {"pe": pe_ratio, "yield": yield_rate}
    except Exception as e:
        print(f"Error fetching TWSE: {e}")
    return {"pe": "0", "yield": "0"}

def get_business_signal():
    # 景氣燈號通常一個月才更新一次，國發會 API 較複雜
    # 這裡為求範例簡單，我們先寫死或抓取一個簡單的 JSON
    # 實戰中建議去國發會 Open Data 平台申請 API Key
    return {"light": "紅燈", "score": 38} 

if __name__ == "__main__":
    # 1. 抓取所有資料
    result = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fear_greed": get_fear_and_greed(),
        "tw_market": get_twse_pe(),
        "business_signal": get_business_signal()
    }
    
    print("Scraped Data:", result)

    # 2. 存檔 (確保 data 資料夾存在)
    os.makedirs("data", exist_ok=True)
    
    # 為了畫長週期的圖，我們通常會「累加」資料，但在這個簡單範例，
    # 我們先做「覆蓋式」的更新，專注於儀表板顯示當下狀態。
    # 如果要畫歷史走勢，需要讀取舊 json -> append 新資料 -> 寫入。
    
    with open("data/dashboard.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
