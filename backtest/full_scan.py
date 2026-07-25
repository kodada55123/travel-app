#!/usr/bin/env python3
"""
全台股 RS 掃描器 — 掃描台股主要個股，找出 RS 強於大盤 + 符合進場條件的標的
涵蓋：台灣50成分股 + 中型100 + 上櫃熱門 + 各產業代表
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── 台股主要個股清單（約 150 檔涵蓋各產業） ──
SCAN_LIST = {
    # ===== 半導體 =====
    '台積電': '2330.TW', '聯發科': '2454.TW', '日月光投控': '3711.TW',
    '聯電': '2303.TW', '南亞科': '2408.TW', '環球晶': '6488.TWO',
    '力積電': '6770.TW', '世芯KY': '3661.TW', '創意': '3443.TW',
    '祥碩': '5269.TW', '瑞昱': '2379.TW', '聯詠': '3034.TW',
    '群聯': '8299.TWO', '矽力KY': '6415.TW', '力智': '6719.TW',
    '譜瑞KY': '4966.TW', '信驊': '5274.TW', '晶技': '3042.TW',
    '穩懋': '3105.TW', '辛耘': '3583.TW', '弘塑': '3131.TW',
    '家登': '3680.TW', '漢唐': '2404.TW', '帆宣': '6196.TW',
    '盛群': '6202.TW', '松翰': '5471.TW', '凌通': '4952.TW',
    '欣銓': '3264.TWO', '京元電子': '2449.TW',
    # ===== AI 伺服器/網通 =====
    '廣達': '2382.TW', '緯穎': '6669.TW', '英業達': '2356.TW',
    '緯創': '3231.TW', '智邦': '2345.TW', '光寶科': '2301.TW',
    '微星': '2377.TW', '技嘉': '2376.TW', '華碩': '2357.TW',
    '仁寶': '2324.TW', '神達': '3706.TW', '事欣科': '4916.TW',
    # ===== AI 散熱/機構件 =====
    '奇鋐': '3017.TW', '雙鴻': '3324.TW', '建準': '2421.TW',
    '超眾': '6230.TW', '順達': '3211.TWO',
    # ===== 連接器/線束 =====
    '貿聯KY': '3665.TW', '嘉澤': '3533.TW', '信邦': '3023.TW',
    # ===== PCB/載板/CCL =====
    '台光電': '2383.TW', '台燿': '6274.TWO', '臻鼎KY': '4958.TW',
    '金像電': '2368.TW', '華通': '2313.TW', '聯茂': '6213.TW',
    '金居': '8358.TWO', '景碩': '3228.TW', '南電': '8046.TW',
    '博智': '8155.TW', '志超': '8213.TW',
    # ===== 面板/顯示 =====
    '群創': '3481.TW', '友達': '2409.TW', '瀚宇博': '5765.TW',
    # ===== 光學/鏡頭 =====
    '大立光': '3008.TW', '玉晶光': '3406.TW', '亞光': '3019.TW',
    # ===== 被動元件 =====
    '國巨': '2327.TW', '華新科': '2492.TW', '奇力新': '2456.TW',
    # ===== 記憶體/DRAM =====
    '南亞': '1303.TW', '華邦電': '2344.TW', '旺宏': '2337.TW',
    # ===== 電信 =====
    '中華電': '2412.TW', '台灣大': '3045.TW', '遠傳': '4904.TW',
    # ===== 金融 =====
    '富邦金': '2881.TW', '國泰金': '2882.TW', '中信金': '2891.TW',
    '兆豐金': '2886.TW', '玉山金': '2884.TW', '台新金': '2887.TW',
    '元大金': '2885.TW', '第一金': '2892.TW', '合庫金': '5880.TW',
    '開發金': '2883.TW', '華南金': '2880.TW',
    # ===== 傳產/鋼鐵/塑化 =====
    '台塑': '1301.TW', '台化': '1326.TW', '台塑化': '6505.TW',
    '中鋼': '2002.TW', '統一': '1216.TW', '遠東新': '1402.TW',
    '亞泥': '1102.TW', '台泥': '1101.TW',
    # ===== 航運 =====
    '長榮': '2603.TW', '陽明': '2609.TW', '萬海': '2615.TW',
    '長榮航': '2618.TW', '華航': '2610.TW',
    # ===== 汽車/電動車 =====
    '裕隆': '2201.TW', '和泰車': '2207.TW', '裕日車': '2227.TW',
    # ===== 生技醫療 =====
    '藥華藥': '6446.TW', '保瑞': '6472.TW', '合一': '4743.TWO',
    '中裕': '4147.TWO', '長聖': '6712.TW',
    # ===== 食品/民生 =====
    '統一超': '2912.TW', '大統益': '1232.TW',
    # ===== 營建/資產 =====
    '興富發': '2542.TW', '華固': '2548.TW', '長虹': '5534.TW',
    '達麗': '6177.TW', '南港': '2101.TW',
    # ===== 綠能/電力 =====
    '台汽電': '8926.TW',
    # ===== 其他熱門 =====
    '鴻海': '2317.TW', '台達電': '2308.TW', '研華': '2395.TW',
    '大聯大': '3702.TW', '定穎投控': '3511.TW', '穎崴': '6515.TWO',
    '博大': '8109.TW', '健鼎': '3044.TW', '新普': '6121.TW',
    '鼎翰': '3611.TW', '中磊': '5388.TW',
}

RS_WIN = 20
MARKET = '^TWII'

def clean(raw):
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df.sort_index()

def calc_obv(df):
    obv = [0]
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
            obv.append(obv[-1] + df['Volume'].iloc[i])
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
            obv.append(obv[-1] - df['Volume'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

# ── 下載大盤 ──
print("📡 下載大盤數據...", file=sys.stderr)
mkt_raw = yf.download(MARKET, period='6mo', progress=False, auto_adjust=False)
mkt = clean(mkt_raw)
mkt = mkt[mkt['Volume'] > 0]
mkt_rs = float(mkt['Close'].iloc[-1]) / float(mkt['Close'].iloc[-RS_WIN])
mkt_ret = (mkt_rs - 1) * 100
mkt_today = float(mkt['Close'].pct_change().iloc[-1] * 100)
mkt_close = float(mkt['Close'].iloc[-1])
mkt_ma20 = float(mkt['Close'].rolling(20).mean().iloc[-1])

print(f"\n{'='*75}")
print(f"  📊 全台股 RS 掃描  資料日期: {mkt.index[-1].strftime('%Y-%m-%d')}")
print(f"  大盤 ^TWII: {mkt_close:,.0f}  20日: {mkt_ret:+.2f}%  今日: {mkt_today:+.2f}%  {'📈站上' if mkt_close > mkt_ma20 else '📉跌破'}月線")
print(f"{'='*75}")

# ── 下載所有個股（多線程加速）──
print(f"\n📡 下載 {len(SCAN_LIST)} 檔個股數據（多線程）...", file=sys.stderr)

def fetch_stock(name, ticker):
    try:
        raw = yf.download(ticker, period='6mo', progress=False, auto_adjust=False)
        if raw.empty or len(raw) < RS_WIN + 5:
            return None
        df = clean(raw)
        df = df[df['Volume'] > 0]
        if len(df) < RS_WIN + 5:
            return None

        close = float(df['Close'].iloc[-1])
        close_20d = float(df['Close'].iloc[-RS_WIN])
        rs = close / close_20d
        ret_20d = (rs - 1) * 100

        # 均線
        ma5  = float(df['Close'].rolling(5).mean().iloc[-1])
        ma10 = float(df['Close'].rolling(10).mean().iloc[-1])
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])

        # 量能
        vol = float(df['Volume'].iloc[-1])
        vol3 = float(df['Volume'].rolling(3).mean().iloc[-1])
        vol5 = float(df['Volume'].rolling(5).mean().iloc[-1])
        prev_vol = float(df['Volume'].iloc[-2])

        # Box5H
        bh = df[['Open', 'Close']].max(axis=1)
        box5h = float(bh.shift(1).rolling(5).max().iloc[-1])

        # OBV
        obv = calc_obv(df)
        obv_ma5 = float(obv.rolling(5).mean().iloc[-1])
        obv_now = float(obv.iloc[-1])
        obv_5ago = float(obv.iloc[-6]) if len(obv) > 5 else 0

        today_ret = float(df['Close'].pct_change().iloc[-1] * 100)
        open_price = float(df['Open'].iloc[-1])

        # 8 條件檢查
        c1 = vol > vol3                              # 量 > 3日均量
        c2 = vol >= prev_vol * 1.2                    # 量加速
        c3 = close > box5h                            # 突破 Box5H
        c4 = ma5 > ma10 > ma20                        # 均線多頭
        c5 = close > ma20                              # 站上月線
        c6 = obv_now > obv_ma5 and obv_now > obv_5ago # OBV 向上
        c7 = rs > mkt_rs                               # RS > 大盤
        conditions = [c1, c2, c3, c4, c5, c6, c7]
        n_pass = sum(conditions)

        return {
            'name': name, 'ticker': ticker, 'close': close,
            'ret_20d': ret_20d, 'rs': rs, 'stronger': rs > mkt_rs,
            'ma5': ma5, 'ma10': ma10, 'ma20': ma20,
            'above_ma20': close > ma20, 'ma_bull': ma5 > ma10 > ma20,
            'vol': vol, 'vol3': vol3, 'today_ret': today_ret,
            'n_pass': n_pass, 'conditions': conditions,
            'c_labels': ['量>3日均', '量加速', '突破Box5H', '均線多頭', '站上月線', 'OBV向上', 'RS>大盤'],
        }
    except Exception:
        return None

results = []
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(fetch_stock, n, t): n for n, t in SCAN_LIST.items()}
    done = 0
    for f in as_completed(futures):
        done += 1
        if done % 20 == 0:
            print(f"  已完成 {done}/{len(SCAN_LIST)}...", file=sys.stderr)
        r = f.result()
        if r:
            results.append(r)

print(f"  ✅ 成功取得 {len(results)}/{len(SCAN_LIST)} 檔", file=sys.stderr)

# ── 分析結果 ──

# 1. 進場訊號（7/7 或 6/7）
signals = [r for r in results if r['n_pass'] >= 6]
signals.sort(key=lambda x: x['n_pass'], reverse=True)

print(f"\n{'='*75}")
print(f"  🟢 進場訊號掃描（≥ 6/7 條件）")
print(f"{'='*75}")

if signals:
    for r in signals:
        icon = '🟢' if r['n_pass'] >= 7 else '🟡'
        missing = [r['c_labels'][i] for i, c in enumerate(r['conditions']) if not c]
        miss_str = f"  缺: {', '.join(missing)}" if missing else ""
        print(f"  {icon} {r['n_pass']}/7  {r['name']:<8} ({r['ticker']:<10}) 收盤:{r['close']:>8.1f}  20日:{r['ret_20d']:>+6.2f}%  今日:{r['today_ret']:>+5.2f}%{miss_str}")
else:
    print(f"  ⚠️ 今日全市場無 6/7 以上的進場訊號")

# 2. RS 強於大盤 + 站上月線
strong_rs = [r for r in results if r['stronger'] and r['above_ma20']]
strong_rs.sort(key=lambda x: x['ret_20d'], reverse=True)

print(f"\n{'='*75}")
print(f"  🏆 RS 強於大盤 + 站上月線（{len(strong_rs)} 檔）")
print(f"{'='*75}")
print(f"  {'個股':<8} {'代碼':<10} {'收盤':>8} {'20日漲幅':>8} {'超額RS':>8} {'均線多頭':>6} {'條件':>4} {'今日':>6}")
print(f"  {'-'*68}")

for r in strong_rs[:30]:
    ma_icon = '✅' if r['ma_bull'] else '—'
    print(f"  {r['name']:<8} {r['ticker']:<10} {r['close']:>8.1f} {r['ret_20d']:>+7.2f}% {r['ret_20d']-mkt_ret:>+7.2f}% {ma_icon:>6} {r['n_pass']:>3}/7 {r['today_ret']:>+5.2f}%")

# 3. RS 強但跌破月線（潛力反轉觀察）
strong_below = [r for r in results if r['stronger'] and not r['above_ma20']]
strong_below.sort(key=lambda x: x['ret_20d'], reverse=True)

if strong_below:
    print(f"\n{'='*75}")
    print(f"  👀 RS 強於大盤但跌破月線（觀察名單，{len(strong_below)} 檔）")
    print(f"{'='*75}")
    for r in strong_below[:15]:
        print(f"  {r['name']:<8} {r['ticker']:<10} {r['close']:>8.1f} {r['ret_20d']:>+7.2f}% {r['ret_20d']-mkt_ret:>+7.2f}%  條件:{r['n_pass']}/7  今日:{r['today_ret']:>+5.2f}%")

# 4. 均線多頭排列
bull_ma = [r for r in results if r['ma_bull']]
bull_ma.sort(key=lambda x: x['ret_20d'], reverse=True)

print(f"\n{'='*75}")
print(f"  📈 均線多頭排列（5MA>10MA>20MA）的個股（{len(bull_ma)} 檔）")
print(f"{'='*75}")
for r in bull_ma[:20]:
    rs_icon = '✅' if r['stronger'] else '❌'
    print(f"  {rs_icon} {r['name']:<8} {r['ticker']:<10} {r['close']:>8.1f} {r['ret_20d']:>+7.2f}%  RS{'強' if r['stronger'] else '弱'}  條件:{r['n_pass']}/7  今日:{r['today_ret']:>+5.2f}%")

# 5. 統計摘要
stronger_count = sum(1 for r in results if r['stronger'])
above_ma20_count = sum(1 for r in results if r['above_ma20'])
bull_count = len(bull_ma)

print(f"\n{'='*75}")
print(f"  📊 市場概況統計（共掃描 {len(results)} 檔）")
print(f"{'='*75}")
print(f"  RS 強於大盤:  {stronger_count}/{len(results)} ({stronger_count/len(results)*100:.1f}%)")
print(f"  站上月線:     {above_ma20_count}/{len(results)} ({above_ma20_count/len(results)*100:.1f}%)")
print(f"  均線多頭排列:  {bull_count}/{len(results)} ({bull_count/len(results)*100:.1f}%)")
print(f"  ≥6/7 進場條件: {len(signals)}/{len(results)}")

# 市場溫度
temp = above_ma20_count / len(results) * 100
if temp > 70:
    mood = "🔥 極度樂觀（過熱警戒）"
elif temp > 50:
    mood = "😊 偏多格局"
elif temp > 30:
    mood = "😐 中性偏弱"
elif temp > 15:
    mood = "😰 偏空格局"
else:
    mood = "🥶 極度悲觀（超跌反彈機會）"

print(f"\n  🌡️ 市場溫度: {temp:.1f}% 站上月線 → {mood}")
