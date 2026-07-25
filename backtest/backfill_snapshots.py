#!/usr/bin/env python3
"""
淨值歷史回填 — 從交易紀錄反推每週持股，配合歷史收盤價重建資產曲線

方法：
  由「目前持股」往回走每筆交易（買進→減股數、賣出→加股數），
  跨過股票分割日時除以分割比（處理 0050 一拆四），
  得到任一日期的持股表，乘上該日未調整收盤價 = 當日淨值。
  ticker 無法解析的股票（界霖等）以其成交均價近似。

輸出：SNAPSHOTS 的 JS 陣列 → /tmp/snapshots.js
"""
import json
import re
import sys
import os
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import yfinance as yf  # noqa: E402
import pandas as pd  # noqa: E402
from engine import TICKER_MAP  # noqa: E402

DATA = open(os.path.expanduser('~/Desktop/trading/data.js')).read()


def parse_block(name):
    m = re.search(rf'const {name} = \[(.*?)\n\];', DATA, re.S)
    items = []
    for line in m.group(1).split('\n'):
        line = line.strip().rstrip(',')
        if not line.startswith('{'):
            continue
        obj = {}
        for key, val in re.findall(r'(\w+):("(?:[^"\\]|\\.)*"|-?[\d.]+)', line):
            obj[key] = json.loads(val) if val.startswith('"') else float(val)
        items.append(obj)
    return items


positions = parse_block('POSITIONS')
trades = parse_block('TRADES')

# ── ticker 解析：ETF 用代號，股票查 TICKER_MAP ──
def get_ticker(stock, code=None):
    if code and code not in ('—', '?'):
        c = str(code)
        if c.isdigit() or c.startswith('00'):
            return f'{c}.TW'
    name = stock.replace('-', '').replace('*', '')
    return TICKER_MAP.get(name)


code_by_stock = {p['stock']: p.get('code') for p in positions}
all_stocks = sorted({t['stock'] for t in trades} | {p['stock'] for p in positions})
tickers, approx = {}, {}
for s in all_stocks:
    tk = get_ticker(s, code_by_stock.get(s))
    if tk:
        tickers[s] = tk
    else:
        # 近似價：用該股所有成交均價
        ts = [t for t in trades if t['stock'] == s]
        approx[s] = sum(t['price'] * t['shares'] for t in ts) / sum(t['shares'] for t in ts)
print(f'ticker 解析 {len(tickers)} 檔；近似價 {len(approx)} 檔: {list(approx)}', file=sys.stderr)

# ── 下載歷史價（未調整）與分割 ──
START = '2024-12-25'
closes, splits = {}, {}
for s, tk in tickers.items():
    try:
        h = yf.Ticker(tk).history(start=START, auto_adjust=False)
        if h.empty:
            approx[s] = sum(t['price'] * t['shares'] for t in trades if t['stock'] == s) / \
                        max(1, sum(t['shares'] for t in trades if t['stock'] == s))
            print(f'  無價格 {s}（{tk}）→ 改用近似價', file=sys.stderr)
            continue
        h.index = h.index.tz_localize(None)
        closes[s] = h['Close']
        sp = h['Stock Splits'][h['Stock Splits'] > 0]
        if len(sp):
            splits[s] = [(d.strftime('%Y-%m-%d'), float(r)) for d, r in sp.items()]
            print(f'  分割 {s}: {splits[s]}', file=sys.stderr)
    except Exception as e:
        print(f'  {s} 失敗 {e}', file=sys.stderr)

# ── 事件表（交易 + 分割），依日期由新到舊 ──
cur_shares = {p['stock']: p['shares'] for p in positions}
events = []
for t in trades:
    delta = t['shares'] if t['action'] == 'BUY' else -t['shares']
    events.append((t['date'], 'trade', t['stock'], delta))
# yfinance 缺漏的分割手動補：0050 於 2025-06-18 一拆四
splits.setdefault('元大台灣50', []).append(('2025-06-18', 4.0))
for s, sps in splits.items():
    for d, r in sps:
        events.append((d, 'split', s, r))
events.sort(key=lambda e: e[0], reverse=True)


def shares_at(d):
    sh = dict(cur_shares)
    for ed, kind, s, v in events:
        if ed <= d:
            break
        if kind == 'trade':
            sh[s] = sh.get(s, 0) - v
        else:
            sh[s] = sh.get(s, 0) / v
    return {s: round(v) for s, v in sh.items() if round(v) != 0}


def price_at(s, d):
    if s in closes:
        ser = closes[s][closes[s].index <= pd.Timestamp(d)]
        if len(ser):
            return float(ser.iloc[-1])
    return approx.get(s, 0)


# ── 每週五 + 今天 ──
d = date(2025, 1, 3)
snap_dates = []
while d <= date.today():
    snap_dates.append(d.isoformat())
    d += timedelta(days=7)
if snap_dates[-1] != date.today().isoformat():
    snap_dates.append(date.today().isoformat())

rows = []
for sd in snap_dates:
    sh = shares_at(sd)
    val = sum(cnt * price_at(s, sd) for s, cnt in sh.items())
    rows.append((sd, round(val)))
    print(f'{sd}  {round(val):>12,}', file=sys.stderr)

js = 'const SNAPSHOTS = [\n' + '\n'.join(
    f'  {{ date:"{d}", value:{v} }},' for d, v in rows) + '\n];\n'
open('/tmp/snapshots.js', 'w').write(js)
print(f'\n✅ {len(rows)} 筆快照 → /tmp/snapshots.js', file=sys.stderr)
