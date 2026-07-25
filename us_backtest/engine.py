#!/usr/bin/env python3
"""
美股回測系統 — 正式版引擎
策略：EMA 趨勢跟蹤 + ATR 動態停損（詳見 STRATEGY.md）

用法：
  回測持倉標的      python3 engine.py backtest --stocks holdings --years 2024 2025
  回測指定標的      python3 engine.py backtest --stocks NVDA,AAPL --years 2024 2025
  產生圖表          加 --charts
  比較停損方案      python3 engine.py backtest --stocks NVDA --years 2024 2025 --compare-stops
  每日訊號掃描      python3 engine.py scan
  持倉健檢          python3 engine.py check
"""
import argparse
import os
import sys
import warnings
from datetime import date as _date, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

# 載入設定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CFG, HOLDINGS, WATCHLIST

warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.abspath(__file__))

# ── 資料下載與處理 ───────────────────────────────────────────────

_MKT_CACHE = {}


def clean(raw):
    """清理 yfinance 回傳的 MultiIndex 欄位。"""
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df.sort_index()


def calc_obv(df):
    """計算 On-Balance Volume。"""
    obv = [0]
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i - 1]:
            obv.append(obv[-1] + df['Volume'].iloc[i])
        elif df['Close'].iloc[i] < df['Close'].iloc[i - 1]:
            obv.append(obv[-1] - df['Volume'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)


def get_market(start, end):
    """下載 S&P 500 基準指數。"""
    key = (start, end)
    if key not in _MKT_CACHE:
        mkt = clean(yf.download(CFG['MARKET'], start=start, end=end,
                                progress=False, auto_adjust=False))
        mkt = mkt[mkt['Volume'] > 0]
        mkt['MktRS'] = mkt['Close'] / mkt['Close'].shift(CFG['RS_WIN'])
        mkt['MktRet'] = mkt['Close'].pct_change()
        _MKT_CACHE[key] = mkt
    return _MKT_CACHE[key]


def prepare(ticker, start='2019-01-01', end=None):
    """下載並計算所有技術指標。"""
    if end is None:
        end = (_date.today() + timedelta(days=1)).isoformat()
    df = clean(yf.download(ticker, start=start, end=end,
                           progress=False, auto_adjust=False))
    df = df[df['Volume'] > 0]  # 移除幽靈K棒
    if len(df) < 120:
        return None

    mkt = get_market(start, end)

    # EMA
    df['EMA20'] = df['Close'].ewm(span=CFG['EMA_FAST'], adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=CFG['EMA_MID'], adjust=False).mean()
    df['EMA100'] = df['Close'].ewm(span=CFG['EMA_SLOW'], adjust=False).mean()

    # ATR(14)
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = true_range.rolling(CFG['ATR_PERIOD']).mean()

    # 成交量均線
    df['Vol5'] = df['Volume'].rolling(CFG['VOL_WIN']).mean()

    # Box 突破
    df['BH'] = df[['Open', 'Close']].max(axis=1)
    df['BoxH'] = df['BH'].shift(1).rolling(CFG['BOX_WIN']).max()

    # OBV
    df['OBV'] = calc_obv(df)
    df['OBV_MA'] = df['OBV'].rolling(CFG['OBV_WIN']).mean()
    df['OBV_Up'] = ((df['OBV'] > df['OBV_MA']) &
                    (df['OBV'] > df['OBV'].shift(CFG['OBV_WIN'])))

    # 相對強度 vs S&P 500
    df['StockRS'] = df['Close'] / df['Close'].shift(CFG['RS_WIN'])
    df = df.join(mkt[['MktRet', 'MktRS']], how='left')

    # 進場訊號（6 條件全滿足）
    df['Sig'] = (
        (df['Volume'] > df['Vol5']) &                # 1. 量能放大
        (df['Close'] > df['BoxH']) &                 # 2. 突破 Box 高點
        (df['EMA20'] > df['EMA50']) &                # 3a. EMA 多頭排列
        (df['EMA50'] > df['EMA100']) &               # 3b. EMA 多頭排列
        (df['Close'] > df['EMA50']) &                # 4. 站上趨勢線
        df['OBV_Up'] &                               # 5. OBV 向上
        (df['StockRS'] > df['MktRS'])                # 6. RS > S&P 500
    )

    return df


# ── ATR 部位計算 ─────────────────────────────────────────────────

def calc_shares(capital, entry_price, atr):
    """ATR-based 部位計算：每筆最多虧 1% 資金。"""
    risk_amount = capital * CFG['RISK_PCT']
    stop_distance = CFG['ATR_SL_MULT'] * atr
    if stop_distance <= 0 or entry_price <= 0:
        return 0
    shares = int(risk_amount / stop_distance)
    max_by_pct = int(capital * CFG['MAX_SINGLE_PCT'] / entry_price)
    return max(0, min(shares, max_by_pct))


# ── 回測核心 ─────────────────────────────────────────────────────

def run(df, ys, ye, stop_mode='mixed'):
    """
    單一標的、單一期間回測。
    stop_mode: 'fixed'（-10%）、'atr'（2×ATR）、'mixed'（ATR trailing + -10% 硬停損）
    """
    slip = CFG['SLIPPAGE']
    capital = CFG['MAX_CAP']
    batches = []       # [{sh, price, atr, ts}]
    p_t1 = p_t2 = False
    trades, events = [], []
    eq_dates, eq_vals = [], []
    entry_date = None
    trailing_stop = None

    def tsh():
        return sum(b['sh'] for b in batches)

    def tcost():
        return sum(b['sh'] * b['price'] for b in batches)

    def uret(px):
        c = tcost()
        return (px * tsh() - c) / c if c > 0 else 0.0

    def sell_all(px, dt, reason):
        nonlocal capital, p_t1, p_t2, entry_date, trailing_stop
        px = px * (1 - slip)
        sh, cost, r = tsh(), tcost(), uret(px)
        proceeds = sh * px   # 零佣金、零交易稅
        capital += proceeds
        trades.append(dict(
            entry_date=entry_date,
            exit_date=dt.strftime('%Y-%m-%d'),
            reason=reason,
            exit_price=round(px, 2),
            shares=sh,
            pnl=round(proceeds - cost, 2),
            return_pct=round(r * 100, 2),
        ))
        events.append(dict(Date=dt, Price=px, Type='exit'))
        batches.clear()
        p_t1 = p_t2 = False
        entry_date = None
        trailing_stop = None

    def sell_frac(px, frac, dt, tag):
        nonlocal capital
        px = px * (1 - slip)
        sell = max(1, int(tsh() * frac))
        capital += sell * px
        for b in batches:
            take = min(b['sh'], sell)
            b['sh'] -= take
            sell -= take
            if sell == 0:
                break
        batches[:] = [b for b in batches if b['sh'] > 0]
        events.append(dict(Date=dt, Price=px, Type=tag))

    def buy(px, atr_val, dt, tag):
        nonlocal capital, entry_date, trailing_stop
        px = px * (1 + slip)
        if capital < CFG['MAX_CAP'] * 0.05:
            return
        sh = calc_shares(capital, px, atr_val)
        if sh <= 0:
            return
        cost = sh * px
        if cost > capital:
            sh = int(capital / px)
            if sh <= 0:
                return
            cost = sh * px
        capital -= cost
        if entry_date is None:
            entry_date = dt.strftime('%Y-%m-%d')
        batches.append(dict(sh=sh, price=px, atr=atr_val, ts=dt))
        events.append(dict(Date=dt, Price=px, Type=tag))
        # 設定 / 更新 trailing stop
        if stop_mode in ('atr', 'mixed'):
            new_stop = px - CFG['ATR_SL_MULT'] * atr_val
            if trailing_stop is None or new_stop > trailing_stop:
                trailing_stop = new_stop

    period = df[(df.index >= ys) & (df.index < ye)]

    for dt, row in period.iterrows():
        c = float(row['Close'])
        ema20 = float(row['EMA20']) if not pd.isna(row['EMA20']) else 0
        ema50 = float(row['EMA50']) if not pd.isna(row['EMA50']) else 0
        vol5 = float(row['Vol5']) if not pd.isna(row['Vol5']) else 0
        atr_val = float(row['ATR']) if not pd.isna(row['ATR']) else 0
        vol_today = float(row['Volume'])

        # ① 部分停利
        if batches:
            r = uret(c)
            if not p_t1 and r >= CFG['PROFIT_T1']:
                p_t1 = True
                sell_frac(c, CFG['PROFIT_T1_FRAC'], dt, 'profit_15%')
            if batches and not p_t2 and uret(c) >= CFG['PROFIT_T2']:
                p_t2 = True
                sell_frac(c, CFG['PROFIT_T2_FRAC'], dt, 'profit_40%')

        # ② 全部出場（優先：ATR停損 → 硬停損 → 跌破趨勢線 → 高檔出場）
        if batches:
            r = uret(c)
            reason = None

            # ATR trailing stop
            if stop_mode in ('atr', 'mixed') and trailing_stop and c < trailing_stop:
                reason = 'ATR_stop'

            # 硬停損 -10%
            if reason is None and stop_mode in ('fixed', 'mixed') and r <= CFG['HARD_SL']:
                reason = 'hard_stop'

            # 跌破 EMA50
            if reason is None and ema50 > 0 and c < ema50:
                reason = 'below_EMA50'

            # 高檔出場：獲利 ≥20% + 放量 + 跌破 EMA20
            if (reason is None and r >= CFG['PROFIT_LOCK']
                    and vol_today > vol5 and ema20 > 0 and c < ema20):
                reason = 'profit_lock'

            if reason:
                sell_all(c, dt, reason)
                eq_dates.append(dt)
                eq_vals.append(capital)
                continue

        # 更新 trailing stop（持倉中、價格上漲時跟進）
        if batches and stop_mode in ('atr', 'mixed') and atr_val > 0:
            new_stop = c - CFG['ATR_SL_MULT'] * atr_val
            if trailing_stop is not None and new_stop > trailing_stop:
                trailing_stop = new_stop

        # ③ 進場 / 順勢加碼
        if row['Sig'] and atr_val > 0:
            if batches:
                # 加碼條件：持倉獲利中才加
                if uret(c) > 0:
                    # 部位上限檢查
                    current_value = tsh() * c
                    if current_value < CFG['MAX_CAP'] * CFG['MAX_SINGLE_PCT']:
                        buy(c, atr_val, dt, 'add')
            else:
                buy(c, atr_val, dt, 'entry')

        eq_dates.append(dt)
        eq_vals.append(capital + tsh() * c)

    # 期末強制平倉
    if batches:
        last_dt = period.index[-1]
        sell_all(float(period['Close'].iloc[-1]), last_dt, 'period_end')
        eq_vals[-1] = capital

    equity = pd.Series(eq_vals, index=eq_dates)
    return dict(trades=trades, events=events, capital=capital,
                equity=equity, period=period)


# ── 績效統計 ─────────────────────────────────────────────────────

def equity_metrics(equity):
    """計算權益曲線指標（MDD, Sharpe）。"""
    if len(equity) < 2:
        return dict(mdd=0.0, sharpe=0.0)
    dd = equity / equity.cummax() - 1
    daily = equity.pct_change().dropna()
    sharpe = (daily.mean() / daily.std() * np.sqrt(252)
              if daily.std() > 0 else 0.0)
    return dict(mdd=float(dd.min()), sharpe=float(sharpe))


def aggregate_stats(all_trades):
    """匯總多檔多年交易統計。"""
    pnls = [t['pnl'] for t in all_trades]
    rets = [t['return_pct'] for t in all_trades]
    wins = [p for p in pnls if p > 0]
    loss = [p for p in pnls if p <= 0]
    n = len(pnls)
    streak = cur = 0
    for p in pnls:
        cur = cur + 1 if p <= 0 else 0
        streak = max(streak, cur)
    return dict(
        n=n,
        wr=len(wins) / n * 100 if n else 0,
        total=sum(pnls),
        avg_win=round(np.mean(wins), 2) if wins else 0,
        avg_loss=round(np.mean(loss), 2) if loss else 0,
        pf=abs(sum(wins) / sum(loss)) if loss and sum(loss) else float('inf'),
        rr=abs(np.mean(wins) / np.mean(loss)) if wins and loss and np.mean(loss) else 0,
        max_win=max(pnls) if pnls else 0,
        max_loss=min(pnls) if pnls else 0,
        avg_r=round(np.mean(rets), 2) if rets else 0,
        std_r=round(np.std(rets), 2) if rets else 0,
        max_streak=streak,
    )


# ── 圖表 ─────────────────────────────────────────────────────────

def plot_run(ticker, yr, res, tag):
    """產生單一標的回測圖表。"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    period = res['period']
    total = sum(t['pnl'] for t in res['trades'])
    wins = sum(1 for t in res['trades'] if t['pnl'] > 0)
    ret_pct = (res['capital'] - CFG['MAX_CAP']) / CFG['MAX_CAP'] * 100
    style = {
        'entry': ('#00cc00', '^', 160), 'add': ('#00ffff', '^', 130),
        'exit': ('#ff2222', 'v', 160),
        'profit_15%': ('#ffd700', 'D', 85), 'profit_40%': ('#ff8c00', 'D', 110),
    }

    fig, axes = plt.subplots(3, 1, figsize=(15, 11),
                             gridspec_kw={'height_ratios': [3.5, 1, 1]})
    fig.suptitle(f'{ticker}  {tag} {yr}  '
                 f'PnL: ${total:,.0f}  Return: {ret_pct:.2f}%  '
                 f'Win: {wins}/{len(res["trades"])}', fontsize=12)

    # 價格圖
    ax1 = axes[0]
    ax1.plot(period.index, period['Close'], color='#1f77b4', lw=1.3, label='Close')
    for col, clr in [('EMA20', 'orange'), ('EMA50', 'purple'), ('EMA100', 'green')]:
        ax1.plot(period.index, period[col], color=clr, lw=0.9, ls='--',
                 alpha=0.85, label=col)
    for ev in res['events']:
        s = style.get(ev['Type'])
        if s:
            ax1.scatter(ev['Date'], ev['Price'], color=s[0], marker=s[1],
                        s=s[2], zorder=5)
    ax1.legend(loc='upper left', fontsize=7, ncol=2)
    ax1.set_ylabel('Price (USD)')
    ax1.grid(alpha=0.3)

    # 成交量圖
    ax2 = axes[1]
    clrs = ['red' if c >= o else 'green'
            for c, o in zip(period['Close'], period['Open'])]
    ax2.bar(period.index, period['Volume'], color=clrs, alpha=0.65, width=0.8)
    ax2.plot(period.index, period['Vol5'], color='navy', lw=1, label='Vol MA5')
    ax2.legend(fontsize=8)
    ax2.set_ylabel('Volume')
    ax2.grid(alpha=0.3)

    # OBV 圖
    ax3 = axes[2]
    ax3.plot(period.index, period['OBV'], color='purple', lw=1.1, label='OBV')
    ax3.plot(period.index, period['OBV_MA'], color='red', lw=0.9, ls='--',
             label=f'OBV MA{CFG["OBV_WIN"]}')
    ax3.legend(fontsize=8)
    ax3.set_ylabel('OBV')
    ax3.grid(alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    os.makedirs(os.path.join(BASE, 'charts'), exist_ok=True)
    path = os.path.join(BASE, 'charts', f'{ticker}_{tag}_{yr}.png')
    plt.savefig(path, dpi=130, bbox_inches='tight')
    plt.close()
    return path


# ── 指令：回測 ───────────────────────────────────────────────────

def cmd_backtest(args):
    if args.stocks == 'holdings':
        tickers = list(HOLDINGS.keys())
    elif args.stocks == 'watchlist':
        tickers = WATCHLIST
    else:
        tickers = [s.strip().upper() for s in args.stocks.split(',')]

    years = [int(y) for y in args.years]
    end = f'{max(years) + 1}-01-01'
    stop_modes = ['fixed', 'atr', 'mixed'] if args.compare_stops else [args.stop_mode]

    for mode in stop_modes:
        tag = mode
        all_trades = []
        rows = []

        if args.compare_stops:
            print(f'\n{"=" * 66}')
            print(f'  停損方案：{mode.upper()}')
            print(f'{"=" * 66}')

        for ticker in tickers:
            df = prepare(ticker, end=end)
            if df is None:
                print(f'⚠ {ticker}: 資料不足，跳過')
                continue
            for yr in years:
                res = run(df, f'{yr}-01-01', f'{yr + 1}-01-01', stop_mode=mode)
                m = equity_metrics(res['equity'])
                total = sum(t['pnl'] for t in res['trades'])
                wins = sum(1 for t in res['trades'] if t['pnl'] > 0)
                for t in res['trades']:
                    all_trades.append(dict(ticker=ticker, year=yr, **t))
                rows.append((ticker, yr, total,
                             (res['capital'] - CFG['MAX_CAP']) / CFG['MAX_CAP'] * 100,
                             wins, len(res['trades']), m['mdd'] * 100, m['sharpe']))
                print(f'{ticker} {yr}: PnL ${total:+,.0f}  '
                      f'Win {wins}/{len(res["trades"])}  '
                      f'MDD {m["mdd"] * 100:.1f}%  Sharpe {m["sharpe"]:.2f}')
                if args.charts:
                    path = plot_run(ticker, yr, res, tag)
                    print(f'  Chart → {path}')

        if not all_trades:
            continue

        s = aggregate_stats(all_trades)
        print(f'\n{"─" * 62}')
        print(f'Summary ({len(tickers)} tickers × {years})  '
              f'Stop mode: {mode.upper()}')
        print(f'{"─" * 62}')
        print(f'Total trades    {s["n"]}')
        print(f'Win rate        {s["wr"]:.1f}%')
        print(f'Total PnL       ${s["total"]:+,.2f}')
        print(f'Avg win         ${s["avg_win"]:+,.2f}   Avg loss ${s["avg_loss"]:+,.2f}')
        print(f'Profit factor   {s["pf"]:.2f}      Win/Loss ratio {s["rr"]:.2f}')
        print(f'Best trade      ${s["max_win"]:+,.2f}')
        print(f'Worst trade     ${s["max_loss"]:+,.2f}')
        print(f'Avg return      {s["avg_r"]:.2f}%   Std {s["std_r"]:.2f}%')
        print(f'Max losing streak  {s["max_streak"]}')

        os.makedirs(os.path.join(BASE, 'results'), exist_ok=True)
        yr_tag = '_'.join(map(str, years))
        csv_path = os.path.join(BASE, 'results', f'trades_{tag}_{yr_tag}.csv')
        pd.DataFrame(all_trades).to_csv(csv_path, index=False)
        print(f'\nTrade details → {csv_path}')


# ── 指令：每日掃描 ───────────────────────────────────────────────

def cmd_scan(args):
    tickers = WATCHLIST if not args.stocks else [
        s.strip().upper() for s in args.stocks.split(',')]
    start = (_date.today() - timedelta(days=400)).isoformat()
    results = []

    for ticker in tickers:
        df = prepare(ticker, start=start)
        if df is None:
            results.append((ticker, None, [], '❓ No data', 0, 0, 0))
            continue
        row = df.iloc[-1]
        bar_date = df.index[-1].strftime('%m/%d')
        c = float(row['Close'])
        ema20 = float(row['EMA20'])
        ema50 = float(row['EMA50'])
        ema100 = float(row['EMA100'])
        atr = float(row['ATR'])
        boxh = float(row['BoxH']) if not pd.isna(row['BoxH']) else 0
        vol_t, vol5 = float(row['Volume']), float(row['Vol5'])
        srs = float(row['StockRS']) if not pd.isna(row['StockRS']) else 0
        mrs = float(row['MktRS']) if not pd.isna(row['MktRS']) else 0

        checks = [
            ('Vol>5MA', vol_t > vol5),
            (f'C{c:.1f}>Box{boxh:.1f}', c > boxh and boxh > 0),
            ('EMA20>50', ema20 > ema50),
            ('EMA50>100', ema50 > ema100),
            ('C>EMA50', c > ema50),
            ('OBV↑', bool(row['OBV_Up'])),
            ('RS>SPX', srs > mrs if mrs > 0 else False),
        ]
        n_pass = sum(1 for _, v in checks if v)
        verdict = ('🟢 ENTRY' if n_pass == 7
                   else f'🟡 {7 - n_pass} away' if n_pass >= 5
                   else '⚪ No signal')
        results.append((ticker, bar_date, checks, verdict, n_pass, c, atr))

    results.sort(key=lambda r: -r[4])
    bar = results[0][1] if results and results[0][1] else '?'
    print(f'\n📡 Daily Signal Scan  Data: {bar}')
    print('=' * 70)

    for r in results:
        ticker, _, checks, verdict, n_pass, c, atr = r
        fails = [lbl for lbl, v in checks if not v]
        name = HOLDINGS.get(ticker, {}).get('name', '')
        held = '📌' if ticker in HOLDINGS else '  '
        print(f'\n{held}{verdict}  {ticker} {name}  {n_pass}/7  '
              f'${c:.2f}  ATR:{atr:.2f}')
        if fails and n_pass >= 5:
            print(f'    Missing: {", ".join(fails)}')

    print('\n⏰ Run after market close for accurate volume data.')


# ── 指令：持倉健檢 ───────────────────────────────────────────────

def cmd_check(args):
    start = (_date.today() - timedelta(days=400)).isoformat()
    print(f'\n🏥 Portfolio Health Check')
    print(f'{"=" * 74}')
    print(f'{"Ticker":<8} {"Cost":>8} {"Now":>8} {"PnL%":>7} '
          f'{"Trend":>6} {"ATR Stop":>9} {"Signal":>8} {"Action"}')
    print(f'{"─" * 74}')

    total_value = 0
    total_cost = 0

    for ticker, info in HOLDINGS.items():
        df = prepare(ticker, start=start)
        if df is None:
            print(f'{ticker:<8} — No data —')
            continue

        row = df.iloc[-1]
        c = float(row['Close'])
        ema50 = float(row['EMA50'])
        ema20 = float(row['EMA20'])
        ema100 = float(row['EMA100'])
        atr = float(row['ATR'])

        cost = info['cost']
        shares = info['shares']
        pnl_pct = (c - cost) / cost * 100
        total_value += c * shares
        total_cost += cost * shares

        # 趨勢判斷
        if ema20 > ema50 > ema100:
            trend = '🟢 Up'
        elif c > ema50:
            trend = '🟡 Flat'
        else:
            trend = '🔴 Down'

        # ATR 停損位置（假設從成本開始）
        atr_stop = cost - CFG['ATR_SL_MULT'] * atr
        atr_stop_pct = (atr_stop - c) / c * 100

        # 訊號
        sig = bool(row['Sig'])
        sig_str = '🟢 Yes' if sig else '⚪ No'

        # 建議
        if pnl_pct <= CFG['HARD_SL'] * 100:
            action = '🚨 STOP LOSS'
        elif c < ema50:
            action = '⚠️  EXIT (below EMA50)'
        elif trend == '🔴 Down':
            action = '⚠️  REDUCE'
        elif sig:
            action = '✅ HOLD (strong)'
        elif c > ema50:
            action = '👀 HOLD (monitor)'
        else:
            action = '⚠️  WATCH'

        print(f'{ticker:<8} ${cost:>7.2f} ${c:>7.2f} {pnl_pct:>+6.1f}% '
              f'{trend:>6} ${atr_stop:>7.2f} {sig_str:>8}  {action}')

    cash = CFG.get('CASH_BALANCE', 0.0)
    net_equity = total_value + cash
    total_account_cost = total_cost + cash
    total_pnl = total_value - total_cost
    total_pnl_pct = total_pnl / total_cost * 100 if total_cost > 0 else 0
    risk_per_trade = net_equity * CFG['RISK_PCT']

    print(f'\n{"─" * 74}')
    print(f'Holdings Value : ${total_value:,.2f}   Cost: ${total_cost:,.2f}   Unrealized PnL: ${total_pnl:+,.2f} ({total_pnl_pct:+.1f}%)')
    print(f'Cash Balance   : ${cash:,.2f}')
    print(f'Total Equity   : ${net_equity:,.2f}   (Account Cost: ${total_account_cost:,.2f})')
    print(f'Single Trade Risk (1%): ${risk_per_trade:,.2f}')

    # 產業集中度警告
    semi_tickers = ['AMKR', 'AVGO', 'COHR', 'MU', 'ON', 'TSM']
    semi_value = sum(HOLDINGS[t]['shares'] * float(prepare(t, start=start).iloc[-1]['Close'])
                     for t in semi_tickers if t in HOLDINGS and prepare(t, start=start) is not None)
    semi_pct = semi_value / net_equity * 100 if net_equity > 0 else 0
    if semi_pct > 40:
        print(f'\n⚠️  Semiconductor concentration: {semi_pct:.0f}% of total account (recommend < 40%)')


# ── CLI ──────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='US Stock Backtesting Engine')
    sub = ap.add_subparsers(dest='cmd', required=True)

    # backtest
    bt = sub.add_parser('backtest', help='Run backtest')
    bt.add_argument('--stocks', default='holdings',
                    help='holdings / watchlist / NVDA,AAPL,...')
    bt.add_argument('--years', nargs='+', default=['2024', '2025'])
    bt.add_argument('--charts', action='store_true', help='Generate charts')
    bt.add_argument('--stop-mode', default='mixed',
                    choices=['fixed', 'atr', 'mixed'],
                    help='Stop loss mode (default: mixed)')
    bt.add_argument('--compare-stops', action='store_true',
                    help='Compare all 3 stop loss modes')
    bt.add_argument('--tag', default=None)

    # scan
    sc = sub.add_parser('scan', help='Daily signal scan')
    sc.add_argument('--stocks', default=None,
                    help='Comma-separated tickers (default: watchlist)')

    # check
    sub.add_parser('check', help='Portfolio health check')

    args = ap.parse_args()
    if args.cmd == 'backtest':
        cmd_backtest(args)
    elif args.cmd == 'scan':
        cmd_scan(args)
    elif args.cmd == 'check':
        cmd_check(args)


if __name__ == '__main__':
    main()
