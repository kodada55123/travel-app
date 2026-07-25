#!/usr/bin/env python3
"""
美股持股同步腳本
從 us_backtest/config.py 讀取 Firstrade 美股持股與現金餘額，
抓取即時美股價格與 USD/TWD 匯率，
並更新 trading/data.js 中的 US_POSITIONS、US_CASH、USD_TWD、LAST_UPDATED 與 DATA_TS。
"""
import os
import re
import json
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_DIR = os.path.dirname(BASE_DIR)
US_CONFIG_PATH = os.path.join(GOOGLE_DIR, 'us_backtest', 'config.py')
DATA_JS_PATH = os.path.join(BASE_DIR, 'data.js')

sys.path.insert(0, os.path.join(GOOGLE_DIR, 'us_backtest'))

try:
    from config import HOLDINGS, CFG
except ImportError:
    print("❌ 無法從 us_backtest/config.py 載入 HOLDINGS / CFG")
    sys.exit(1)

us_cash = CFG.get('CASH_BALANCE', 1504.81)

print(f"📦 讀取到 {len(HOLDINGS)} 檔美股持股，現金餘額: ${us_cash:,.2f} USD...")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 抓取 USD/TWD 匯率
usd_twd = 32.34
try:
    url_rate = 'https://query1.finance.yahoo.com/v8/finance/chart/USDTWD=X'
    req_rate = urllib.request.Request(url_rate, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_rate, context=ctx, timeout=5) as r:
        d_rate = json.loads(r.read().decode('utf-8'))
        usd_twd = round(d_rate['chart']['result'][0]['meta']['regularMarketPrice'], 2)
except Exception as e:
    print(f"⚠️ 無法取得 USD/TWD 匯率，使用預設值 32.34: {e}")

print(f"💱 當前 USD/TWD 匯率: {usd_twd}")

us_positions = []
total_val = 0
total_cost = 0

for code, info in HOLDINGS.items():
    shares = info['shares']
    avg_cost = info['cost']
    name = info['name']
    pos_type = 'ETF' if 'ETF' in name or code == 'QQQ' else '股票'
    
    # 抓取即時價格
    price = avg_cost
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            d = json.loads(r.read().decode('utf-8'))
            price = d['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception as e:
        print(f"⚠️ {code} 無法取得即時價格，使用成本估算: {e}")

    val = round(shares * price, 2)
    cost_sum = round(shares * avg_cost, 2)
    pnl = round(val - cost_sum, 2)
    pct = round((price - avg_cost) / avg_cost * 100, 2)
    
    total_val += val
    total_cost += cost_sum

    us_positions.append({
        'stock': name,
        'code': code,
        'type': pos_type,
        'shares': shares,
        'avgCost': avg_cost,
        'price': price,
        'value': val,
        'pnl': pnl,
        'pct': pct,
        'currency': 'USD'
    })

total_account_us = round(total_val + us_cash, 2)
total_us_twd = round(total_account_us * usd_twd)
print(f"💵 美股持股市值: ${total_val:,.2f} USD | 現金餘額: ${us_cash:,.2f} USD | 美股總資產: ${total_account_us:,.2f} USD (折合 NT$ {total_us_twd:,})")

# 讀取現有 data.js
with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# 升級時間戳
now_utc = datetime.now(timezone.utc)
today_str = now_utc.strftime('%Y-%m-%d')
iso_ts = now_utc.isoformat()

content = re.sub(r'const LAST_UPDATED = ".*?";', f'const LAST_UPDATED = "{today_str}";', content)
content = re.sub(r'const DATA_TS = ".*?";', f'const DATA_TS = "{iso_ts}";', content)

if 'const US_CASH =' in content:
    content = re.sub(r'const US_CASH = [\d.]+;', f'const US_CASH = {us_cash};', content)
else:
    content = content.replace('const LAST_UPDATED =', f'const US_CASH = {us_cash};\nconst LAST_UPDATED =')

if 'const USD_TWD =' in content:
    content = re.sub(r'const USD_TWD = [\d.]+;', f'const USD_TWD = {usd_twd};', content)
else:
    content = content.replace('const LAST_UPDATED =', f'const USD_TWD = {usd_twd};\nconst LAST_UPDATED =')

# 格式化 US_POSITIONS JS 程式碼
js_lines = ["const US_POSITIONS = ["]
for item in us_positions:
    line = f'  {{ stock:"{item["stock"]}", code:"{item["code"]}", type:"{item["type"]}", shares:{item["shares"]}, avgCost:{item["avgCost"]}, price:{item["price"]}, value:{item["value"]}, pnl:{item["pnl"]}, pct:{item["pct"]}, currency:"USD" }},'
    js_lines.append(line)
js_lines.append("];")
js_code = "\n".join(js_lines)

if 'const US_POSITIONS =' in content:
    content = re.sub(r'const US_POSITIONS = \[.*?\];', js_code, content, flags=re.DOTALL)
else:
    content = content.replace('const POSITIONS = [', f'{js_code}\n\nconst POSITIONS = [')

with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ 成功將美股持股、現金 (${us_cash:,.2f}) 與匯率 ({usd_twd}) 同步至 trading/data.js！")
