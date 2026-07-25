"""
台股回測系統 v3c
加碼條件更新：OBV 未創新低加碼 → 需額外滿足「股價站上5MA」
進場=綠點 / OBV加碼=藍點 / 順勢加碼=青色點 / 出場=紅點
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS','PingFang TC','Heiti TC','sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

TICKERS = {
    '2454.TW': '聯發科',
    '3443.TW': '創意',
    '3665.TW': '貿聯KY',
    '2301.TW': '光寶科',
    '2308.TW': '台達電',
    '3661.TW': '世芯KY',
}
MARKET_TICKER   = '^TWII'
FEE_RATE        = 0.001425
TAX_RATE        = 0.003
MAX_CAP         = 5_000_000
INVEST_RATIO    = 0.30
STOP_LOSS_PCT   = -0.05
PROFIT_LOCK_PCT =  0.20
PARTIAL_10      =  0.10
PARTIAL_40      =  0.40
BIG_DROP_MKT    = -0.02
BODY_DROP_EXIT  =  0.05
RS_WINDOW       = 20

PERIODS = [
    ('2024-01-01', '2024-12-31'),
    ('2025-01-01', '2025-12-31'),
    ('2026-01-01', pd.Timestamp.today().strftime('%Y-%m-%d')),
]

# ── 工具 ─────────────────────────────────────────────────────────

def clean(raw):
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df.sort_index()

def calc_obv(df):
    obv = [0]
    for i in range(1, len(df)):
        if   df['Close'].iloc[i] > df['Close'].iloc[i-1]: obv.append(obv[-1] + df['Volume'].iloc[i])
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1]: obv.append(obv[-1] - df['Volume'].iloc[i])
        else: obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def body_high(df):
    return df[['Open','Close']].max(axis=1)

def buy_shares(invest, price):
    cp  = price * (1 + FEE_RATE)
    lot = 1000 if cp * 1000 <= invest else 1
    return int(invest / cp / lot) * lot

# ── Position ──────────────────────────────────────────────────────

class Position:
    def __init__(self):
        self.batches  = []
        self.p10_done = False
        self.p40_done = False

    @property
    def total_shares(self):
        return sum(b['shares'] for b in self.batches)

    def total_cost(self):
        return sum(b['shares'] * b['entry_price'] * (1 + FEE_RATE) for b in self.batches)

    def current_ret(self, price):
        tc = self.total_cost()
        return (price * self.total_shares - tc) / tc if tc else 0

    def market_value(self, price):
        return self.total_shares * price

    def first_entry_date(self):
        return self.batches[0]['entry_date'] if self.batches else None

    def is_empty(self):
        return self.total_shares == 0

    def obv_low_since_last(self, obv_series):
        if not self.batches: return False
        start = self.batches[-1]['entry_date']
        sub   = obv_series[obv_series.index >= start]
        return len(sub) > 1 and float(sub.iloc[-1]) <= float(sub.min())

    def add(self, shares, price, date):
        self.batches.append({'shares': shares, 'entry_price': price, 'entry_date': date})

    def sell_partial(self, ratio, price):
        to_sell  = max(1, int(self.total_shares * ratio))
        sold = proceeds = cost = 0
        for b in self.batches:
            if sold >= to_sell: break
            can = min(b['shares'], to_sell - sold)
            b['shares'] -= can
            sold     += can
            proceeds += can * price * (1 - TAX_RATE) * (1 - FEE_RATE)
            cost     += can * b['entry_price'] * (1 + FEE_RATE)
        self.batches = [b for b in self.batches if b['shares'] > 0]
        return sold, round(proceeds - cost, 0)

    def sell_all(self, price):
        return self.sell_partial(1.0, price)

    def clear(self):
        self.batches.clear()
        self.p10_done = self.p40_done = False

# ── 回測核心 ──────────────────────────────────────────────────────

def run_backtest(ticker, name, mkt_df):
    raw = yf.download(ticker,
                      start=mkt_df.index[0].strftime('%Y-%m-%d'),
                      end=mkt_df.index[-1].strftime('%Y-%m-%d'),
                      progress=False, auto_adjust=False)
    if raw.empty or len(raw) < 25:
        return None, None, None, None

    df = clean(raw)
    df['MA5']    = df['Close'].rolling(5).mean()
    df['MA10']   = df['Close'].rolling(10).mean()
    df['MA20']   = df['Close'].rolling(20).mean()
    df['Vol3']   = df['Volume'].rolling(3).mean()
    df['Vol5']   = df['Volume'].rolling(5).mean()
    df['BH']     = body_high(df)
    df['BoxH']   = df['BH'].shift(1).rolling(3).max()
    df['BoxL']   = df['Low'].shift(1).rolling(20).min()
    df['OBV']    = calc_obv(df)
    df['OBV_MA'] = df['OBV'].rolling(5).mean()
    df['OBV_Up'] = (df['OBV'] > df['OBV_MA']) & (df['OBV'] > df['OBV'].shift(5))
    df['StockRS']= df['Close'] / df['Close'].shift(RS_WINDOW)
    df = df.join(mkt_df[['Mkt_Ret','MktRS']], how='left')

    df['Signal'] = (
        (df['Volume'] > df['Vol3']) &
        (df['Volume'] >= df['Volume'].shift(1) * 1.2) &
        (df['Close']  > df['BoxH']) &
        (df['MA5']    > df['MA10']) & (df['MA10'] > df['MA20']) &
        (df['Close']  > df['MA20']) &
        df['OBV_Up'] &
        (df['StockRS'] > df['MktRS'])
    )

    capital = MAX_CAP
    pos     = Position()
    trades  = []
    events  = []
    eq_crv  = []

    for i in range(len(df)):
        row   = df.iloc[i]
        date  = df.index[i]
        close = float(row['Close'])
        ma5   = float(row['MA5'])  if not pd.isna(row['MA5'])  else 0
        ma10  = float(row['MA10']) if not pd.isna(row['MA10']) else 0

        eq_crv.append({'Date': date,
                       'Equity': capital + (pos.market_value(close) if not pos.is_empty() else 0)})

        mkt_ret      = float(row['Mkt_Ret']) if not pd.isna(row['Mkt_Ret']) else 0.0
        big_drop_mkt = mkt_ret < BIG_DROP_MKT
        vol5         = float(row['Vol5'])   if not pd.isna(row['Vol5']) else 0
        vol_today    = float(row['Volume'])
        body_ret     = (close - float(row['Open'])) / float(row['Open']) if float(row['Open']) > 0 else 0

        # ── 出場 ────────────────────────────────────────────────
        if not pos.is_empty():
            ret = pos.current_ret(close)

            # 分階停利 10%（獲利達10%）
            if not pos.p10_done and ret >= PARTIAL_10:
                sold, pnl = pos.sell_partial(0.10, close)
                if sold:
                    capital += sold * close * (1 - TAX_RATE) * (1 - FEE_RATE)
                    events.append({'Date': date, 'Price': close, 'Type': '停利10%'})
                    pos.p10_done = True

            # 分階停利 50%（獲利達40%）
            if not pos.p40_done and ret >= PARTIAL_40 and not pos.is_empty():
                sold, pnl = pos.sell_partial(0.50, close)
                if sold:
                    capital += sold * close * (1 - TAX_RATE) * (1 - FEE_RATE)
                    events.append({'Date': date, 'Price': close, 'Type': '停利40%'})
                    pos.p40_done = True

            if not pos.is_empty():
                ret = pos.current_ret(close)

            # 停利：≥20% 後跌破10MA + 放量
            exit_profit = (ret >= PROFIT_LOCK_PCT and vol_today > vol5 and close < ma10)
            # 跌破盤整下緣
            boxl      = float(row['BoxL']) if not pd.isna(row['BoxL']) else 0
            exit_box  = boxl > 0 and close < boxl
            # 急跌綠K
            exit_drop = (not big_drop_mkt and body_ret < -BODY_DROP_EXIT and vol_today > vol5)
            # 強制止損
            exit_sl   = ret <= STOP_LOSS_PCT

            reason = None
            if   exit_sl:     reason = '強制止損'
            elif exit_profit: reason = '停利(≥20%+跌破10MA)'
            elif exit_box:    reason = '跌破盤整下緣'
            elif exit_drop:   reason = '急跌綠K'

            if reason and not pos.is_empty():
                tc = pos.total_cost(); sh = pos.total_shares
                _, pnl = pos.sell_all(close)
                capital += sh * close * (1 - TAX_RATE) * (1 - FEE_RATE)
                trades.append({
                    'Entry_Date' : pos.first_entry_date(),
                    'Exit_Date'  : date,
                    'Avg_Cost'   : round(tc / sh / (1 + FEE_RATE), 2) if sh else 0,
                    'Exit_Price' : round(close, 2),
                    'Shares'     : sh,
                    'PnL'        : round(pnl, 0),
                    'Return_pct' : round(ret * 100, 2),
                    'Exit_Reason': reason,
                })
                events.append({'Date': date, 'Price': close, 'Type': 'exit'})
                pos.clear()

        # ── OBV 未創新低加碼（新增：需站上5MA）─────────────────
        if not pos.is_empty():
            if (pos.current_ret(close) < 0 and
                    not pos.obv_low_since_last(df['OBV'][:i+1]) and
                    close > ma5 and ma5 > 0 and          # ← 新增：站上5MA
                    capital >= MAX_CAP * 0.1):
                sh = buy_shares(capital * INVEST_RATIO, close)
                if sh > 0:
                    capital -= sh * close * (1 + FEE_RATE)
                    pos.add(sh, close, date)
                    events.append({'Date': date, 'Price': close, 'Type': 'add_obv'})

        # ── 進場 / 順勢加碼（訊號觸發）──────────────────────────
        if row['Signal'] and capital >= MAX_CAP * 0.1:
            ev_type = 'add_signal' if not pos.is_empty() else 'entry'
            sh = buy_shares(capital * INVEST_RATIO, close)
            if sh > 0:
                capital -= sh * close * (1 + FEE_RATE)
                pos.add(sh, close, date)
                events.append({'Date': date, 'Price': close, 'Type': ev_type})

    # 強制平倉
    if not pos.is_empty():
        last = float(df['Close'].iloc[-1])
        tc = pos.total_cost(); sh = pos.total_shares; ret = pos.current_ret(last)
        _, pnl = pos.sell_all(last)
        capital += sh * last * (1 - TAX_RATE) * (1 - FEE_RATE)
        trades.append({
            'Entry_Date': pos.first_entry_date(), 'Exit_Date': df.index[-1],
            'Avg_Cost': round(tc/sh/(1+FEE_RATE), 2) if sh else 0,
            'Exit_Price': round(last, 2), 'Shares': sh,
            'PnL': round(pnl, 0), 'Return_pct': round(ret*100, 2), 'Exit_Reason': '回測結束',
        })
        events.append({'Date': df.index[-1], 'Price': last, 'Type': 'exit'})

    return (pd.DataFrame(trades),
            pd.DataFrame(eq_crv).set_index('Date'),
            df,
            pd.DataFrame(events) if events else pd.DataFrame())

# ── 績效 ──────────────────────────────────────────────────────────

def calc_metrics(trades_df, equity_df):
    if trades_df is None or trades_df.empty: return {}
    init  = MAX_CAP; final = equity_df['Equity'].iloc[-1]
    wins  = trades_df[trades_df['PnL'] > 0]
    losses= trades_df[trades_df['PnL'] <= 0]
    wr    = len(wins)/len(trades_df)*100 if len(trades_df) else 0
    mdd   = ((equity_df['Equity'] - equity_df['Equity'].cummax()) /
              equity_df['Equity'].cummax()).min() * 100
    return {
        '總報酬率 (%)':     round((final-init)/init*100, 2),
        '最終權益 (元)':    int(final),
        '勝率 (%)':         round(wr, 2),
        '最大回撤 MDD (%)': round(mdd, 2),
        '總交易次數':        len(trades_df),
        '獲利次數':          len(wins),
        '虧損次數':          len(losses),
        '最大單筆獲利 (元)': int(wins['PnL'].max())   if len(wins)   else 0,
        '最大單筆虧損 (元)': int(losses['PnL'].min()) if len(losses) else 0,
        '平均獲利 (元)':    int(wins['PnL'].mean())   if len(wins)   else 0,
        '平均虧損 (元)':    int(losses['PnL'].mean()) if len(losses) else 0,
        '總損益 (元)':      int(trades_df['PnL'].sum()),
    }

# ── 圖表 ──────────────────────────────────────────────────────────

# 事件樣式：顏色 / 標記 / 大小 / zorder / 說明
EVENT_STYLE = {
    'entry'     : ('#00cc00', '^', 160, 6, '首次進場 ▲'),
    'add_signal': ('#00ffff', '^', 130, 5, '順勢加碼 ▲'),   # 青色
    'add_obv'   : ('#1e90ff', '^', 120, 5, 'OBV加碼 ▲'),    # 藍色
    'exit'      : ('#ff2222', 'v', 160, 6, '出場 ▼'),
    '停利10%'   : ('#ffd700', 'D',  85, 5, '停利10% ◆'),
    '停利40%'   : ('#ff8c00', 'D', 110, 5, '停利40% ◆'),
}

def plot_results(ticker, name, df, trades_df, equity_df, events_df, metrics, start, end):
    fig, axes = plt.subplots(5, 1, figsize=(15, 22),
                             gridspec_kw={'height_ratios': [3.5, 1, 1, 1, 1.5]})
    yr = start[:4]
    fig.suptitle(f'{name}（{ticker.replace(".TW","")}）  v3c 策略  {start} ~ {end}',
                 fontsize=14, fontweight='bold', y=0.99)

    # ── 子圖 1：股價 + 均線 + 所有事件點 ─────────────────────
    ax1 = axes[0]
    ax1.plot(df.index, df['Close'], color='#1f77b4', lw=1.3, label='收盤價', zorder=2)
    for col, clr, lbl in [('MA5','orange','MA5'),('MA10','purple','MA10'),('MA20','green','MA20')]:
        ax1.plot(df.index, df[col], color=clr, lw=0.9, ls='--', alpha=0.85, label=lbl)

    if events_df is not None and not events_df.empty:
        for _, ev in events_df.iterrows():
            s = EVENT_STYLE.get(ev['Type'])
            if s:
                ax1.scatter(ev['Date'], ev['Price'],
                            color=s[0], marker=s[1], s=s[2], zorder=s[3],
                            edgecolors='black' if ev['Type'] in ('entry','exit') else 'none',
                            linewidths=0.5)

    handles, labels = ax1.get_legend_handles_labels()
    extra = [mpatches.Patch(color=v[0], label=v[4]) for v in EVENT_STYLE.values()]
    ax1.legend(handles + extra, labels + [e.get_label() for e in extra],
               loc='upper left', fontsize=7.5, ncol=2)
    ax1.set_ylabel('股價 (TWD)')
    ax1.set_title('股價走勢、均線與進出場點\n（綠=首次進場 / 青=順勢加碼 / 藍=OBV加碼 / 紅=出場）')
    ax1.grid(alpha=0.3)

    # ── 子圖 2：成交量 ───────────────────────────────────────
    ax2 = axes[1]
    clrs = ['red' if c >= o else 'green' for c, o in zip(df['Close'], df['Open'])]
    ax2.bar(df.index, df['Volume'], color=clrs, alpha=0.65, width=0.8)
    ax2.plot(df.index, df['Vol5'], color='navy',  lw=1,   label='5日均量')
    ax2.plot(df.index, df['Vol3'], color='brown', lw=0.9, ls=':', label='3日均量')
    ax2.legend(fontsize=8)
    ax2.set_ylabel('成交量'); ax2.set_title('成交量 vs 均量'); ax2.grid(alpha=0.3)

    # ── 子圖 3：OBV ─────────────────────────────────────────
    ax3 = axes[2]
    ax3.plot(df.index, df['OBV'],    color='purple', lw=1.1, label='OBV')
    ax3.plot(df.index, df['OBV_MA'], color='red',    lw=0.9, ls='--', label='OBV MA5')
    ax3.fill_between(df.index, df['OBV'], df['OBV_MA'],
                     where=df['OBV'] >= df['OBV_MA'], alpha=0.2, color='green')
    ax3.legend(fontsize=8)
    ax3.set_ylabel('OBV'); ax3.set_title('OBV（能量潮）'); ax3.grid(alpha=0.3)

    # ── 子圖 4：RS 相對強弱 ──────────────────────────────────
    ax4 = axes[3]
    rs_diff = df['StockRS'] - df['MktRS']
    ax4.fill_between(df.index, rs_diff, 0, where=rs_diff >= 0, color='limegreen', alpha=0.6, label='強於大盤')
    ax4.fill_between(df.index, rs_diff, 0, where=rs_diff <  0, color='salmon',    alpha=0.5, label='弱於大盤')
    ax4.axhline(0, color='gray', lw=0.8)
    ax4.legend(fontsize=8)
    ax4.set_ylabel('RS差值'); ax4.set_title(f'個股 vs 大盤相對強弱（{RS_WINDOW}日漲幅差）'); ax4.grid(alpha=0.3)

    # ── 子圖 5：權益曲線 ─────────────────────────────────────
    ax5 = axes[4]
    init = MAX_CAP
    ax5.plot(equity_df.index, equity_df['Equity'], color='darkorange', lw=1.5, label='帳戶權益')
    ax5.axhline(init, color='gray', ls='--', lw=0.8, label=f'初始資金 {init:,}')
    ax5.fill_between(equity_df.index, equity_df['Equity'], init,
                     where=equity_df['Equity'] >= init, alpha=0.2, color='green')
    ax5.fill_between(equity_df.index, equity_df['Equity'], init,
                     where=equity_df['Equity'] <  init, alpha=0.2, color='red')
    ax5.set_ylabel('帳戶資金 (TWD)'); ax5.set_title('權益曲線')
    ax5.legend(loc='upper left', fontsize=8); ax5.grid(alpha=0.3)
    if metrics:
        txt = (f"總報酬率: {metrics.get('總報酬率 (%)',0):+.2f}%\n"
               f"MDD: {metrics.get('最大回撤 MDD (%)',0):.2f}%\n"
               f"勝率: {metrics.get('勝率 (%)',0):.1f}%\n"
               f"總交易: {metrics.get('總交易次數',0)} 筆\n"
               f"總損益: {metrics.get('總損益 (元)',0):,} 元")
        ax5.text(0.01, 0.97, txt, transform=ax5.transAxes, va='top', fontsize=9,
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.88))

    plt.tight_layout(rect=[0, 0, 1, 0.98])
    path = f'/Users/kochechin/Desktop/google/backtest/{ticker.replace(".TW","")}_v3c_{yr}.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  圖表已儲存：{path}")

# ── 主程式 ────────────────────────────────────────────────────────

def main():
    grand = {}

    for (start, end) in PERIODS:
        yr = start[:4]
        print(f"\n{'#'*68}\n  回測期間：{start} ~ {end}\n{'#'*68}")

        raw_mkt = yf.download(MARKET_TICKER, start=start, end=end,
                              progress=False, auto_adjust=False)
        mkt = clean(raw_mkt)
        mkt['Mkt_Ret'] = mkt['Close'].pct_change()
        mkt['MktRS']   = mkt['Close'] / mkt['Close'].shift(RS_WINDOW)

        period_metrics = {}
        all_trades     = []

        for ticker, name in TICKERS.items():
            print(f"\n{'='*62}\n  {name} ({ticker})\n{'='*62}")

            result = run_backtest(ticker, name, mkt)
            if result[0] is None:
                print("  [警告] 資料不足，跳過。"); continue

            trades_df, equity_df, df, events_df = result
            df        = df[(df.index >= start)        & (df.index <= end)]
            equity_df = equity_df[(equity_df.index >= start) & (equity_df.index <= end)]

            metrics = calc_metrics(trades_df, equity_df)
            period_metrics[name] = metrics

            print("  ▶ 績效摘要：")
            if metrics:
                for k, v in metrics.items():
                    print(f"    {k:<24} {v:>14,}" if isinstance(v,(int,float)) else f"    {k:<24} {v}")
            else:
                print("    本期間無觸發進場訊號")

            if trades_df is not None and not trades_df.empty:
                print("  ▶ 交易明細：")
                cols = ['Entry_Date','Exit_Date','Avg_Cost','Exit_Price','Shares','PnL','Return_pct','Exit_Reason']
                print(trades_df[[c for c in cols if c in trades_df.columns]].to_string(index=False))
                all_trades.append(trades_df)

            plot_results(ticker, name, df, trades_df, equity_df, events_df, metrics, start, end)

        print(f"\n{'='*68}\n  {yr} 年度彙總\n{'='*68}")
        summary = pd.DataFrame(period_metrics).T
        if not summary.empty:
            cols = ['總報酬率 (%)','最終權益 (元)','勝率 (%)','最大回撤 MDD (%)','總交易次數','總損益 (元)']
            print(summary[[c for c in cols if c in summary.columns]].to_string())
        if all_trades:
            combined = pd.concat(all_trades, ignore_index=True)
            wins = combined[combined['PnL'] > 0]
            print(f"\n  合計損益：{int(combined['PnL'].sum()):,} 元")
            print(f"  整體勝率：{len(wins)/len(combined)*100:.1f}%  ({len(wins)}/{len(combined)} 筆)")

        grand[yr] = period_metrics

    # 三年橫向對比
    print(f"\n{'#'*68}\n  三年橫向報酬率對比\n{'#'*68}")
    rows = {}
    for yr, pm in grand.items():
        for name, m in pm.items():
            if name not in rows: rows[name] = {}
            rows[name][yr] = m.get('總報酬率 (%)', 'N/A')
    df_cmp = pd.DataFrame(rows).T
    df_cmp.columns = [f'{c}年報酬率(%)' for c in df_cmp.columns]
    print(df_cmp.to_string())

    # 三年損益加總
    print(f"\n  三年各標的損益加總：")
    total_rows = {}
    for yr, pm in grand.items():
        for name, m in pm.items():
            if name not in total_rows: total_rows[name] = 0
            total_rows[name] += m.get('總損益 (元)', 0)
    for name, total in sorted(total_rows.items(), key=lambda x: -x[1]):
        print(f"    {name:<10} {int(total):>12,} 元")

if __name__ == '__main__':
    main()
