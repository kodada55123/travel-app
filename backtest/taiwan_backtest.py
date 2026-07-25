"""
台股回測系統 - 2026年以來
策略：實體K線突破 + 量能爆增 + OBV上彎 + 籌碼集中度過濾
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

# ─── 設定中文字型 ────────────────────────────────────────────────
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang TC', 'Heiti TC', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ════════════════════════════════════════════════════════════════
# 參數設定
# ════════════════════════════════════════════════════════════════
TICKERS       = ['6658.TW', '6719.TW', '8299.TW', '2425.TW']
START_DATE    = '2026-01-01'
END_DATE      = pd.Timestamp.today().strftime('%Y-%m-%d')
INIT_CAPITAL  = 1_000_000   # 初始資金 100 萬台幣
FEE_RATE      = 0.001425    # 手續費 0.1425%
TAX_RATE      = 0.003       # 交易稅 0.3%（僅賣出）
STOP_LOSS     = -0.03       # 強制止損 -3%
BODY_DROP_EXIT = 0.04       # 實體跌幅出場 >4%
CONSOL_WINDOW  = 20         # 盤整區間天數
BODY_LOOKBACK  = 5          # 實體高點回看天數
VOL_MULT       = 3.0        # 量能倍數門檻

# ════════════════════════════════════════════════════════════════
# 指標計算函式
# ════════════════════════════════════════════════════════════════

def calc_obv(df):
    """計算 OBV（On-Balance Volume）"""
    obv = [0]
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
            obv.append(obv[-1] + df['Volume'].iloc[i])
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
            obv.append(obv[-1] - df['Volume'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)


def obv_turning_up(obv_series, window=3):
    """
    OBV 明顯上彎：當日 OBV > 過去 window 日 OBV 平均，
    且 OBV 斜率（當日 - window日前）為正。
    """
    obv_ma  = obv_series.rolling(window).mean()
    obv_slope = obv_series - obv_series.shift(window)
    return (obv_series > obv_ma) & (obv_slope > 0)


def chip_concentration_proxy(df, window=10):
    """
    籌碼集中度代理指標（無法取得券商進出資料時的替代方案）：
    用「量加權平均成本距離」近似：
        若近期成交量集中在較高價位 → 籌碼集中（正值）
        計算方式：(Close - VWMA(window)) / VWMA(window)
    正值代表目前收盤高於近期均成本 → 籌碼偏多方集中
    """
    vwma = (df['Close'] * df['Volume']).rolling(window).sum() / df['Volume'].rolling(window).sum()
    return (df['Close'] - vwma) / vwma


def body_high(df):
    """實體 K 線最高點（排除上影線）"""
    return df[['Open', 'Close']].max(axis=1)


def body_low(df):
    """實體 K 線最低點（排除下影線）"""
    return df[['Open', 'Close']].min(axis=1)


def rolling_body_high(df, window=5):
    """過去 window 日實體最高點"""
    bh = body_high(df)
    # 排除當日（用 shift(1) 取昨天往前 window 天）
    return bh.shift(1).rolling(window).max()


# ════════════════════════════════════════════════════════════════
# 核心回測函式
# ════════════════════════════════════════════════════════════════

def run_backtest(ticker, capital):
    """對單一標的執行回測，回傳 (trades_df, equity_series, df_with_signals)"""

    print(f"\n{'='*55}")
    print(f"  回測標的：{ticker}  ({START_DATE} ~ {END_DATE})")
    print(f"{'='*55}")

    # ── 1. 下載數據 ──────────────────────────────────────────────
    raw = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False, auto_adjust=True)
    if raw.empty or len(raw) < 30:
        print(f"  [警告] {ticker} 資料不足，跳過。")
        return None, None, None

    df = raw.copy()
    # yfinance 有時回傳 MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df.sort_index(inplace=True)

    # ── 2. 計算指標 ───────────────────────────────────────────────
    df['Body_High']     = body_high(df)
    df['Body_Low']      = body_low(df)
    df['OBV']           = calc_obv(df)
    df['OBV_Up']        = obv_turning_up(df['OBV'])
    df['Chip_Score']    = chip_concentration_proxy(df)
    df['Roll_Body_High']= rolling_body_high(df, BODY_LOOKBACK)
    df['Consol_Low']    = df['Low'].rolling(CONSOL_WINDOW).min().shift(1)
    df['Vol_Prev']      = df['Volume'].shift(1)

    # ── 3. 進場訊號 ───────────────────────────────────────────────
    cond_breakout = df['Close'] > df['Roll_Body_High']           # 突破實體高點
    cond_volume   = df['Volume'] > df['Vol_Prev'] * VOL_MULT     # 量能 > 前日 3 倍
    cond_obv      = df['OBV_Up']                                  # OBV 上彎
    cond_chip     = df['Chip_Score'] > 0                          # 籌碼集中度正值

    df['Signal'] = cond_breakout & cond_volume & cond_obv & cond_chip

    # ── 4. 模擬交易 ───────────────────────────────────────────────
    trades     = []
    equity     = capital
    in_trade   = False
    entry_price= 0.0
    entry_date = None
    shares     = 0

    equity_curve = []

    for i in range(len(df)):
        row  = df.iloc[i]
        date = df.index[i]

        # 記錄每日權益（equity 為持倉中的剩餘現金，加上持倉市值）
        if in_trade:
            equity_curve.append({'Date': date,
                                  'Equity': equity + shares * row['Close']})
        else:
            equity_curve.append({'Date': date, 'Equity': equity})

        if in_trade:
            ret_now = (row['Close'] - entry_price) / entry_price

            # 出場條件 1：跌破盤整區間下緣
            exit_consol = row['Close'] < row['Consol_Low'] if not pd.isna(row['Consol_Low']) else False

            # 出場條件 2：當日實體跌幅 > 4%
            body_ret    = (row['Close'] - row['Open']) / row['Open'] if row['Open'] > 0 else 0
            exit_body   = body_ret < -BODY_DROP_EXIT

            # 出場條件 3：強制止損 -3%
            exit_sl     = ret_now <= STOP_LOSS

            if exit_consol or exit_body or exit_sl:
                sell_price = row['Close']
                proceeds   = shares * sell_price * (1 - TAX_RATE) * (1 - FEE_RATE)
                pnl        = proceeds - shares * entry_price * (1 + FEE_RATE)
                equity    += proceeds

                reason = ('止損' if exit_sl else
                          '跌幅出場' if exit_body else
                          '盤整下緣')

                trades.append({
                    'Ticker'     : ticker,
                    'Entry_Date' : entry_date,
                    'Exit_Date'  : date,
                    'Entry_Price': round(entry_price, 2),
                    'Exit_Price' : round(sell_price,  2),
                    'Shares'     : shares,
                    'PnL'        : round(pnl, 0),
                    'Return_pct' : round(ret_now * 100, 2),
                    'Exit_Reason': reason,
                })
                in_trade = False

        else:
            if row['Signal'] and equity > 1000:
                # 以收盤價進場（隔日開盤更保守，這裡用當日收盤模擬）
                buy_price   = row['Close']
                invest      = min(equity, equity * 0.95)   # 最多用 95% 資金
                # 優先整張（1000股），若不足一張改用零股（1股為單位）
                lot_size    = 1000 if buy_price * 1000 * (1 + FEE_RATE) <= invest else 1
                shares      = int(invest / (buy_price * (1 + FEE_RATE) / lot_size)) * lot_size
                if shares == 0:
                    continue
                cost        = shares * buy_price * (1 + FEE_RATE)
                equity     -= cost
                entry_price = buy_price
                entry_date  = date
                in_trade    = True

    # 強制平倉（回測結束仍持倉）
    if in_trade:
        last_price = df['Close'].iloc[-1]
        proceeds   = shares * last_price * (1 - TAX_RATE) * (1 - FEE_RATE)
        pnl        = proceeds - shares * entry_price * (1 + FEE_RATE)
        equity    += proceeds
        ret_now    = (last_price - entry_price) / entry_price
        trades.append({
            'Ticker'     : ticker,
            'Entry_Date' : entry_date,
            'Exit_Date'  : df.index[-1],
            'Entry_Price': round(entry_price, 2),
            'Exit_Price' : round(last_price,  2),
            'Shares'     : shares,
            'PnL'        : round(pnl, 0),
            'Return_pct' : round(ret_now * 100, 2),
            'Exit_Reason': '回測結束',
        })

    trades_df    = pd.DataFrame(trades)
    equity_df    = pd.DataFrame(equity_curve).set_index('Date')
    return trades_df, equity_df, df


# ════════════════════════════════════════════════════════════════
# 績效指標計算
# ════════════════════════════════════════════════════════════════

def calc_metrics(trades_df, equity_df, init_capital):
    if trades_df is None or trades_df.empty:
        return {}

    final_equity = equity_df['Equity'].iloc[-1]
    total_return = (final_equity - init_capital) / init_capital * 100

    wins     = trades_df[trades_df['PnL'] > 0]
    losses   = trades_df[trades_df['PnL'] <= 0]
    win_rate = len(wins) / len(trades_df) * 100 if len(trades_df) > 0 else 0

    # 最大回撤
    roll_max = equity_df['Equity'].cummax()
    drawdown = (equity_df['Equity'] - roll_max) / roll_max
    mdd      = drawdown.min() * 100

    return {
        '總報酬率 (%)' : round(total_return, 2),
        '最終權益 (元)': int(final_equity),
        '勝率 (%)' : round(win_rate, 2),
        '最大回撤 MDD (%)': round(mdd, 2),
        '總交易次數': len(trades_df),
        '獲利次數'  : len(wins),
        '虧損次數'  : len(losses),
        '平均獲利 (元)': int(wins['PnL'].mean())   if len(wins)   > 0 else 0,
        '平均虧損 (元)': int(losses['PnL'].mean()) if len(losses) > 0 else 0,
        '總損益 (元)' : int(trades_df['PnL'].sum()),
    }


# ════════════════════════════════════════════════════════════════
# 圖表繪製
# ════════════════════════════════════════════════════════════════

def plot_results(ticker, df, trades_df, equity_df, metrics):
    if df is None:
        return

    fig, axes = plt.subplots(4, 1, figsize=(14, 18),
                             gridspec_kw={'height_ratios': [3, 1, 1, 1.5]})
    fig.suptitle(f'{ticker}  回測結果  ({START_DATE} ~ {END_DATE})',
                 fontsize=15, fontweight='bold', y=0.98)

    # ── 子圖 1：股價走勢 + 進出場點 ──────────────────────────────
    ax1 = axes[0]
    ax1.plot(df.index, df['Close'], color='#1f77b4', linewidth=1.2, label='收盤價')

    if trades_df is not None and not trades_df.empty:
        entries = trades_df.set_index('Entry_Date')['Entry_Price']
        exits   = trades_df.set_index('Exit_Date')['Exit_Price']

        for dt, price in entries.items():
            if dt in df.index:
                ax1.scatter(dt, price, marker='^', color='lime',
                            s=100, zorder=5)
        for dt, price in exits.items():
            if dt in df.index:
                ax1.scatter(dt, price, marker='v', color='red',
                            s=100, zorder=5)

    entry_patch = mpatches.Patch(color='lime', label='進場點 ▲')
    exit_patch  = mpatches.Patch(color='red',  label='出場點 ▼')
    ax1.legend(handles=[entry_patch, exit_patch], loc='upper left')
    ax1.set_ylabel('股價 (TWD)')
    ax1.grid(alpha=0.3)
    ax1.set_title('股價走勢與進出場點')

    # ── 子圖 2：成交量 ────────────────────────────────────────────
    ax2 = axes[1]
    colors = ['red' if c >= o else 'green'
              for c, o in zip(df['Close'], df['Open'])]
    ax2.bar(df.index, df['Volume'], color=colors, alpha=0.7, width=0.8)
    ax2.set_ylabel('成交量')
    ax2.set_title('成交量')
    ax2.grid(alpha=0.3)

    # ── 子圖 3：OBV ───────────────────────────────────────────────
    ax3 = axes[2]
    ax3.plot(df.index, df['OBV'], color='purple', linewidth=1)
    ax3.set_ylabel('OBV')
    ax3.set_title('OBV（On-Balance Volume）')
    ax3.grid(alpha=0.3)

    # ── 子圖 4：權益曲線 ──────────────────────────────────────────
    ax4 = axes[3]
    ax4.plot(equity_df.index, equity_df['Equity'],
             color='darkorange', linewidth=1.5, label='帳戶權益')
    ax4.axhline(INIT_CAPITAL, color='gray', linestyle='--',
                linewidth=0.8, label=f'初始資金 {INIT_CAPITAL:,}')
    ax4.fill_between(equity_df.index,
                     equity_df['Equity'], INIT_CAPITAL,
                     where=equity_df['Equity'] >= INIT_CAPITAL,
                     alpha=0.2, color='green')
    ax4.fill_between(equity_df.index,
                     equity_df['Equity'], INIT_CAPITAL,
                     where=equity_df['Equity'] < INIT_CAPITAL,
                     alpha=0.2, color='red')
    ax4.set_ylabel('帳戶資金 (TWD)')
    ax4.set_title('權益曲線')
    ax4.legend(loc='upper left')
    ax4.grid(alpha=0.3)

    # 在圖上加績效文字框
    if metrics:
        info = (f"總報酬率: {metrics['總報酬率 (%)']:+.2f}%\n"
                f"最大回撤: {metrics['最大回撤 MDD (%)']:.2f}%\n"
                f"勝率: {metrics['勝率 (%)']:.1f}%\n"
                f"交易次數: {metrics['總交易次數']}")
        ax4.text(0.01, 0.97, info, transform=ax4.transAxes,
                 verticalalignment='top', fontsize=9,
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    save_path = f'/Users/kochechin/Desktop/google/backtest/{ticker.replace(".TW","")}_result.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  圖表已儲存：{save_path}")


# ════════════════════════════════════════════════════════════════
# 主程式
# ════════════════════════════════════════════════════════════════

def main():
    all_metrics = {}
    all_trades  = []

    for ticker in TICKERS:
        trades_df, equity_df, df = run_backtest(ticker, INIT_CAPITAL)

        if trades_df is None:
            continue

        metrics = calc_metrics(trades_df, equity_df, INIT_CAPITAL)
        all_metrics[ticker] = metrics

        # 印出績效指標
        print(f"\n  ▶ 績效摘要：")
        for k, v in metrics.items():
            print(f"    {k:<20} {v:>12,}" if isinstance(v, (int, float)) else
                  f"    {k:<20} {v}")

        # 印出交易明細
        if not trades_df.empty:
            print(f"\n  ▶ 交易明細：")
            print(trades_df[['Entry_Date','Exit_Date','Entry_Price',
                              'Exit_Price','Shares','PnL',
                              'Return_pct','Exit_Reason']].to_string(index=False))
            all_trades.append(trades_df)

        plot_results(ticker, df, trades_df, equity_df, metrics)

    # ── 彙總所有標的 ─────────────────────────────────────────────
    print(f"\n{'='*55}")
    print("  全標的績效彙總")
    print(f"{'='*55}")
    summary = pd.DataFrame(all_metrics).T
    if not summary.empty:
        print(summary.to_string())

    if all_trades:
        combined = pd.concat(all_trades, ignore_index=True)
        wins  = combined[combined['PnL'] > 0]
        total_pnl = combined['PnL'].sum()
        print(f"\n  合計損益：{int(total_pnl):,} 元")
        print(f"  合計勝率：{len(wins)/len(combined)*100:.1f}%")


# ════════════════════════════════════════════════════════════════
# 優化建議（列印）
# ════════════════════════════════════════════════════════════════

OPTIMIZATION_NOTES = """
╔══════════════════════════════════════════════════════════╗
║             策略優化建議（降低最大回撤）                 ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. 加入均線趨勢過濾（EMA 20/60 多頭排列）              ║
║     → 只在股價站上 EMA20 且 EMA20 > EMA60 時進場，      ║
║       可過濾掉下跌趨勢中的假突破，預期降低 MDD 30~50%。 ║
║                                                          ║
║  2. 以 ATR 動態止損取代固定 3% 止損                     ║
║     → 止損價 = 進場價 - 1.5 × ATR(14)，                 ║
║       波動大時給更大空間、波動小時收緊保護，             ║
║       避免被短期雜訊打出後股價繼續上漲。                 ║
║                                                          ║
║  3. 大盤過濾（加權指數）                                 ║
║     → 當大盤（^TWII）跌破 20 日均線時暫停新進場，        ║
║       出場條件中「跌幅 >4% 但大盤大跌可排除」            ║
║       改以量化門檻（大盤當日跌 >1.5%）自動判斷，         ║
║       降低系統性風險帶來的損失。                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

if __name__ == '__main__':
    main()
    print(OPTIMIZATION_NOTES)
