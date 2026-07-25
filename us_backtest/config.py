#!/usr/bin/env python3
"""
美股回測系統 — 策略參數設定
所有可調參數集中在此，方便修改與回測比較。
"""

# ── 策略參數 ─────────────────────────────────────────────────────
CFG = dict(
    # 市場基準
    MARKET='^GSPC',              # S&P 500

    # 交易成本（Firstrade 零佣金）
    FEE=0.0,                     # 手續費
    TAX=0.0,                     # 交易稅（美股無）
    SLIPPAGE=0.0005,             # 滑價 0.05%（單邊）

    # 資金管理
    CASH_BALANCE=1504.81,        # 未投入現金餘額 USD (Firstrade)
    MAX_CAP=30_000,              # 初始資金 USD
    RISK_PCT=0.01,               # 單筆風險 = 帳戶總淨值 1%（約 $305）
    MAX_POSITIONS=5,             # 最多同時持倉檔數
    MAX_SINGLE_PCT=0.25,         # 單檔最大部位 = 帳戶 25%

    # 進場指標參數
    EMA_FAST=20,                 # 快速 EMA
    EMA_MID=50,                  # 中期 EMA（趨勢線）
    EMA_SLOW=100,                # 慢速 EMA
    BOX_WIN=10,                  # Box 突破窗口（日）
    VOL_WIN=5,                   # 成交量均線窗口
    OBV_WIN=10,                  # OBV 均線窗口
    RS_WIN=20,                   # 相對強度窗口（日）

    # 出場 / 停損
    ATR_PERIOD=14,               # ATR 計算週期
    ATR_SL_MULT=2.0,             # ATR 停損倍數（2×ATR）
    HARD_SL=-0.10,               # 硬停損 -10%（最後防線）
    PROFIT_T1=0.15,              # 部分停利門檻 1：+15%
    PROFIT_T1_FRAC=0.20,         # 賣出 20%
    PROFIT_T2=0.40,              # 部分停利門檻 2：+40%
    PROFIT_T2_FRAC=0.50,         # 賣出 50%
    PROFIT_LOCK=0.20,            # 高檔出場：+20% + 放量 + 跌破 EMA20
)

# ── 目前持倉（Firstrade 帳戶）────────────────────────────────────
HOLDINGS = {
    'AMKR': {'shares': 30, 'cost': 72.46,  'name': 'Amkor Technology'},
    'AVGO': {'shares': 6,  'cost': 394.00, 'name': 'Broadcom'},
    'COHR': {'shares': 10, 'cost': 381.81, 'name': 'Coherent'},
    'CRWD': {'shares': 4,  'cost': 167.63, 'name': 'CrowdStrike'},
    'MSFT': {'shares': 6,  'cost': 407.41, 'name': 'Microsoft'},
    'MU':   {'shares': 6,  'cost': 913.38, 'name': 'Micron'},
    'ON':   {'shares': 30, 'cost': 99.05,  'name': 'ON Semi'},
    'QQQ':  {'shares': 5,  'cost': 604.54, 'name': 'Invesco QQQ ETF'},
    'TSLA': {'shares': 4,  'cost': 408.27, 'name': 'Tesla'},
    'TSM':  {'shares': 15, 'cost': 400.52, 'name': 'TSMC'},
}

# ── 觀察清單 ─────────────────────────────────────────────────────
WATCHLIST = list(HOLDINGS.keys()) + [
    # AI / 半導體龍頭
    'NVDA', 'AMD', 'ASML', 'KLAC', 'LRCX',
    # 科技大型股
    'AAPL', 'GOOGL', 'META', 'AMZN',
    # ETF 基準
    'SPY',
]
