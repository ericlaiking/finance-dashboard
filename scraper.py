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
    改良版：抓取 VIX, 美債, 匯率, 黃金, 台積電
    使用 period='5d' 確保不會因為假日或剛開盤而抓到空值
    """
    try:
        tickers_list = ["^VIX", "^TNX", "TWD=X", "GC=F", "2330.TW"]
        # 一次抓 5 天，避免當天沒開盤回傳空值
        data = yf.download(tickers_list, period="5d", progress=False)['Close']
        
        # 取得各指標「最後一筆有效的數值」(Last Valid Index)
        # .iloc[-1] 即使中間有缺漏，也會抓到最近的一筆
        vix = data['^VIX'].dropna().iloc[-1]
        tnx = data['^TNX'].dropna().iloc[-1]
        twd = data['TWD=X'].dropna().iloc[-1]
        gold = data['GC=F'].dropna().iloc[-1]
        tsmc = data['2330.TW'].dropna().iloc[-1]

        # 計算 PE
        pe = tsmc / FIXED_EPS

        return {
            "vix": round(float(vix), 2),
            "us_10y": round(float(tnx), 2), 
            "usd_twd": round(float(twd), 2),
            "gold": round(float(gold), 2),
            "tw_pe": round(float(pe), 2)
        }
    except Exception as e:
        print(f"❌ 市場指標抓取失敗 (將沿用舊資料): {e}")
        # 回傳 None，讓主程式知道要去讀歷史紀錄
        return None

def get_business_score(date_obj):
    # 根據當下月份回傳景氣分數 (模擬/真實對照表)
    y = date_obj.year
    m = date_obj.month
    # 2026 最新
    if y == 2026: return 38
    # 2025 歷史
    if y == 2025 and m >= 12: return 34
    return 32 # 預設

if __name__ == "__main__":
    print("🚀 開始執行爬蟲 (Robust Version)...")
    
    # 1. 時間設定
    utc_now = datetime.now(timezone.utc)
    tw_time = utc_now + timedelta(hours=8)
    date_str = tw_time.strftime("%Y-%m-%d %H:%M")

    # 2. 抓取資料
    market_data = get_market_metrics()
    cnn_score = get_fear_and_greed()
    biz_score = get_business_score(tw_time)

    # 3. 讀取歷史檔案
    file_path = "data/history.json"
    history = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: pass
    
    # 取得上一筆資料作為備份
    last_entry = history[-1] if history else {
        "cnn_score": 50, "tw_pe": 20, "biz_score": 30,
        "vix": 15, "us_10y": 4.0, "usd_twd": 31.0, "gold": 2000
    }

    # 4. 資料合併與防呆 (關鍵步驟!)
    # 如果抓取失敗 (None) 或數值為 0，就用上一筆資料覆蓋
    
    final_vix = market_data['vix'] if (market_data and market_data['vix'] > 0) else last_entry.get('vix', 0)
    final_bond = market_data['us_10y'] if (market_data and market_data['us_10y'] > 0) else last_entry.get('us_10y', 0)
    final_usd = market_data['usd_twd'] if (market_data and market_data['usd_twd'] > 0) else last_entry.get('usd_twd', 0)
    final_gold = market_data['gold'] if (market_data and market_data['gold'] > 0) else last_entry.get('gold', 0)
    final_pe = market_data['tw_pe'] if (market_data and market_data['tw_pe'] > 0) else last_entry.get('tw_pe', 0)
    
    final_cnn = cnn_score if cnn_score is not None else last_entry.get('cnn_score', 50)

    # 5. 建立新資料
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

    # 6. 寫入檔案
    history.append(new_entry)
    
    # 保留 20000 筆
    history = history[-20000:] 

    os.makedirs("data", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        
    print(f"💾 資料更新完成: {date_str}")
    print(f"📊 寫入數據: VIX={final_vix}, Gold={final_gold}, PE={final_pe}")
