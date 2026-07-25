#!/usr/bin/env python3
"""檢查指定日期 3665 的 8 項進場條件逐項達成狀況"""
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

TICKER = '3665.TW'
MARKET = '^TWII'
RS_WIN = 20

# 下載數據（多抓前面做均線暖機）
stock_raw = yf.download(TICKER, start='2026-05-01', end='2026-07-25', progress=False, auto_adjust=False)
mkt_raw   = yf.download(MARKET, start='2026-05-01', end='2026-07-25', progress=False, auto_adjust=False)

def clean(raw):
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df.sort_index()

df  = clean(stock_raw)
mkt = clean(mkt_raw)

# 過濾零成交量
df = df[df['Volume'] > 0]

# 計算指標
df['MA5']    = df['Close'].rolling(5).mean()
df['MA10']   = df['Close'].rolling(10).mean()
df['MA20']   = df['Close'].rolling(20).mean()
df['Vol3']   = df['Volume'].rolling(3).mean()
df['Vol5']   = df['Volume'].rolling(5).mean()
df['BH']     = df[['Open','Close']].max(axis=1)
df['Box5H']  = df['BH'].shift(1).rolling(5).max()

# OBV
obv = [0]
for i in range(1, len(df)):
    if   df['Close'].iloc[i] > df['Close'].iloc[i-1]: obv.append(obv[-1] + df['Volume'].iloc[i])
    elif df['Close'].iloc[i] < df['Close'].iloc[i-1]: obv.append(obv[-1] - df['Volume'].iloc[i])
    else: obv.append(obv[-1])
df['OBV']    = pd.Series(obv, index=df.index)
df['OBV_MA'] = df['OBV'].rolling(5).mean()

# RS
df['StockRS'] = df['Close'] / df['Close'].shift(RS_WIN)
mkt['MktRS']  = mkt['Close'] / mkt['Close'].shift(RS_WIN)
df = df.join(mkt[['MktRS']], how='left')
df['MktRS'] = df['MktRS'].ffill()

# 檢查指定日期
for check_date in ['2026-07-22', '2026-07-23', '2026-07-24']:
    matches = df[df.index.strftime('%Y-%m-%d') == check_date]
    if matches.empty:
        print(f"\n{'='*60}")
        print(f"  {check_date}：無交易資料（可能為假日）")
        continue

    row = matches.iloc[0]
    close = float(row['Close'])
    open_ = float(row['Open'])
    vol   = float(row['Volume'])
    
    print(f"\n{'='*60}")
    print(f"  貿聯KY (3665)  日期: {check_date}")
    print(f"  開盤: {open_:.1f}  收盤: {close:.1f}  成交量: {vol:,.0f}")
    print(f"{'='*60}")
    
    c1 = vol > float(row['Vol3'])
    print(f"  {'✅' if c1 else '❌'} ① 量能放大     量={vol:,.0f} vs Vol3={float(row['Vol3']):,.0f}")
    
    idx = df.index.get_loc(matches.index[0])
    prev_vol = float(df['Volume'].iloc[idx-1]) if idx > 0 else 0
    c2 = vol >= prev_vol * 1.2
    print(f"  {'✅' if c2 else '❌'} ② 量能加速     量={vol:,.0f} vs 前日量×1.2={prev_vol*1.2:,.0f}")
    
    box5h = float(row['Box5H']) if not pd.isna(row['Box5H']) else 0
    c3 = close > box5h
    print(f"  {'✅' if c3 else '❌'} ③ 突破Box5H    收盤={close:.1f} vs Box5H={box5h:.1f}")
    
    ma5  = float(row['MA5'])
    ma10 = float(row['MA10'])
    ma20 = float(row['MA20'])
    c4 = ma5 > ma10 > ma20
    print(f"  {'✅' if c4 else '❌'} ④ 均線多頭排列  5MA={ma5:.1f} > 10MA={ma10:.1f} > 20MA={ma20:.1f}")
    
    c5 = close > ma20
    print(f"  {'✅' if c5 else '❌'} ⑤ 站上月線     收盤={close:.1f} vs 20MA={ma20:.1f}")
    
    obv_val  = float(row['OBV'])
    obv_ma   = float(row['OBV_MA'])
    obv_5ago = float(df['OBV'].iloc[idx-5]) if idx >= 5 else 0
    c6 = obv_val > obv_ma and obv_val > obv_5ago
    print(f"  {'✅' if c6 else '❌'} ⑥ OBV向上      OBV={obv_val:,.0f} vs MA5={obv_ma:,.0f}, 5日前={obv_5ago:,.0f}")
    
    stock_rs = float(row['StockRS']) if not pd.isna(row['StockRS']) else 0
    mkt_rs   = float(row['MktRS'])   if not pd.isna(row['MktRS'])   else 0
    c7 = stock_rs > mkt_rs
    print(f"  {'✅' if c7 else '❌'} ⑦ RS強於大盤   個股RS={stock_rs:.4f} vs 大盤RS={mkt_rs:.4f}")
    
    total = sum([c1, c2, c3, c4, c5, c6, c7])
    print(f"\n  📊 達成: {total}/7 項（第⑧項為實體上漲，含在③中）")
    
    if total >= 7:
        print(f"  🟢 全部達成 → 可進場！")
    else:
        print(f"  🔴 未達全部條件 → 不可進場")
