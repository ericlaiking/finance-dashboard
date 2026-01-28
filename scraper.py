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
        return None

def get_tw_stock_pe():
    try:
        stock = yf.Ticker("2330.TW")
        pe = stock.info.get('trailingPE')
        if pe is None:
            pe = stock.info.get('currentPrice', 1000) / 42.0 
        return round(pe, 2)
    except Exception as e:
        print(f"❌ 台股 PE 失敗: {e}")
        return None

def get_market_metrics():
    """
    一次抓取: VIX恐慌指數, 10年美債殖利率, 美元兌台幣
    """
    try:
        # ^VIX: 波動率指數
        # ^TNX: 10年期公債殖利率 (Yahoo給的格式通常是 42.5 代表 4.25%)
        # TWD=X: 美元兌台幣匯率
        tickers = yf.Tickers("^VIX ^TNX TWD=X")
        
        # 取得數據 (使用 history 因為 info有時候會漏)
        vix_hist = tickers.tickers["^VIX"].history(period='1d')
        tnx_hist = tickers.tickers["^TNX"].history(period='1d')
        twd_hist = tickers.tickers["TWD=X"].history(period='1d')

        vix = vix_hist['Close'].iloc[-1] if not vix_hist.empty else 0
        tnx = tnx_hist['Close'].iloc[-1] if not tnx_hist.empty else 0
        twd = twd_hist['Close'].iloc[-1] if not twd_hist.empty else 0

        print(f"✅ 市場指標成功: VIX={vix:.2f}, TNX={tnx:.2f}, TWD={twd:.2f}")
        return {
            "vix": round(vix, 2),
            "us_10y": round(tnx, 2), 
            "usd_twd": round(twd, 2)
        }
    except Exception as e:
        print(f"❌ 市場指標失敗: {e}")
        return {"vix": 0, "us_10y": 0, "usd_twd": 0}

def get_business_signal():
    # 模擬數據 (台灣景氣燈號通常一個月變一次)
    return {"light": "紅燈", "score": 38}

if __name__ == "__main__":
    print("🚀 開始執行爬蟲...")

    # 1. 設定台灣時間
    utc_now = datetime.now(timezone.utc)
    tw_time = utc_now + timedelta(hours=8)
    date_str = tw_time.strftime("%Y-%m-%d %H:%M")

    # 2. 抓取所有資料
    market_data = get_market_metrics()
    
    new_data = {
        "date": date_str,
        "cnn_score": get_fear_and_greed(),
        "tw_pe": get_tw_stock_pe(),
        "biz_score": get_business_signal()['score'],
        # 新增欄位
        "vix": market_data['vix'],
        "us_10y": market_data['us_10y'],
        "usd_twd": market_data['usd_twd']
    }

    # 3. 讀取與更新歷史資料
    file_path = "data/history.json"
    history = []
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

    # 填補 None 值 (防呆)
    if history:
        last = history[-1]
        for key in new_data:
            if new_data[key] is None: new_data[key] = last.get(key, 0)

    # 加入新資料並保留最後 90 筆 (因為現在有 90 天資料了，我們保留多一點)
    history.append(new_data)
    history = history[-100:] 

    # 4. 存檔
    os.makedirs("data", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        
    print(f"💾 資料更新完成: {date_str}")
