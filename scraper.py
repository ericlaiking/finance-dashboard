import requests
import json
import os
import yfinance as yf
from datetime import datetime, timedelta, timezone

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
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
        return None

def get_tw_stock_pe():
    try:
        stock = yf.Ticker("2330.TW")
        # 取得最新收盤價
        price = stock.history(period="1d")['Close'].iloc[-1]
        
        # 強制使用 2025 全年 EPS (避免 Yahoo 資料庫浮動)
        EPS_TTM = 66.25 
        
        pe = price / EPS_TTM
        return round(pe, 2)
    except Exception as e:
        print(f"❌ 台股 PE 失敗: {e}")
        return None

def get_market_metrics():
    """抓取 VIX, 美債, 匯率, 黃金"""
    try:
        # 新增 GC=F (黃金)
        tickers = yf.Tickers("^VIX ^TNX TWD=X GC=F")
        
        vix = tickers.tickers["^VIX"].history(period='1d')['Close'].iloc[-1]
        tnx = tickers.tickers["^TNX"].history(period='1d')['Close'].iloc[-1]
        twd = tickers.tickers["TWD=X"].history(period='1d')['Close'].iloc[-1]
        gold = tickers.tickers["GC=F"].history(period='1d')['Close'].iloc[-1]

        return {
            "vix": round(vix, 2),
            "us_10y": round(tnx, 2), 
            "usd_twd": round(twd, 2),
            "gold": round(gold, 2) # 新增
        }
    except Exception as e:
        print(f"❌ 市場指標失敗: {e}")
        return {"vix": 0, "us_10y": 0, "usd_twd": 0, "gold": 0}

def get_business_score():
    return 38

if __name__ == "__main__":
    print("🚀 開始執行爬蟲...")
    utc_now = datetime.now(timezone.utc)
    tw_time = utc_now + timedelta(hours=8)
    date_str = tw_time.strftime("%Y-%m-%d %H:%M")

    market_data = get_market_metrics()
    
    new_data = {
        "date": date_str,
        "cnn_score": get_fear_and_greed(),
        "tw_pe": get_tw_stock_pe(),
        "biz_score": get_business_score(),
        "vix": market_data['vix'],
        "us_10y": market_data['us_10y'],
        "usd_twd": market_data['usd_twd'],
        "gold": market_data['gold']
    }

    file_path = "data/history.json"
    history = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: pass

    if history:
        last = history[-1]
        for key in new_data:
            if new_data[key] is None: new_data[key] = last.get(key, 0)

    history.append(new_data)
    history = history[-150:] 

    os.makedirs("data", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        
    print(f"💾 資料更新完成: {date_str}")
