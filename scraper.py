import requests
import json
import os
import pandas as pd
import yfinance as yf
import re
from datetime import datetime, timedelta, timezone

# ==========================================
# ★ 您的 Google Sheet CSV 網址 ★
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNHviKb9PNe3Ho-5JAf10hfsJkRusPT_oJS2rfP0i2US0AGs32ZbQAoYa3TaIzNdHsWPcEpqX1IcJ3/pub?gid=1615478278&single=true&output=csv"
# ==========================================

# 設定固定的 EPS (2025 全年)
FIXED_EPS = 66.25 

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7'
}

def parse_val(val):
    """
    ★ 核心修正：超強效數字提取器 ★
    能處理: "$4,774.70", "4.25 (備註)", "16.35%", "N/A"
    """
    if val is None: return 0.0
    
    # 1. 轉成字串
    s = str(val).strip()
    
    # 2. 先移除絕對會干擾的符號 (逗號, 美元, 百分比)
    #    這樣 4,774.70 會變成 4774.70
    s_clean = s.replace(',', '').replace('$', '').replace('%', '')
    
    # 3. 使用 Regex 抓取「字串中的第一個數字」
    #    \d+   : 數字
    #    \.?   : 可能有小數點
    #    \d* : 小數點後的數字
    match = re.search(r'-?\d+\.?\d*', s_clean)
    
    if match:
        try:
            return float(match.group())
        except:
            pass
            
    return 0.0

def get_google_sheet_data_smart():
    print("📥 正在從 Google Sheets 讀取數據 (Smart Mode)...")
    try:
        # header=None 讀取所有內容
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL, header=None)
        
        extracted_data = {}
        # 注意: 您的 Google Sheet 裡的 Key 似乎是小寫，這裡要對應
        target_keys = ['gold', 'usd_twd', '2330_price', 'vix', 'us_10y']
        
        # 遍歷尋找
        for r_idx, row in df.iterrows():
            for c_idx, cell_value in enumerate(row):
                val_str = str(cell_value).strip()
                
                if val_str in target_keys:
                    # 找到 Key，抓右邊那格
                    if c_idx + 1 < len(row):
                        target_val = row[c_idx + 1]
                        # ★ 立即在此處解析並印出結果，方便除錯 ★
                        clean_val = parse_val(target_val)
                        print(f"   ✅ 找到 {val_str}: 原文='{target_val}' -> 解析={clean_val}")
                        extracted_data[val_str] = clean_val
        
        return extracted_data

    except Exception as e:
        print(f"❌ Google Sheet 讀取失敗: {e}")
        return {}

def get_investing_us10y():
    url = "https://hk.investing.com/rates-bonds/u.s.-10-year-bond-yield"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        match = re.search(r'data-test="instrument-price-last"[^>]*>([0-9\.]+)<', r.text)
        if match: return float(match.group(1))
    except: pass
    return None

def get_vix_from_yf():
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
    print("🚀 開始執行爬蟲 (v4.3 Robust Parser)...")
    
    # 1. 抓取資料
    sheet_data = get_google_sheet_data_smart()
    us_10y_val = get_investing_us10y()
    vix_val = get_vix_from_yf()
    cnn_score = get_fear_and_greed()
    
    # 2. 取值 (因為 sheet_data 裡面的值已經被 clean 過了，直接拿即可)
    tw_price = sheet_data.get('2330_price', 0)
    gold_price = sheet_data.get('gold', 0)
    usd_twd = sheet_data.get('usd_twd', 0)
    sheet_vix = sheet_data.get('vix', 0)
    sheet_us10y = sheet_data.get('us_10y', 0)
    
    # 3. 備援邏輯
    final_vix = sheet_vix if sheet_vix > 0 else (vix_val if vix_val else 0)
    final_us10y = sheet_us10y if sheet_us10y > 0 else (us_10y_val if us_10y_val else 0)

    # 4. 讀取歷史
    file_path = "data/history.json"
    history = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    last = history[-1] if history else {}

    # 5. 最終防呆繼承
    if final_vix == 0: final_vix = last.get('vix', 0)
    if final_us10y == 0: final_us10y = last.get('us_10y', 0)
    if gold_price == 0: gold_price = last.get('gold', 0)
    if usd_twd == 0: usd_twd = last.get('usd_twd', 0)
    if tw_price == 0: tw_price = last.get('tw_pe', 0) * FIXED_EPS
    
    final_pe = round(tw_price / FIXED_EPS, 2) if tw_price > 0 else last.get('tw_pe', 0)
    final_cnn = cnn_score if cnn_score else last.get('cnn_score', 50)

    # 6. 存檔
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
    print(f"   - USD/TWD: {usd_twd}")
