#!/usr/bin/env python3
"""
冷卻期機制 A/B 測試
測試冷卻天數 (0天 vs 5天 vs 10天 vs 15天) 對回測績效的影響
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from engine import prepare, buy_shares, CFG, TICKER_MAP, CORE5

def run_cooldown_backtest(ticker_name, ys, ye, cooldown_days=0):
    tk = TICKER_MAP[ticker_name]
    df = prepare(tk, start='2023-01-01', end=ye)
    if df is None or df.empty or len(df) < 25:
        return None
    
    capital = CFG['MAX_CAP']
    batches = []
    trades = []
    p10 = p40 = False
    entry_date = None
    last_exit_date = None  # 上次出場日期
    
    def tsh(): return sum(b['sh'] for b in batches)
    def tc(): return sum(b['sh'] * b['p'] * (1 + CFG['FEE']) for b in batches)
    def ret(px):
        c = tc()
        s = tsh()
        return (px * s - c) / c if c else 0.0
    
    def sell_all(px, dt, reason):
        nonlocal capital, p10, p40, entry_date, last_exit_date
        sh, c, r = tsh(), tc(), ret(px)
        proceeds = sh * px * (1 - CFG['TAX']) * (1 - CFG['FEE'])
        capital += proceeds
        trades.append(dict(進場日=entry_date, 出場日=dt.strftime('%Y-%m-%d'),
                           原因=reason, 出場價=round(px, 2),
                           損益=int(proceeds - c), 報酬率=round(r * 100, 2)))
        batches.clear()
        p10 = p40 = False
        entry_date = None
        last_exit_date = dt
        
    def sell_frac(px, frac, dt, tag):
        nonlocal capital
        sell = max(1, int(tsh() * frac))
        capital += sell * px * (1 - CFG['TAX']) * (1 - CFG['FEE'])
        for b in batches:
            take = min(b['sh'], sell)
            b['sh'] -= take
            sell -= take
            if sell == 0: break
        batches[:] = [b for b in batches if b['sh'] > 0]
        
    def buy(px, dt, tag):
        nonlocal capital, entry_date
        if capital < CFG['MAX_CAP'] * 0.1: return
        sh = buy_shares(capital * CFG['INV'], px)
        if sh <= 0: return
        capital -= sh * px * (1 + CFG['FEE'])
        if entry_date is None:
            entry_date = dt.strftime('%Y-%m-%d')
        batches.append(dict(sh=sh, p=px, ts=dt))

    period = df[(df.index >= ys) & (df.index < ye)]
    
    for dt, row in period.iterrows():
        o, c = float(row['Open']), float(row['Close'])
        ma5  = float(row['MA5'])  if not pd.isna(row['MA5'])  else 0
        ma10 = float(row['MA10']) if not pd.isna(row['MA10']) else 0
        ma20 = float(row['MA20']) if not pd.isna(row['MA20']) else 0
        vol5 = float(row['Vol5']) if not pd.isna(row['Vol5']) else 0
        volT = float(row['Volume'])
        box5h= float(row['Box5H']) if not pd.isna(row['Box5H']) else 0
        mkt_ret = float(row['MktRet']) if not pd.isna(row['MktRet']) else 0
        body_ret = (c - o) / o if o > 0 else 0
        big_drop = mkt_ret < CFG['BIG_DROP']

        # ① 部分停利
        if batches:
            r = ret(c)
            if not p10 and r >= CFG['P10']:
                p10 = True
                sell_frac(c, 0.10, dt, '停利10%')
            if batches and not p40 and ret(c) >= CFG['P40']:
                p40 = True
                sell_frac(c, 0.50, dt, '停利40%')

        # ② 全部出場
        if batches:
            r = ret(c)
            reason = None
            if r <= CFG['HARD_SL']: reason = '8%硬停損'
            elif ma20 > 0 and c < ma20: reason = '跌破月線'
            elif not big_drop and body_ret < CFG['BIG_CANDLE'] and volT > vol5: reason = '急跌>10%+放量'
            elif r >= CFG['PROFIT_LOCK'] and volT > vol5 and c < ma10: reason = '停利≥20%+跌10MA'
            
            if reason:
                sell_all(c, dt, reason)
                continue

        # ③ OBV 加碼
        if batches and ret(c) < 0:
            obv_sub = df['OBV'][(df.index >= batches[0]['ts']) & (df.index <= dt)]
            if (len(obv_sub) > 1 and float(obv_sub.iloc[-1]) > float(obv_sub.min())
                    and c > ma5 > 0 and c > box5h and box5h > 0
                    and capital >= CFG['MAX_CAP'] * 0.1):
                buy(c, dt, 'add_obv')

        # ④ 進場（檢查冷卻期）
        if row['Sig'] and capital >= CFG['MAX_CAP'] * 0.1:
            in_cooldown = False
            if not batches and last_exit_date is not None and cooldown_days > 0:
                trading_days = len(df[(df.index > last_exit_date) & (df.index <= dt)])
                if trading_days <= cooldown_days:
                    in_cooldown = True
            
            if not in_cooldown:
                tag = 'add_signal' if batches else 'entry'
                buy(c, dt, tag)

    # 期末平倉
    if batches:
        last_dt = period.index[-1]
        sell_all(float(period['Close'].iloc[-1]), last_dt, '回測結束')

    return pd.DataFrame(trades)

# ── 執行 A/B 測試 ──
print("🧪 開始 A/B 測試：冷卻天數 (0天 vs 5天 vs 10天 vs 15天)...")

for cooldown in [0, 5, 10, 15]:
    all_trades = []
    for name in CORE5:
        df_t24 = run_cooldown_backtest(name, '2024-01-01', '2024-12-31', cooldown_days=cooldown)
        df_t25 = run_cooldown_backtest(name, '2025-01-01', '2025-12-31', cooldown_days=cooldown)
        if df_t24 is not None and not df_t24.empty: all_trades.append(df_t24)
        if df_t25 is not None and not df_t25.empty: all_trades.append(df_t25)
    
    if all_trades:
        df_all = pd.concat(all_trades, ignore_index=True)
        n_trades = len(df_all)
        wins = df_all[df_all['損益'] > 0]
        losses = df_all[df_all['損益'] <= 0]
        win_rate = len(wins) / n_trades * 100
        total_pnl = df_all['損益'].sum()
        total_win = wins['損益'].sum()
        total_loss = abs(losses['損益'].sum())
        profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
        win_loss_ratio = (wins['損益'].mean() / abs(losses['損益'].mean())) if len(losses) > 0 and abs(losses['損益'].mean()) > 0 else 0
        
        print(f"\n【冷卻期 {cooldown:>2} 天】")
        print(f"  總交易筆數: {n_trades:>3} 筆  (比原本減少 {43 - n_trades} 筆無效交易)")
        print(f"  勝率:       {win_rate:>5.1f}%  ({len(wins)}勝 / {len(losses)}敗)")
        print(f"  盈虧比:     {win_loss_ratio:>5.2f}")
        print(f"  獲利因子:   {profit_factor:>5.2f}")
        print(f"  總損益:     +{total_pnl:,.0f} 元")
