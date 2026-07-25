#!/usr/bin/env python3
"""檢查緯穎 6669 今日 8 項進場條件逐項達成狀況"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

TICKER = '6669.TW'
MARKET = '^TWII'
RS_WIN = 20

stock_raw = yf.download(TICKER, period='3mo', progress=False, auto_adjust=False)
mkt_raw   = yf.download(MARKET, period='3mo', progress=False, auto_adjust=False)

def clean(raw):
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df.sort_index()

df  = clean(stock_raw)
mkt = clean(mkt_raw)
df = df[df['Volume'] > 0]
mkt = mkt[mkt['Volume'] > 0]

df['MA5']    = df['Close'].rolling(5).mean()
df['MA10']   = df['Close'].rolling(10).mean()
df['MA20']   = df['Close'].rolling(20).mean()
df['Vol3']   = df['Volume'].rolling(3).mean()
df['Vol5']   = df['Volume'].rolling(5).mean()
df['BH']     = df[['Open','Close']].max(axis=1)
df['Box5H']  = df['BH'].shift(1).rolling(5).max()

obv = [0]
for i in range(1, len(df)):
    if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
        obv.append(obv[-1] + df['Volume'].iloc[i])
    elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
        obv.append(obv[-1] - df['Volume'].iloc[i])
    else:
        obv.append(obv[-1])
df['OBV']    = pd.Series(obv, index=df.index)
df['OBV_MA'] = df['OBV'].rolling(5).mean()

df['StockRS'] = df['Close'] / df['Close'].shift(RS_WIN)
mkt['MktRS']  = mkt['Close'] / mkt['Close'].shift(RS_WIN)
df = df.join(mkt[['MktRS']], how='left')
df['MktRS'] = df['MktRS'].ffill()

# 最近 5 天的條件
print(f"\n{'='*75}")
print(f"  緯穎 (6669.TW) 近 5 日進場條件逐項檢查")
print(f"{'='*75}")

for offset in range(-4, 1):
    idx = len(df) + offset - 1
    if idx < RS_WIN + 5:
        continue
    row = df.iloc[idx]
    dt = df.index[idx].strftime('%Y-%m-%d')
    close = float(row['Close'])
    open_ = float(row['Open'])
    vol = float(row['Volume'])

    print(f"\n  📅 {dt}  開:{open_:.0f}  收:{close:.0f}  量:{vol:,.0f}")
    print(f"  {'-'*60}")

    c1 = vol > float(row['Vol3'])
    c2 = vol >= float(df['Volume'].iloc[idx-1]) * 1.2
    box5h = float(row['Box5H']) if not pd.isna(row['Box5H']) else 0
    c3 = close > box5h
    ma5 = float(row['MA5']); ma10 = float(row['MA10']); ma20 = float(row['MA20'])
    c4 = ma5 > ma10 > ma20
    c5 = close > ma20
    obv_val = float(row['OBV']); obv_ma = float(row['OBV_MA'])
    obv_5ago = float(df['OBV'].iloc[idx-5])
    c6 = obv_val > obv_ma and obv_val > obv_5ago
    stock_rs = float(row['StockRS']) if not pd.isna(row['StockRS']) else 0
    mkt_rs = float(row['MktRS']) if not pd.isna(row['MktRS']) else 0
    c7 = stock_rs > mkt_rs

    checks = [
        (c1, '量>3日均量', f'量={vol:,.0f} vs Vol3={float(row["Vol3"]):,.0f}'),
        (c2, '量加速×1.2', f'量={vol:,.0f} vs 前日×1.2={float(df["Volume"].iloc[idx-1])*1.2:,.0f}'),
        (c3, '突破Box5H', f'收盤={close:.0f} vs Box5H={box5h:.0f}'),
        (c4, '均線多頭排列', f'5MA={ma5:.0f} > 10MA={ma10:.0f} > 20MA={ma20:.0f}'),
        (c5, '站上月線', f'收盤={close:.0f} vs 20MA={ma20:.0f}'),
        (c6, 'OBV向上', f'OBV={obv_val:,.0f} vs MA5={obv_ma:,.0f}'),
        (c7, 'RS>大盤', f'個股={stock_rs:.4f} vs 大盤={mkt_rs:.4f}'),
    ]
    total = sum(c for c, _, _ in checks)
    for passed, label, detail in checks:
        print(f"    {'✅' if passed else '❌'} {label:<12} {detail}")
    
    emoji = '🟢' if total >= 7 else '🟡' if total >= 6 else '🔴'
    print(f"    {emoji} 達成: {total}/7{'  → 可進場！' if total >= 7 else ''}")
