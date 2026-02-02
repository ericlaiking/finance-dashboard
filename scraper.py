import requests
import json
import os
import pandas as pd
import yfinance as yf
import re
from datetime import datetime, timedelta, timezone

# ==========================================
# ★ 請確認您的 Google Sheet CSV 網址還在 ★
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNHviKb9PNe3Ho-5JAf10hfsJkRusPT_oJS2rfP0i2US0AGs32ZbQAoYa3TaIzNdHsWPcEpqX1IcJ3/pub?gid=1615478278&single=true&output=csv" 
# (請記得換回您真正的那串網址)
# ==========================================

# 設定固定的 EPS (2025 全年)
FIXED_EPS = 66.25 

# 偽裝 Headers (這是突破 Investing.com 的關鍵)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7'
}

def get_google_sheet_data():
    """從 Google Sheets 讀取黃金、匯率、台積電"""
    print("📥 正在從 Google Sheets 讀取數據...")
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        # 轉成 Dictionary
        data = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
        return data
    except Exception as e:
        print(f"❌ Google Sheet 讀取失敗: {e}")
        return {}

def get_investing_us10y():
    """
    專門為 Investing.com 寫的爬蟲
    目標網址: https://hk.investing.com/rates-bonds/u.s.-10-year-bond-yield
    """
    url = "https://hk.investing.com/rates-bonds/u.s.-10-year-bond-yield"
    print(f"🕵️ 正在嘗試抓取 Investing.com: {url} ...")
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            print(f"⚠️ Investing.com 回傳錯誤碼: {r.status_code}")
            return None
            
        # 使用 Regex 直接搜尋 HTML 裡的價格數據
        # 目標特徵: data-test="instrument-price-last">4.253</span>
        # 這種寫法不需要安裝 BeautifulSoup，適合 GitHub Actions
        match = re.search(r'data-test="instrument-price-last"[^>]*>([0-9\.]+)<', r.text)
        
        if match:
            val = float(match.group(1))
            print(f"✅ 抓到了！美債殖利率: {val}")
            return val
        else:
            print("⚠️ 找不到價格欄位，可能是網頁改版了")
            return None
    except Exception as e:
        print(f"❌ Investing.com 抓取失敗: {e}")
        return None

def get_vix_from_yf():
    """VIX 維持原案，用 yfinance 抓"""
    try:
        ticker = yf.Ticker("^VIX")
        data = ticker.history(period="5d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
    except:
        pass
    return None

def get_fear_and_greed():
    try:
        r = requests.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata", headers=HEADERS, timeout=10)
        return int(r.json()['fear_and_greed']['score'])
    except:
        return None

if __name__ == "__main__":
    print("🚀 開始執行爬蟲 (Hybrid V4.0)...")
    
    # 1. 各路人馬分頭抓取
    sheet_data = get_google_sheet_data()  # 黃金, 匯率, 2330
    us_10y_val = get_investing_us10y()    # 美債 (新來源)
    vix_val = get_vix_from_yf()           # VIX (原方案)
    cnn_score = get_fear_and_greed()      # CNN
    
    # 2. 數值整理
    def parse_val(val):
        try:
            return float(val)
        except:
            return 0.0

    # 從 Sheet 拿
    tw_price = parse_val(sheet_data.get('2330_price', 0))
    gold_price = parse_val(sheet_data.get('gold', 0))
    usd_twd = parse_val(sheet_data.get('usd_twd', 0))
    
    # 3. 讀取歷史 (為了繼承舊資料)
    file_path = "data/history.json"
    history = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            history = json.load(f)
            
    last = history[-1] if history else {}
    
    # 4. 組合最終數據 (優先用新抓到的 -> 失敗用 Sheet 備份 -> 再失敗用 History 繼承)
    
    # VIX
    final_vix = vix_val if (vix_val and vix_val > 0) else parse_val(sheet_data.get('vix', 0))
    if final_vix == 0: final_vix = last.get('vix', 0)
    
    # 美債 (US 10Y)
    final_us10y = us_10y_val if (us_10y_val and us_10y_val > 0) else parse_val(sheet_data.get('us_10y', 0))
    if final_us10y == 0: final_us10y = last.get('us_10y', 0)

    # 黃金 & 匯率 & 股價 (主要靠 Sheet)
    final_gold = gold_price if gold_price > 0 else last.get('gold', 0)
    final_usd = usd_twd if usd_twd > 0 else last.get('usd_twd', 0)
    final_price = tw_price if tw_price > 0 else last.get('tw_price', 0) # 暫存股價但不寫入 JSON

    # PE 計算
    if final_price > 0:
        final_pe = round(final_price / FIXED_EPS, 2)
    else:
        final_pe = last.get('tw_pe', 0)

    # CNN
    final_cnn = cnn_score if cnn_score else last.get('cnn_score', 50)

    # 5. 建立新紀錄
    final_entry = {
        "date": (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
        "cnn_score": final_cnn,
        "tw_pe": final_pe,
        "biz_score": 38,
        "vix": final_vix,
        "us_10y": final_us10y,
        "usd_twd": final_usd,
        "gold": final_gold
    }

    history.append(final_entry)
    history = history[-20000:]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"✅ 更新完成: US10Y={final_us10y}, VIX={final_vix}, Gold={final_gold}")
