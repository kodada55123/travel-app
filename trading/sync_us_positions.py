#!/usr/bin/env python3
"""
美股持股同步腳本
從 us_backtest/config.py 讀取 Firstrade 美股持股，
並更新 trading/data.js 中的 US_POSITIONS。
"""
import os
import re
import json
import ssl
import sys
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_DIR = os.path.dirname(BASE_DIR)
US_CONFIG_PATH = os.path.join(GOOGLE_DIR, 'us_backtest', 'config.py')
DATA_JS_PATH = os.path.join(BASE_DIR, 'data.js')

sys.path.insert(0, os.path.join(GOOGLE_DIR, 'us_backtest'))

try:
    from config import HOLDINGS
except ImportError:
    print("❌ 無法從 us_backtest/config.py 載入 HOLDINGS")
    sys.exit(1)

print(f"📦 讀取到 {len(HOLDINGS)} 檔美股持股...")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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

print(f"💵 美股持股總市值: ${total_val:,.2f} USD, 總損益: ${total_val - total_cost:+,.2f} USD")

# 讀取現有 data.js
with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# 格式化 US_POSITIONS JS 程式碼
js_lines = ["const US_POSITIONS = ["]
for item in us_positions:
    line = f'  {{ stock:"{item["stock"]}", code:"{item["code"]}", type:"{item["type"]}", shares:{item["shares"]}, avgCost:{item["avgCost"]}, price:{item["price"]}, value:{item["value"]}, pnl:{item["pnl"]}, pct:{item["pct"]}, currency:"USD" }},'
    js_lines.append(line)
js_lines.append("];")
js_code = "\n".join(js_lines)

# 若 data.js 中已存在 US_POSITIONS 則替換，否則加在 POSITIONS 之後
if 'const US_POSITIONS =' in content:
    content = re.sub(r'const US_POSITIONS = \[.*?\];', js_code, content, flags=re.DOTALL)
else:
    content = content.replace('const POSITIONS = [', f'{js_code}\n\nconst POSITIONS = [')

with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 成功將美股持股同步至 trading/data.js！")
