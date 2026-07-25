#!/usr/bin/env python3
"""
族群 RS 強弱分析 — 掃描觀察清單各族群相對大盤的 20 日強弱度
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from engine import TICKER_MAP

# ── 族群分類 ──
SECTORS = {
    'AI 晶片/IC 設計': ['聯發科', '創意', '世芯KY', '群聯', '祥碩', '力智', '凌通', '盛群', '松翰'],
    '半導體設備/材料': ['辛耘', '環球晶', '力積電'],
    'AI 散熱/機構件': ['奇鋐', '順達'],
    'AI 伺服器/網通': ['智邦', '光寶科', '微星', '事欣科'],
    'PCB/載板/CCL': ['台光電', '台燿', '臻鼎KY', '金像電', '華通', '聯茂', '金居', '欣銓'],
    '連接器/線束': ['貿聯KY'],
    '記憶體': ['南亞科', '南亞'],
    '被動元件/模組': ['晶技'],
}

RS_WIN = 20
MARKET = '^TWII'

def clean(raw):
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df.sort_index()

# ── 下載大盤 ──
print("下載大盤數據...", file=sys.stderr)
mkt_raw = yf.download(MARKET, period='3mo', progress=False, auto_adjust=False)
mkt = clean(mkt_raw)
mkt = mkt[mkt['Volume'] > 0]
mkt_rs = float(mkt['Close'].iloc[-1]) / float(mkt['Close'].iloc[-RS_WIN]) if len(mkt) > RS_WIN else 1.0
mkt_ret_20d = (mkt_rs - 1) * 100
mkt_today = float(mkt['Close'].pct_change().iloc[-1] * 100)
mkt_close = float(mkt['Close'].iloc[-1])

print(f"\n{'='*70}")
print(f"  族群 RS 強弱分析  資料日期: {mkt.index[-1].strftime('%m/%d')}")
print(f"  大盤 ^TWII 收盤: {mkt_close:,.0f}  20日漲幅: {mkt_ret_20d:+.2f}%  今日: {mkt_today:+.2f}%")
print(f"{'='*70}\n")

# ── 下載所有個股 ──
all_stocks = set()
for names in SECTORS.values():
    all_stocks.update(names)

stock_data = {}
print("下載個股數據...", file=sys.stderr)
for name in sorted(all_stocks):
    ticker = TICKER_MAP.get(name)
    if not ticker:
        continue
    try:
        raw = yf.download(ticker, period='3mo', progress=False, auto_adjust=False)
        if raw.empty or len(raw) < RS_WIN + 1:
            continue
        df = clean(raw)
        df = df[df['Volume'] > 0]
        if len(df) < RS_WIN + 1:
            continue
        
        close_now = float(df['Close'].iloc[-1])
        close_20d = float(df['Close'].iloc[-RS_WIN])
        stock_rs = close_now / close_20d
        stock_ret = (stock_rs - 1) * 100
        today_ret = float(df['Close'].pct_change().iloc[-1] * 100)
        
        # MA20 判斷
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        above_ma20 = close_now > ma20
        
        stock_data[name] = {
            'ticker': ticker,
            'close': close_now,
            'rs': stock_rs,
            'ret_20d': stock_ret,
            'today_ret': today_ret,
            'above_ma20': above_ma20,
            'stronger': stock_rs > mkt_rs,
        }
    except Exception as e:
        print(f"  {name} 失敗: {e}", file=sys.stderr)

# ── 族群分析 ──
sector_results = []

for sector, names in SECTORS.items():
    members = []
    for name in names:
        if name in stock_data:
            members.append((name, stock_data[name]))
    
    if not members:
        continue
    
    avg_rs = sum(d['ret_20d'] for _, d in members) / len(members)
    strong_count = sum(1 for _, d in members if d['stronger'])
    above_ma20_count = sum(1 for _, d in members if d['above_ma20'])
    avg_today = sum(d['today_ret'] for _, d in members) / len(members)
    
    sector_results.append({
        'sector': sector,
        'avg_ret_20d': avg_rs,
        'excess_rs': avg_rs - mkt_ret_20d,
        'strong_ratio': f"{strong_count}/{len(members)}",
        'strong_count': strong_count,
        'total': len(members),
        'above_ma20': f"{above_ma20_count}/{len(members)}",
        'avg_today': avg_today,
        'members': members,
    })

# 按超額 RS 排序
sector_results.sort(key=lambda x: x['excess_rs'], reverse=True)

# ── 輸出 ──
print(f"{'族群':<20} {'20日漲幅':>8} {'超額RS':>8} {'RS>大盤':>8} {'站上月線':>8} {'今日':>6}")
print(f"{'-'*70}")

for s in sector_results:
    emoji = '🟢' if s['excess_rs'] > 0 else '🔴'
    print(f"{emoji} {s['sector']:<18} {s['avg_ret_20d']:>+7.2f}% {s['excess_rs']:>+7.2f}% {s['strong_ratio']:>8} {s['above_ma20']:>8} {s['avg_today']:>+5.2f}%")

# ── 各族群明細 ──
for s in sector_results:
    emoji = '🟢' if s['excess_rs'] > 0 else '🔴'
    print(f"\n{emoji} {s['sector']}  (族群平均超額RS: {s['excess_rs']:+.2f}%)")
    print(f"  {'個股':<10} {'代碼':<10} {'收盤':>8} {'20日漲幅':>8} {'vs大盤':>8} {'月線':>4} {'今日':>6}")
    print(f"  {'-'*60}")
    
    # 按 RS 排序
    sorted_members = sorted(s['members'], key=lambda x: x[1]['ret_20d'], reverse=True)
    for name, d in sorted_members:
        rs_icon = '✅' if d['stronger'] else '❌'
        ma_icon = '📈' if d['above_ma20'] else '📉'
        ticker_short = d['ticker'].replace('.TW', '').replace('.TWO', 'O')
        print(f"  {rs_icon} {name:<8} {ticker_short:<10} {d['close']:>8.1f} {d['ret_20d']:>+7.2f}% {d['ret_20d']-mkt_ret_20d:>+7.2f}% {ma_icon}  {d['today_ret']:>+5.2f}%")

# ── 總結 ──
strong_sectors = [s for s in sector_results if s['excess_rs'] > 0]
weak_sectors = [s for s in sector_results if s['excess_rs'] <= 0]

print(f"\n{'='*70}")
print(f"  📊 總結")
print(f"{'='*70}")

if strong_sectors:
    print(f"\n  🟢 強於大盤的族群 ({len(strong_sectors)} 個):")
    for s in strong_sectors:
        top_stocks = sorted(s['members'], key=lambda x: x[1]['ret_20d'], reverse=True)
        top_names = ', '.join(f"{n}({d['ret_20d']:+.1f}%)" for n, d in top_stocks[:3])
        print(f"     {s['sector']:<20} 超額RS {s['excess_rs']:+.2f}%  領頭: {top_names}")
else:
    print(f"\n  ⚠️ 目前沒有族群整體強於大盤！")

if weak_sectors:
    print(f"\n  🔴 弱於大盤的族群 ({len(weak_sectors)} 個):")
    for s in weak_sectors:
        print(f"     {s['sector']:<20} 超額RS {s['excess_rs']:+.2f}%")

# 個股 RS 排名 Top 10
print(f"\n  🏆 個股 RS 排名 Top 10:")
all_sorted = sorted(stock_data.items(), key=lambda x: x[1]['ret_20d'], reverse=True)
for i, (name, d) in enumerate(all_sorted[:10], 1):
    rs_icon = '✅' if d['stronger'] else '❌'
    ma_icon = '📈' if d['above_ma20'] else '📉'
    sector_name = next((s for s, names in SECTORS.items() if name in names), '?')
    print(f"     {i:>2}. {rs_icon} {name:<8} {d['ret_20d']:>+7.2f}% {ma_icon}  ({sector_name})")
