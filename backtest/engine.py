#!/usr/bin/env python3
"""
台股回測系統 — 正式版引擎
策略：月線+急跌>10% + 8%硬停損（詳見 STRATEGY.md）

用法：
  回測（核心五檔）   python3 engine.py backtest --stocks core --years 2024 2025
  回測（指定標的）   python3 engine.py backtest --stocks 奇鋐,聯發科 --years 2025
  次日開盤執行模式   python3 engine.py backtest --stocks core --years 2024 2025 --next-open
  產生圖表           加 --charts
  每日訊號掃描       python3 engine.py scan
  掃描指定標的       python3 engine.py scan --stocks 晶技,力智,世芯KY
"""
import argparse
import os
import sys
import warnings
from datetime import date as _date, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.abspath(__file__))

# ── 策略參數（與 STRATEGY.md 同步）─────────────────────────────
CFG = dict(
    MARKET='^TWII',
    FEE=0.001425,        # 手續費（買賣各收）
    TAX=0.003,           # 交易稅（賣出）
    MAX_CAP=5_000_000,   # 總資金上限
    INV=0.30,            # 每次進場投入剩餘資金比例
    P10=0.10,            # 部分停利門檻1：+10% 賣 10%
    P40=0.40,            # 部分停利門檻2：+40% 賣 50%
    PROFIT_LOCK=0.20,    # 高檔停利門檻：獲利≥20% + 放量 + 跌破10MA
    HARD_SL=-0.08,       # 硬停損：帳面 -8% 全出
    BIG_CANDLE=-0.10,    # 急跌出場：實體跌幅 >10% + 放量
    BIG_DROP=-0.02,      # 大盤跌幅 >2% 當日豁免急跌出場
    RS_WIN=20,           # 相對強度窗口（日）
    SLIPPAGE=0.0,        # 滑價（單邊，例 0.001 = 0.1%）
)
FEE, TAX = CFG['FEE'], CFG['TAX']

# ── Ticker 對照表（已用實際成交價驗證過）────────────────────────
TICKER_MAP = {
    '聯發科': '2454.TW', '創意': '3443.TW', '奇鋐': '3017.TW',
    '貿聯KY': '3665.TW', '群聯': '8299.TWO', '緯創': '3231.TW',
    '雙鴻': '3324.TWO', '研華': '2395.TW', '鈊象': '3293.TWO',
    '光寶科': '2301.TW', '鴻海': '2317.TW', '緯穎': '6669.TW',
    '嘉澤': '3533.TW', '世芯KY': '3661.TW', '智邦': '2345.TW',
    '力積電': '6770.TW', '頎邦': '6239.TW', '毅嘉': '2402.TW',
    '華通': '2313.TW', '金像電': '2368.TW', '亞翔': '6139.TW',
    '中興電': '1513.TW', '鈺創': '5351.TWO', '譜瑞KY': '4966.TWO',
    '迅得': '6438.TW', '達麗': '6177.TW', '力智': '6719.TW',
    '順德': '2351.TW', '博智': '8155.TWO', '富鼎': '8261.TW',
    '達欣工': '3515.TW', '辛耘': '3583.TW', '晶技': '3042.TW',
    '祥碩': '5269.TW', '今展科': None,  # 4961 是天鈺，今展科待查
    # 2026-07-07 由 2025 對帳單成交價驗證
    '啟碁': '6285.TW', 'M31': '6643.TWO', '南港': '2101.TW',
    '新美齊': '2442.TW', '定穎投控': '3715.TW', '廣達': '2382.TW',
    '瀚宇博': '5469.TW', '穎崴': '6515.TW', '中磊': '5388.TW',
    '長科': '6548.TWO', '萬泰科': '6190.TWO',
    '欣銓': '3264.TWO', '均豪': '5443.TWO',
    # 2026-07-08 CCL 供應鏈掃描時解析
    '台玻': '1802.TW', '富喬': '1815.TWO', '建榮': '5340.TWO',
    '德宏': '5475.TWO', '南亞': '1303.TW', '金居': '8358.TWO',
    '長興': '1717.TW', '台光電': '2383.TW', '台燿': '6274.TWO',
    '聯茂': '6213.TW', '欣興': '3037.TW', '南電': '8046.TW',
    '景碩': '3189.TW', '臻鼎KY': '4958.TW',
    '健鼎': '3044.TW', '尖點': '8021.TW', '凱崴': '5498.TWO',
    '亞泰金屬': '6727.TWO', '大量': '3167.TW', '由田': '3455.TWO',
    '鉅橡': '8074.TWO',
    '聯策': '6658.TW',  # 2026-07-08 確認（券商介面誤標 6299）
    '順達': '3211.TWO', '盛群': '6202.TW', '松翰': '5471.TW',
    '凌通': '4952.TW', '微星': '2377.TW', '英業達': '2356.TW',
    '南亞科': '2408.TW', '環球晶': '6488.TWO', '新唐': '4919.TW',
    '天鈺': '4961.TW',  # 4961 實為天鈺（原誤標今展科）
    '新盛力': '4931.TWO', '鈦昇': '8027.TWO', '事欣科': '4916.TW',
}
# 尚未找到正確 ticker（yfinance 查無或價格不符）：
# 界霖、新盛力、台嘉碩、今展科、AES-KY
# 注意：6285.TW 是「啟碁」不是界霖（2026-06 對帳單分析曾誤標）

CORE5 = ['聯發科', '創意', '奇鋐', '貿聯KY', '群聯']
# 依 2025+2026 回測分級（results/trades_watchlist_2025_2026.csv）：
# A級優先執行；C級（博智/凌通/英業達已移除）訊號亮也跳過
DEFAULT_WATCHLIST = ['聯發科', '創意', '奇鋐', '貿聯KY', '群聯',
                     '晶技', '力智', '世芯KY', '辛耘', '祥碩',
                     '智邦', '華通', '力積電', '金像電',
                     '台光電', '台燿', '臻鼎KY', '金居', '南亞',
                     '順達', '盛群', '松翰', '微星',
                     '南亞科', '環球晶', '聯茂', '事欣科', '光寶科', '欣銓']

_MKT_CACHE = {}


def resolve(name):
    """股名或 ticker → ticker"""
    if name in TICKER_MAP:
        return TICKER_MAP[name]
    if '.' in name:
        return name
    return None


def display_name(ticker):
    for n, t in TICKER_MAP.items():
        if t == ticker:
            return n
    return ticker


def clean(raw):
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df.sort_index()


def calc_obv(df):
    obv = [0]
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i - 1]:
            obv.append(obv[-1] + df['Volume'].iloc[i])
        elif df['Close'].iloc[i] < df['Close'].iloc[i - 1]:
            obv.append(obv[-1] - df['Volume'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)


def buy_shares(invest, price):
    cp = price * (1 + FEE)
    lot = 1000 if cp * 1000 <= invest else 1
    return int(invest / cp / lot) * lot


def get_market(start, end):
    key = (start, end)
    if key not in _MKT_CACHE:
        mkt = clean(yf.download(CFG['MARKET'], start=start, end=end,
                                progress=False, auto_adjust=False))
        mkt['MktRS'] = mkt['Close'] / mkt['Close'].shift(CFG['RS_WIN'])
        mkt['MktRet'] = mkt['Close'].pct_change()
        _MKT_CACHE[key] = mkt
    return _MKT_CACHE[key]


def prepare(ticker, start='2023-06-01', end=None):
    """下載並計算所有技術指標（auto_adjust=False 用真實市價）"""
    if end is None:
        end = (_date.today() + timedelta(days=1)).isoformat()
    df = clean(yf.download(ticker, start=start, end=end,
                           progress=False, auto_adjust=False))
    # 移除幽靈K棒（yfinance 會在休市日插入量=0、價格複製前日的假資料，
    # 導致所有均線偏移一天。例：2026-07-10）
    df = df[df['Volume'] > 0]
    if len(df) < 25:
        return None
    mkt = get_market(start, end)
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Vol3'] = df['Volume'].rolling(3).mean()
    df['Vol5'] = df['Volume'].rolling(5).mean()
    df['BH'] = df[['Open', 'Close']].max(axis=1)
    df['Box5H'] = df['BH'].shift(1).rolling(5).max()
    df['OBV'] = calc_obv(df)
    df['OBV_MA'] = df['OBV'].rolling(5).mean()
    df['OBV_Up'] = (df['OBV'] > df['OBV_MA']) & (df['OBV'] > df['OBV'].shift(5))
    df['StockRS'] = df['Close'] / df['Close'].shift(CFG['RS_WIN'])
    df = df.join(mkt[['MktRet', 'MktRS']], how='left')
    df['Sig'] = (
        (df['Volume'] > df['Vol3']) &
        (df['Volume'] >= df['Volume'].shift(1) * 1.2) &
        (df['Close'] > df['Box5H']) &
        (df['MA5'] > df['MA10']) & (df['MA10'] > df['MA20']) &
        (df['Close'] > df['MA20']) &
        df['OBV_Up'] &
        (df['StockRS'] > df['MktRS'])
    )
    return df


# ── 回測核心 ─────────────────────────────────────────────────────

def run(df, ys, ye, next_open=False):
    """單一標的、單一期間回測。next_open=True 時所有動作延至次日開盤執行。"""
    slip = CFG['SLIPPAGE']
    capital = CFG['MAX_CAP']
    batches = []
    p10 = p40 = False
    pending = []          # 次日開盤模式的待執行動作
    trades, events = [], []
    eq_dates, eq_vals = [], []
    entry_date = None

    def tsh():
        return sum(b['sh'] for b in batches)

    def tc():
        return sum(b['sh'] * b['p'] * (1 + FEE) for b in batches)

    def ret(px):
        cv = tc()
        s = tsh()
        return (px * s - cv) / cv if cv else 0.0

    def sell_all(px, dt, reason):
        nonlocal capital, p10, p40, entry_date
        px = px * (1 - slip)
        sh, c, r = tsh(), tc(), ret(px)
        proceeds = sh * px * (1 - TAX) * (1 - FEE)
        capital += proceeds
        trades.append(dict(進場日=entry_date, 出場日=dt.strftime('%Y-%m-%d'),
                           原因=reason, 出場價=round(px, 2),
                           損益=int(proceeds - c), 報酬率=round(r * 100, 2)))
        events.append(dict(Date=dt, Price=px, Type='exit'))
        batches.clear()
        p10 = p40 = False
        entry_date = None

    def sell_frac(px, frac, dt, tag):
        nonlocal capital
        px = px * (1 - slip)
        sell = max(1, int(tsh() * frac))
        capital += sell * px * (1 - TAX) * (1 - FEE)
        for b in batches:
            take = min(b['sh'], sell)
            b['sh'] -= take
            sell -= take
            if sell == 0:
                break
        batches[:] = [b for b in batches if b['sh'] > 0]
        events.append(dict(Date=dt, Price=px, Type=tag))

    def buy(px, dt, tag):
        nonlocal capital, entry_date
        px = px * (1 + slip)
        if capital < CFG['MAX_CAP'] * 0.1:
            return
        sh = buy_shares(capital * CFG['INV'], px)
        if sh <= 0:
            return
        capital -= sh * px * (1 + FEE)
        if entry_date is None:
            entry_date = dt.strftime('%Y-%m-%d')
        batches.append(dict(sh=sh, p=px, ts=dt))
        events.append(dict(Date=dt, Price=px, Type=tag))

    period = df[(df.index >= ys) & (df.index < ye)]
    for dt, row in period.iterrows():
        o, c = float(row['Open']), float(row['Close'])
        ma5 = float(row['MA5']) if not pd.isna(row['MA5']) else 0
        ma10 = float(row['MA10']) if not pd.isna(row['MA10']) else 0
        ma20 = float(row['MA20']) if not pd.isna(row['MA20']) else 0
        vol5 = float(row['Vol5']) if not pd.isna(row['Vol5']) else 0
        volT = float(row['Volume'])
        box5h = float(row['Box5H']) if not pd.isna(row['Box5H']) else 0
        mkt_ret = float(row['MktRet']) if not pd.isna(row['MktRet']) else 0
        body_ret = (c - o) / o if o > 0 else 0
        big_drop = mkt_ret < CFG['BIG_DROP']

        # 次日開盤模式：先執行昨日排入的動作
        if next_open and pending:
            for act, info in pending:
                if act == 'exit' and batches:
                    sell_all(o, dt, info)
                elif act == 'p10' and batches:
                    sell_frac(o, 0.10, dt, '停利10%')
                elif act == 'p40' and batches:
                    sell_frac(o, 0.50, dt, '停利40%')
                elif act in ('entry', 'add_signal', 'add_obv'):
                    buy(o, dt, act)
            pending = []

        exit_queued = False

        # ① 部分停利
        if batches:
            r = ret(c)
            if not p10 and r >= CFG['P10']:
                p10 = True
                if next_open:
                    pending.append(('p10', None))
                else:
                    sell_frac(c, 0.10, dt, '停利10%')
            if batches and not p40 and ret(c) >= CFG['P40']:
                p40 = True
                if next_open:
                    pending.append(('p40', None))
                else:
                    sell_frac(c, 0.50, dt, '停利40%')

        # ② 全部出場（優先順序：硬停損 → 跌破月線 → 急跌放量 → 高檔停利）
        if batches:
            r = ret(c)
            reason = None
            if r <= CFG['HARD_SL']:
                reason = '8%硬停損'
            elif ma20 > 0 and c < ma20:
                reason = '跌破月線'
            elif not big_drop and body_ret < CFG['BIG_CANDLE'] and volT > vol5:
                reason = '急跌>10%+放量'
            elif r >= CFG['PROFIT_LOCK'] and volT > vol5 and c < ma10:
                reason = '停利≥20%+跌10MA'
            if reason:
                if next_open:
                    pending.append(('exit', reason))
                    exit_queued = True
                else:
                    sell_all(c, dt, reason)
                    eq_dates.append(dt)
                    eq_vals.append(capital)
                    continue

        # ③ OBV 加碼（持倉虧損 + OBV 未創新低 + 站上5MA + 突破Box5H）
        if batches and not exit_queued and ret(c) < 0:
            obv_sub = df['OBV'][(df.index >= batches[0]['ts']) & (df.index <= dt)]
            if (len(obv_sub) > 1 and float(obv_sub.iloc[-1]) > float(obv_sub.min())
                    and c > ma5 > 0 and c > box5h and box5h > 0
                    and capital >= CFG['MAX_CAP'] * 0.1):
                if next_open:
                    pending.append(('add_obv', None))
                else:
                    buy(c, dt, 'add_obv')

        # ④ 進場 / 順勢加碼
        if row['Sig'] and not exit_queued and capital >= CFG['MAX_CAP'] * 0.1:
            tag = 'add_signal' if batches else 'entry'
            if next_open:
                pending.append((tag, None))
            else:
                buy(c, dt, tag)

        eq_dates.append(dt)
        eq_vals.append(capital + tsh() * c)

    # 期末強制平倉
    if batches:
        last_dt = period.index[-1]
        sell_all(float(period['Close'].iloc[-1]), last_dt, '回測結束')
        eq_vals[-1] = capital

    equity = pd.Series(eq_vals, index=eq_dates)
    return dict(trades=trades, events=events, capital=capital,
                equity=equity, period=period)


def equity_metrics(equity):
    if len(equity) < 2:
        return dict(mdd=0.0, sharpe=0.0)
    dd = equity / equity.cummax() - 1
    daily = equity.pct_change().dropna()
    sharpe = daily.mean() / daily.std() * np.sqrt(252) if daily.std() > 0 else 0.0
    return dict(mdd=float(dd.min()), sharpe=float(sharpe))


def aggregate_stats(all_trades):
    pnls = [t['損益'] for t in all_trades]
    rets = [t['報酬率'] for t in all_trades]
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
        avg_win=int(np.mean(wins)) if wins else 0,
        avg_loss=int(np.mean(loss)) if loss else 0,
        pf=abs(sum(wins) / sum(loss)) if loss and sum(loss) else float('inf'),
        rr=abs(np.mean(wins) / np.mean(loss)) if wins and loss and np.mean(loss) else 0,
        max_win=max(pnls) if pnls else 0,
        max_loss=min(pnls) if pnls else 0,
        avg_r=float(np.mean(rets)) if rets else 0,
        std_r=float(np.std(rets)) if rets else 0,
        max_streak=streak,
    )


def plot_run(name, ticker, yr, res, tag):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang TC', 'sans-serif']
    matplotlib.rcParams['axes.unicode_minus'] = False

    period = res['period']
    total = sum(t['損益'] for t in res['trades'])
    wins = sum(1 for t in res['trades'] if t['損益'] > 0)
    ret_pct = (res['capital'] - CFG['MAX_CAP']) / CFG['MAX_CAP'] * 100
    style = {'entry': ('#00cc00', '^', 160), 'add_signal': ('#00ffff', '^', 130),
             'add_obv': ('#1e90ff', '^', 120), 'exit': ('#ff2222', 'v', 160),
             '停利10%': ('#ffd700', 'D', 85), '停利40%': ('#ff8c00', 'D', 110)}

    fig, axes = plt.subplots(3, 1, figsize=(15, 11),
                             gridspec_kw={'height_ratios': [3.5, 1, 1]})
    fig.suptitle(f'{name}（{ticker}）{tag} {yr}  '
                 f'損益:{total:,}元  報酬:{ret_pct:.2f}%  勝率:{wins}/{len(res["trades"])}',
                 fontsize=12)
    ax1 = axes[0]
    ax1.plot(period.index, period['Close'], color='#1f77b4', lw=1.3, label='收盤價')
    for col, clr in [('MA5', 'orange'), ('MA10', 'purple'), ('MA20', 'green')]:
        ax1.plot(period.index, period[col], color=clr, lw=0.9, ls='--', alpha=0.85, label=col)
    for ev in res['events']:
        s = style.get(ev['Type'])
        if s:
            ax1.scatter(ev['Date'], ev['Price'], color=s[0], marker=s[1], s=s[2], zorder=5)
    ax1.legend(loc='upper left', fontsize=7, ncol=2)
    ax1.set_ylabel('股價(TWD)')
    ax1.grid(alpha=0.3)
    ax2 = axes[1]
    clrs = ['red' if c >= o else 'green' for c, o in zip(period['Close'], period['Open'])]
    ax2.bar(period.index, period['Volume'], color=clrs, alpha=0.65, width=0.8)
    ax2.plot(period.index, period['Vol5'], color='navy', lw=1, label='5日均量')
    ax2.legend(fontsize=8)
    ax2.set_ylabel('成交量')
    ax2.grid(alpha=0.3)
    ax3 = axes[2]
    ax3.plot(period.index, period['OBV'], color='purple', lw=1.1, label='OBV')
    ax3.plot(period.index, period['OBV_MA'], color='red', lw=0.9, ls='--', label='OBV MA5')
    ax3.legend(fontsize=8)
    ax3.set_ylabel('OBV')
    ax3.grid(alpha=0.3)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    os.makedirs(os.path.join(BASE, 'charts'), exist_ok=True)
    code = ticker.replace('.TWO', 'O').replace('.TW', '')
    path = os.path.join(BASE, 'charts', f'{code}_{tag}_{yr}.png')
    plt.savefig(path, dpi=130, bbox_inches='tight')
    plt.close()
    return path


# ── 指令 ─────────────────────────────────────────────────────────

def cmd_backtest(args):
    names = CORE5 if args.stocks == 'core' else [s.strip() for s in args.stocks.split(',')]
    years = [int(y) for y in args.years]
    end = f'{max(years) + 1}-01-01'
    tag = args.tag or ('nextopen' if args.next_open else 'official')

    all_trades = []
    rows = []
    for name in names:
        ticker = resolve(name)
        if ticker is None:
            print(f'⚠ {name}: ticker 未確認，跳過')
            continue
        df = prepare(ticker, end=end)
        if df is None:
            print(f'⚠ {name}({ticker}): 無資料，跳過')
            continue
        for yr in years:
            res = run(df, f'{yr}-01-01', f'{yr + 1}-01-01', next_open=args.next_open)
            m = equity_metrics(res['equity'])
            total = sum(t['損益'] for t in res['trades'])
            wins = sum(1 for t in res['trades'] if t['損益'] > 0)
            for t in res['trades']:
                all_trades.append(dict(標的=name, 年度=yr, **t))
            rows.append((name, yr, total,
                         (res['capital'] - CFG['MAX_CAP']) / CFG['MAX_CAP'] * 100,
                         wins, len(res['trades']), m['mdd'] * 100, m['sharpe']))
            print(f'{name} {yr}: 損益{total:+,}  勝率{wins}/{len(res["trades"])}  '
                  f'MDD {m["mdd"]*100:.1f}%  Sharpe {m["sharpe"]:.2f}')
            if args.charts:
                path = plot_run(name, ticker, yr, res, tag)
                print(f'  圖表 → {path}')

    if not all_trades:
        return
    s = aggregate_stats(all_trades)
    print(f'\n{"─" * 62}')
    print(f'匯總（{len(names)}檔 × {years}）  模式：'
          f'{"次日開盤執行" if args.next_open else "當日收盤執行"}')
    print(f'{"─" * 62}')
    print(f'交易筆數     {s["n"]}')
    print(f'勝率         {s["wr"]:.1f}%')
    print(f'總損益       {s["total"]:+,}')
    print(f'平均獲利     {s["avg_win"]:+,}   平均虧損 {s["avg_loss"]:+,}')
    print(f'盈虧比       {s["rr"]:.2f}      獲利因子 {s["pf"]:.2f}')
    print(f'最大單筆     {s["max_win"]:+,} / {s["max_loss"]:+,}')
    print(f'平均報酬率   {s["avg_r"]:.2f}%   標準差 {s["std_r"]:.2f}%')
    print(f'最大連輸     {s["max_streak"]} 筆')

    os.makedirs(os.path.join(BASE, 'results'), exist_ok=True)
    csv_path = os.path.join(BASE, 'results', f'trades_{tag}_{"_".join(map(str, years))}.csv')
    pd.DataFrame(all_trades).to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f'\n交易明細 → {csv_path}')


def cmd_scan(args):
    names = DEFAULT_WATCHLIST if not args.stocks else [s.strip() for s in args.stocks.split(',')]
    start = (_date.today() - timedelta(days=200)).isoformat()
    results = []
    for name in names:
        ticker = resolve(name)
        if ticker is None:
            results.append((name, None, None, [], '❓ ticker未確認'))
            continue
        df = prepare(ticker, start=start)
        if df is None:
            results.append((name, ticker, None, [], '❓ 無資料'))
            continue
        row = df.iloc[-1]
        bar_date = df.index[-1].strftime('%m/%d')
        c = float(row['Close'])
        ma5, ma10, ma20 = float(row['MA5']), float(row['MA10']), float(row['MA20'])
        box5h = float(row['Box5H'])
        volT, vol3 = float(row['Volume']), float(row['Vol3'])
        vol_prev = float(df['Volume'].iloc[-2])
        srs, mrs = float(row['StockRS']), float(row['MktRS'])
        checks = [
            ('量>3日均', volT > vol3),
            ('量>前日1.2x', volT >= vol_prev * 1.2),
            (f'收{c:.0f}>Box5H{box5h:.0f}', c > box5h),
            ('5MA>10MA', ma5 > ma10),
            ('10MA>20MA', ma10 > ma20),
            ('收>20MA', c > ma20),
            ('OBV向上', bool(row['OBV_Up'])),
            ('RS>大盤', srs > mrs),
        ]
        n_pass = sum(1 for _, v in checks if v)
        verdict = ('🟢 進場訊號' if n_pass == 8
                   else f'🟡 差{8 - n_pass}項' if n_pass >= 6
                   else '⚪ 未達')
        results.append((name, ticker, bar_date, checks, verdict, n_pass, c, ma20))

    results_valid = [r for r in results if len(r) > 5]
    results_valid.sort(key=lambda r: -r[5])
    bar = results_valid[0][2] if results_valid else '?'
    print(f'\n每日訊號掃描  資料日期: {bar}')
    print('=' * 66)
    for r in results_valid:
        name, ticker, _, checks, verdict, n_pass, c, ma20 = r
        fails = [lbl for lbl, v in checks if not v]
        exit_flag = '  ⚠️持有者注意: 收盤已破月線' if 0 < ma20 and c < ma20 else ''
        print(f'\n{verdict}  {name}（{ticker}）  {n_pass}/8{exit_flag}')
        if fails and n_pass >= 6:
            print(f'    缺: {"、".join(fails)}')
    unresolved = [r[0] for r in results if len(r) <= 5]
    if unresolved:
        print(f'\n❓ 無法掃描（ticker未確認）: {"、".join(unresolved)}')
    print('\n提醒：盤中執行時當日量未完整，收盤後跑才準。')


def main():
    ap = argparse.ArgumentParser(description='台股回測系統 正式版引擎')
    sub = ap.add_subparsers(dest='cmd', required=True)

    bt = sub.add_parser('backtest', help='執行回測')
    bt.add_argument('--stocks', default='core', help='core 或逗號分隔股名')
    bt.add_argument('--years', nargs='+', default=['2024', '2025'])
    bt.add_argument('--next-open', action='store_true', help='次日開盤執行（較貼近現實）')
    bt.add_argument('--charts', action='store_true', help='輸出圖表到 charts/')
    bt.add_argument('--tag', default=None, help='輸出檔名標籤')

    sc = sub.add_parser('scan', help='每日進場訊號掃描')
    sc.add_argument('--stocks', default=None, help='逗號分隔股名（預設用內建觀察清單）')

    args = ap.parse_args()
    if args.cmd == 'backtest':
        cmd_backtest(args)
    else:
        cmd_scan(args)


if __name__ == '__main__':
    main()
