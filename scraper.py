import requests
import json
import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone

# 偽裝 Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 設定固定的 EPS (2025 全年)
FIXED_EPS = 66.25 

def get_fear_and_greed():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            score = int(data['fear_and_greed']['score'])
            return score
    except Exception as e:
        print(f"❌ CNN 失敗: {e}")
    return None

def get_market_metrics():
    """
    智慧防呆版：
    1. 抓取過去 5 天資料
    2. ★關鍵★ 檢查抓到的資料日期，如果太舊 (>2天) 視為無效，避免用到歷史高價
    """
    try:
        tickers_list = ["^VIX", "^TNX", "TWD=X", "GC=F", "2330.TW"]
        data = yf.download(tickers_list, period="5d", progress=False)['Close']
        
        # 取得當下時間 (UTC+8) 用來比對
        tz_tw = timezone(timedelta(hours=8))
        today = datetime.now(tz_tw).date()
        
        result = {}
        
        # 定義我們要抓的欄位與對應名稱
        map_keys = {
            '^VIX': 'vix', 
            '^TNX': 'us_10y', 
            'TWD=X': 'usd_twd', 
            'GC=F': 'gold', 
            '2330.TW': 'tw_price' # 先存股價，等下算 PE
        }

        for ticker, key in map_keys.items():
            # 1. 取出該商品的資料，移除空值
            series = data[ticker].dropna()
            
            if series.empty:
                result[key] = None
                continue

            # 2. ★關鍵檢核★：最後一筆資料的日期
            last_date = series.index[-1].date()
            days_diff = (today - last_date).days
            
            # 如果資料落後超過 2 天 (例如今天是週五，卻只抓到週二的)，視為失效
            # (週末容許度大一點，設為 4 天以免週一抓不到週五)
            allowable_lag = 4 if today.weekday() == 0 else 2 
            
            if days_diff > allowable_lag:
                print(f"⚠️ {ticker} 資料過期！最後日期: {last_date}, 忽略此數值。")
                result[key] = None # 強制設為 None，讓主程式去繼承舊檔
            else:
                result[key] = float(series.iloc[-1])

        # 計算 PE (如果股價有效)
        if result.get('tw_price'):
            result['tw_pe'] = round(result['tw_price'] / FIXED_EPS, 2)
        else:
            result['tw_pe'] = None

        return result

    except Exception as e:
        print(f"❌ 市場指標抓取失敗: {e}")
        return None

def get_business_score(date_obj):
    y = date_obj.year
    m = date_obj.month
    if y == 2026: return 38
    if y == 2025 and m >= 12: return 34
    return 32

if __name__ == "__main__":
    print("🚀 開始執行爬蟲 (Date-Check Version)...")
    
    utc_now = datetime.now(timezone.utc)
    tw_time = utc_now + timedelta(hours=8)
    date_str = tw_time.strftime("%Y-%m-%d %H:%M")

    market_data = get_market_metrics()
    cnn_score = get_fear_and_greed()
    biz_score = get_business_score(tw_time)

    file_path = "data/history.json"
    history = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: pass
    
    # 上一筆資料 (備份用)
    last_entry = history[-1] if history else {}

    # 4. 資料合併與繼承
    # 邏輯：有新值且不為None -> 用新的；否則 -> 用舊的
    def get_val(key, default=0):
        new_val = market_data.get(key) if market_data else None
        if new_val is not None and new_val > 0:
            return round(new_val, 2)
        return last_entry.get(key, default)

    final_vix = get_val('vix', 15.0)
    final_bond = get_val('us_10y', 4.0)
    final_usd = get_val('usd_twd', 31.0)
    final_gold = get_val('gold', 2000.0)
    final_pe = get_val('tw_pe', 20.0)
    final_cnn = cnn_score if cnn_score is not None else last_entry.get('cnn_score', 50)

    new_entry = {
        "date": date_str,
        "cnn_score": final_cnn,
        "tw_pe": final_pe,
        "biz_score": biz_score,
        "vix": final_vix,
        "us_10y": final_bond,
        "usd_twd": final_usd,
        "gold": final_gold
    }

    history.append(new_entry)
    history = history[-20000:] 

    os.makedirs("data", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        
    print(f"💾 資料更新完成: {date_str}")
    print(f"📊 寫入: VIX={final_vix}, Gold={final_gold} (若為舊值代表抓取過期)")
