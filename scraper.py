import requests
import json
import os
import pandas as pd
import yfinance as yf
import re
from datetime import datetime, timedelta, timezone

# ==========================================
# ★ 您的 Google Sheet CSV 網址 (維持不動) ★
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNHviKb9PNe3Ho-5JAf10hfsJkRusPT_oJS2rfP0i2US0AGs32ZbQAoYa3TaIzNdHsWPcEpqX1IcJ3/pub?gid=1615478278&single=true&output=csv"
# ==========================================

FIXED_EPS = 66.25 

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def parse_val(val):
    """
    數值解析器：
    1. 移除 $, %, , 等符號
    2. 強制四捨五入到小數點第 2 位
    """
    if val is None: return 0.0
    s = str(val).strip()
    s_clean = s.replace(',', '').replace('$', '').replace('%', '')
    match = re.search(r'-?\d+\.?\d*', s_clean)
    
    if match:
        try:
            # ★ 修改點 1: 在解析當下就先 Round 一次，確保 log 顯示也乾淨
            return round(float(match.group()), 2)
        except:
            pass
    return 0.0

def get_google_sheet_data_smart():
    print("📥 正在從 Google Sheets 讀取數據...")
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL, header=None)
        extracted_data = {}
        target_keys = ['gold', 'usd_twd', '2330_price', 'vix', 'us_10y']
        
        for r_idx, row in df.iterrows():
            for c_idx, cell_value in enumerate(row):
                val_str = str(cell_value).strip()
                if val_str in target_keys:
                    if c_idx + 1 < len(row):
                        target_val = row[c_idx + 1]
                        clean_val = parse_val(target_val)
                        print(f"   ✅ 找到 {val_str}: {clean_val}")
                        extracted_data[val_str] = clean_val
        return extracted_data
    except Exception as e:
        print(f"❌ Google Sheet 讀取失敗: {e}")
        return {}

def get_investing_us10y():
    # 備援用，維持不動
    try:
        url = "https://hk.investing.com/rates-bonds/u.s.-10-year-bond-yield"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        match = re.search(r'data-test="instrument-price-last"[^>]*>([0-9\.]+)<', r.text)
        if match: return round(float(match.group(1)), 2)
    except: pass
    return None

def get_vix_from_yf():
    # 備援用，維持不動
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

def get_tsmc_eps():
    print("🕵️ 正在從 Yahoo 抓取最新台積電 EPS...")
    try:
        ticker = yf.Ticker("2330.TW")
        # info 字典裡面的 trailingEps 就是近四季 EPS 總和
        eps = ticker.info.get('trailingEps')
        if eps and eps > 0:
            print(f"✅ 成功抓取最新 EPS: {eps}")
            return round(eps, 2)
    except Exception as e:
        print(f"⚠️ EPS 抓取失敗，使用預設值。錯誤: {e}")
        pass
    return 66.25 # 如果 Yahoo 當機，保底回傳這個數字

if __name__ == "__main__":
    print("🚀 開始執行爬蟲 (v5.0 Two-Decimal Enforcer)...")
    
    # 1. 抓取
    sheet_data = get_google_sheet_data_smart()
    us_10y_val = get_investing_us10y()
    vix_val = get_vix_from_yf()
    cnn_score = get_fear_and_greed()
    
    # 2. 取值
    tw_price = sheet_data.get('2330_price', 0)
    gold_price = sheet_data.get('gold', 0)
    usd_twd = sheet_data.get('usd_twd', 0)
    sheet_vix = sheet_data.get('vix', 0)
    sheet_us10y = sheet_data.get('us_10y', 0)
    
    # 3. 備援邏輯
    final_vix = sheet_vix if sheet_vix > 0 else (vix_val if vix_val else 0)
    final_us10y = sheet_us10y if sheet_us10y > 0 else (us_10y_val if us_10y_val else 0)

    # 4. 讀取與繼承
    file_path = "data/history.json"
    history = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    last = history[-1] if history else {}

    if final_vix == 0: final_vix = last.get('vix', 0)
    if final_us10y == 0: final_us10y = last.get('us_10y', 0)
    if gold_price == 0: gold_price = last.get('gold', 0)
    if usd_twd == 0: usd_twd = last.get('usd_twd', 0)
    if tw_price == 0: tw_price = last.get('tw_pe', 0) * FIXED_EPS
    
    final_pe = round(tw_price / FIXED_EPS, 2) if tw_price > 0 else last.get('tw_pe', 0)
    final_cnn = cnn_score if cnn_score else last.get('cnn_score', 50)

    # 5. ★ 修改點 2: 最終存檔前的強制整形 ★
    # 這裡的 round(x, 2) 是最後一道防線，保證寫入 JSON 的永遠只有兩位小數
    final_entry = {
        "date": (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
        "cnn_score": final_cnn, # 整數不用 round
        "tw_pe": round(final_pe, 2),
        "biz_score": 38,
        "vix": round(final_vix, 2),
        "us_10y": round(final_us10y, 2),
        "usd_twd": round(usd_twd, 2),
        "gold": round(gold_price, 2)
    }

    history.append(final_entry)
    history = history[-20000:]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"✅ 更新完成 (格式已統一)！")
    print(f"   - Gold: {final_entry['gold']}")
    print(f"   - PE: {final_entry['tw_pe']}")
    print(f"   - US10Y: {final_entry['us_10y']}")
