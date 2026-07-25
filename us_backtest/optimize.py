#!/usr/bin/env python3
"""
進階美股策略優化測試腳本
測試項目：
1. 大盤大趨勢濾網 (S&P 500 > 50EMA 或 200SMA 時才允許開新倉)
2. 停損保護門檻 (-8% vs -10% vs -12%)
3. 箱形突破週期 (Box 5d vs 10d vs 15d)
"""
import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine
from config import HOLDINGS, WATCHLIST, CFG

# 擴充 engine 支援大盤多頭濾網
def prepare_with_mkt_filter(ticker, start='2019-01-01', end=None, mkt_filter_ema=50):
    df = engine.prepare(ticker, start=start, end=end)
    if df is None: return None
    
    # 取得大盤資料
    mkt = engine.get_market(start, end if end else '2026-07-25')
    mkt['MktEMA'] = mkt['Close'].ewm(span=mkt_filter_ema, adjust=False).mean()
    mkt['MktBull'] = mkt['Close'] > mkt['MktEMA']
    
    df = df.join(mkt[['MktBull']], how='left')
    
    # 加上大盤濾網
    df['Sig_Filtered'] = df['Sig'] & (df['MktBull'] == True)
    return df

def run_custom(df, ys, ye, hard_sl=-0.10, use_mkt_filter=False):
    # 替換硬停損
    orig_sl = engine.CFG['HARD_SL']
    engine.CFG['HARD_SL'] = hard_sl
    
    if use_mkt_filter and 'Sig_Filtered' in df.columns:
        # 暫時替換 Sig
        orig_sig = df['Sig'].copy()
        df['Sig'] = df['Sig_Filtered']
        res = engine.run(df, ys, ye, stop_mode='fixed')
        df['Sig'] = orig_sig
    else:
        res = engine.run(df, ys, ye, stop_mode='fixed')
        
    engine.CFG['HARD_SL'] = orig_sl
    return res

def test_advance_optimizations():
    target_stocks = ['NVDA', 'META', 'GOOGL', 'AAPL', 'MSFT', 'AVGO', 'MU', 'QQQ']
    years = [2023, 2024, 2025, 2026]
    
    print("=" * 85)
    print("【進階優化測試：A/B級龍頭組合 (2023 ~ 2026)】")
    print("=" * 85)
    
    results = []
    
    # 測試1: 停損幅度的影響 (-8% vs -10% vs -12%)
    for sl in [-0.08, -0.10, -0.12]:
        all_trades = []
        for t in target_stocks:
            df = prepare_with_mkt_filter(t, end='2026-07-25')
            if df is None: continue
            for yr in years:
                res = run_custom(df, f'{yr}-01-01', f'{yr+1}-01-01', hard_sl=sl, use_mkt_filter=False)
                for trade in res['trades']:
                    all_trades.append(dict(ticker=t, year=yr, **trade))
        s = engine.aggregate_stats(all_trades)
        results.append({
            '優化項目': f'停損門檻 {int(sl*100)}%',
            '總交易筆數': s['n'],
            '勝率%': round(s['wr'], 1),
            '總損益($)': round(s['total'], 2),
            '獲利因子': round(s['pf'], 2),
            '盈虧比': round(s['rr'], 2),
            '平均交易報酬%': round(s['avg_r'], 2)
        })
        
    # 測試2: 加入大盤多頭濾網 (S&P 500 > 50EMA 時才允許開新倉)
    for use_mkt in [True]:
        all_trades = []
        for t in target_stocks:
            df = prepare_with_mkt_filter(t, end='2026-07-25', mkt_filter_ema=50)
            if df is None: continue
            for yr in years:
                res = run_custom(df, f'{yr}-01-01', f'{yr+1}-01-01', hard_sl=-0.10, use_mkt_filter=True)
                for trade in res['trades']:
                    all_trades.append(dict(ticker=t, year=yr, **trade))
        s = engine.aggregate_stats(all_trades)
        results.append({
            '優化項目': '大盤多頭濾網 (SPX > 50EMA)',
            '總交易筆數': s['n'],
            '勝率%': round(s['wr'], 1),
            '總損益($)': round(s['total'], 2),
            '獲利因子': round(s['pf'], 2),
            '盈虧比': round(s['rr'], 2),
            '平均交易報酬%': round(s['avg_r'], 2)
        })
        
    df_res = pd.DataFrame(results)
    print(df_res.to_string(index=False))
    print("=" * 85)

if __name__ == '__main__':
    test_advance_optimizations()
