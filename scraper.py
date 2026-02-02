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

def get_google_sheet_data_smart():
    """
    智慧讀取版：
    不再依賴固定欄位 (A, B)，而是搜尋 'key' 在哪裡，然後抓取它右邊的值。
    """
    print("📥 正在從 Google Sheets 讀取數據 (Smart Mode)...")
    try:
        # header=None 代表不把第一行當標題，讀取所有原始數據
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL, header=None)
        
        # 將所有資料轉為字串，方便搜尋
        df_str = df.astype(str)
        
        extracted_data = {}
        target_keys = ['gold', 'usd_twd', '2330_price', 'vix', 'us_10y']
        
        print("🔍 原始資料預覽 (前3列):")
        print(df.head(3)) 

        # 暴力搜尋法：遍歷每一個儲存格
        # 只要找到關鍵字，就抓它「右邊那一格」
        for r_idx, row in df.iterrows():
            for c_idx, cell_value in enumerate(row):
                # 轉成字串並去除空白
                val_str = str(cell_value).strip()
                
                if val_str in target_keys:
                    # 找到了 Key！檢查右邊有沒有值
                    if c_idx + 1 < len(row):
                        target_val = row[c_idx + 1]
                        print(f"   ✅ 找到 {val_str}: {target_val}")
                        extracted_data[val_str] = target_val
        
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
    print("🚀 開始執行爬蟲 (v4.2 Smart Search)...")
    
    # 1. 抓取資料
    sheet_data = get_google_sheet_data_smart()
    us_10y_val = get_investing_us10y()
    vix_val = get_vix_from_yf()
    cnn_score = get_fear_and_greed()
    
    # 2. 數據清洗
    def parse_val(val):
        try:
            return float(str(val).replace(',', '').strip())
        except:
            return 0.0

    tw_price = parse_val(sheet_data.get('2330_price', 0))
    gold_price = parse_val(sheet_data.get('gold', 0))
    usd_twd = parse_val(sheet_data.get('usd_twd', 0))
    
    # VIX 與 美債：Google Sheet 優先 -> 爬蟲備援
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

    # 4. 最終防呆繼承
    if final_vix == 0: final_vix = last.get('vix', 0)
    if final_us10y == 0: final_us10y = last.get('us_10y', 0)
    if gold_price == 0: gold_price = last.get('gold', 0)
    if usd_twd == 0: usd_twd = last.get('usd_twd', 0)
    
    # 股價繼承
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
    print(f"   - USD/TWD: {usd_twd}")
