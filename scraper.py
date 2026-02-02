import requests
import json
import os
import pandas as pd
import yfinance as yf
import re
from datetime import datetime, timedelta, timezone

# ==========================================
# ★ 已更新為您提供的正確網址 ★
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNHviKb9PNe3Ho-5JAf10hfsJkRusPT_oJS2rfP0i2US0AGs32ZbQAoYa3TaIzNdHsWPcEpqX1IcJ3/pub?gid=1615478278&single=true&output=csv"
# ==========================================

# 設定固定的 EPS (2025 全年)
FIXED_EPS = 66.25 

# 偽裝 Headers (用於 Investing.com)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7'
}

def get_google_sheet_data():
    """從 Google Sheets 讀取黃金、匯率、台積電"""
    print("📥 正在從 Google Sheets 讀取數據...")
    try:
        # 直接讀取您的 CSV 連結
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        
        # 簡單檢查格式：如果欄位不對，嘗試印出以利除錯
        if df.shape[1] < 2:
            print(f"⚠️ Google Sheet 格式警告: 讀取到的欄位過少 ({df.shape})")
            print(df.head())
            return {}

        # 轉成 Dictionary: { 'gold': 4685.5, ... }
        # 假設 A 欄是 Key (Item), B 欄是 Value
        data = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
        
        print("✅ Google Sheet 讀取成功！")
        # 印出部分數據確認
        for k, v in data.items():
            print(f"   - {k}: {v}")
            
        return data
    except Exception as e:
        print(f"❌ Google Sheet 讀取失敗: {e}")
        return {}

def get_investing_us10y():
    """備援：從 Investing.com 抓美債"""
    url = "https://hk.investing.com/rates-bonds/u.s.-10-year-bond-yield"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        match = re.search(r'data-test="instrument-price-last"[^>]*>([0-9\.]+)<', r.text)
        if match: return float(match.group(1))
    except: pass
    return None

def get_vix_from_yf():
    """備援：從 yfinance 抓 VIX"""
    try:
        ticker = yf.Ticker("^VIX")
        data = ticker.history(period="5d")
        if not data.empty: return round(data['Close'].iloc[-1], 2)
    except: pass
    return None

def get_fear_and_greed():
    try:
        r = requests.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata", headers=HEADERS, timeout=10)
        return int(r.json()['fear_and_greed']['score'])
    except: return None

if __name__ == "__main__":
    print("🚀 開始執行爬蟲 (v4.1 Correct URL)...")
    
    # 1. 抓取所有來源
    sheet_data = get_google_sheet_data()
    us_10y_val = get_investing_us10y()
    vix_val = get_vix_from_yf()
    cnn_score = get_fear_and_greed()
    
    # 2. 數據清洗與轉換
    def parse_val(val):
        try:
            # 處理 Google Sheet 可能傳回的字串 (例如 "31.5")
            return float(str(val).replace(',', ''))
        except:
            return 0.0

    tw_price = parse_val(sheet_data.get('2330_price', 0))
    gold_price = parse_val(sheet_data.get('gold', 0))
    usd_twd = parse_val(sheet_data.get('usd_twd', 0))
    
    # VIX 與 美債：Google Sheet 優先，抓不到才用爬蟲備援
    sheet_vix = parse_val(sheet_data.get('vix', 0))
    sheet_us10y = parse_val(sheet_data.get('us_10y', 0))
    
    final_vix = sheet_vix if sheet_vix > 0 else (vix_val if vix_val else 0)
    final_us10y = sheet_us10y if sheet_us10y > 0 else (us_10y_val if us_10y_val else 0)

    # 3. 讀取舊歷史 (繼承用)
    file_path = "data/history.json"
    history = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    last = history[-1] if history else {}

    # 4. 最終防呆繼承 (若所有來源都失敗，用昨日資料)
    if final_vix == 0: final_vix = last.get('vix', 0)
    if final_us10y == 0: final_us10y = last.get('us_10y', 0)
    if gold_price == 0: gold_price = last.get('gold', 0)
    if usd_twd == 0: usd_twd = last.get('usd_twd', 0)
    
    # 股價繼承 (為了算 PE)
    if tw_price == 0: tw_price = last.get('tw_pe', 0) * FIXED_EPS
    
    # PE 計算
    final_pe = round(tw_price / FIXED_EPS, 2) if tw_price > 0 else last.get('tw_pe', 0)
    final_cnn = cnn_score if cnn_score else last.get('cnn_score', 50)

    # 5. 組合與存檔
    final_entry = {
        "date": (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
        "cnn_score": final_cnn,
        "tw_pe": final_pe,
        "biz_score": 38,
        "vix": final_vix,
        "us_10y": final_us10y,
        "usd_twd": usd_twd,
        "gold": gold_price
    }

    history.append(final_entry)
    history = history[-20000:]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"✅ 更新完成！")
    print(f"   - Gold: {gold_price}")
    print(f"   - PE: {final_pe} (Price: {tw_price})")
    print(f"   - US10Y: {final_us10y}")
