#!/usr/bin/env python3
"""
每日 LINE 回報產生器 — 持股訊號 + 操作建議 + 新聞

輸出：印到 stdout 並寫入 /tmp/line_report.txt
操作建議依 STRATEGY.md 參數：
  ⛔ 停損   帳面 <= -8%（HARD_SL）
  ⚠️ 出場   收盤破月線（20MA）
  💰 減碼   +10% 停利 10%；+40% 停利 50%
  ➕ 加碼   持有獲利中且當日訊號 8/8
  🟢 開倉   未持有但訊號 8/8（掃描範圍內）
用法：
  /opt/homebrew/bin/python3 daily_report.py            # 持股掃描
  /opt/homebrew/bin/python3 daily_report.py --no-news  # 跳過新聞
"""
import re
import sys
import os
import urllib.request
import urllib.parse
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from sync_and_notify import fetch_data_js, parse_block, update_holdings, run_scan  # noqa: E402


def get_news(stock, code, n=2):
    """Google News RSS 抓個股新聞標題（含財報/營收消息）"""
    try:
        q = urllib.parse.quote(f'{stock} {code}' if code and code != '—' else stock)
        url = f'https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
        xml = urllib.request.urlopen(url, timeout=15).read().decode('utf-8')
        items = re.findall(r'<item>.*?<title>(.*?)</title>.*?<pubDate>(.*?)</pubDate>', xml, re.S)
        out = []
        for title, pub in items[:n]:
            title = title.replace('&amp;', '&').replace('&#39;', "'").replace('&quot;', '"')
            try:
                d = datetime.strptime(pub[5:16], '%d %b %Y').strftime('%m/%d')
            except Exception:
                d = ''
            out.append(f'· {d} {title[:52]}')
        return out
    except Exception:
        return []


def parse_scan(scan_out):
    """從 scan 輸出取出每檔的 n_pass 與破月線旗標"""
    info = {}
    for line in scan_out.split('\n'):
        m = re.match(r'[🟢🟡⚪❓].*?\s+(\S+)（[\d.A-Z]+\.TW[O]?）\s+(\d)/8(.*)', line.strip())
        if m:
            info[m.group(1)] = dict(n=int(m.group(2)), broke_ma20='破月線' in m.group(3))
    return info


def advice(p, sig):
    """依策略規則給操作建議"""
    tags = []
    if p['pct'] <= -8:
        tags.append(f'⛔ 停損！帳面 {p["pct"]}% 已破 -8% 硬停損')
    if sig and sig.get('broke_ma20'):
        tags.append('⚠️ 出場訊號：收盤破月線')
    if p['pct'] >= 40:
        tags.append('💰 減碼：達 +40% 門檻，停利 50%')
    elif p['pct'] >= 10:
        tags.append('💰 減碼：達 +10% 門檻，停利 10%')
    if not tags and sig and sig.get('n') == 8 and p['pct'] > 0:
        tags.append('➕ 可加碼：獲利中且訊號 8/8')
    if not tags:
        tags.append(f'✅ 續抱（訊號 {sig["n"]}/8）' if sig else '✅ 續抱')
    return tags


def main():
    no_news = '--no-news' in sys.argv
    src = fetch_data_js()
    updated = re.search(r'const LAST_UPDATED = "([^"]+)"', src).group(1)
    positions = parse_block(src, 'POSITIONS')
    trades = parse_block(src, 'TRADES')
    update_holdings(positions)

    holds = [p for p in positions if p.get('type') != 'ETF']
    total_pnl = sum(p['pnl'] for p in positions)
    total_val = sum(p['value'] for p in positions)
    today = date.today().isoformat()
    today_trades = [t for t in trades if t['date'] == today]

    scan_out, _ = run_scan([p['stock'] for p in holds])
    sigs = parse_scan(scan_out)

    now = datetime.now().strftime('%H:%M')
    lines = [f'📊 持股回報 {today} {now}',
             f'投組現值 {total_val:,.0f}（未實現 {"+" if total_pnl >= 0 else ""}{total_pnl:,.0f}）']
    if today_trades:
        lines.append(f'今日成交 {len(today_trades)} 筆')

    lines.append('━━ 持股與操作建議 ━━')
    for p in sorted(holds, key=lambda x: x['pct']):
        name = p['stock'].replace('-', '')
        sig = sigs.get(name) or sigs.get(p['stock'])
        lines.append(f'▍{p["stock"]} {p["shares"]:.0f}股 均價{p["avgCost"]} {"+" if p["pct"]>=0 else ""}{p["pct"]}%')
        lines += ['  ' + t for t in advice(p, sig)]

    opens = [n for n, s in sigs.items() if s['n'] == 8]
    if opens:
        lines.append('━━ 8/8 進場訊號 ━━')
        lines.append('🟢 ' + '、'.join(opens))

    if not no_news:
        lines.append('━━ 個股新聞/財報 ━━')
        for p in holds:
            news = get_news(p['stock'], p.get('code'))
            if news:
                lines.append(f'▍{p["stock"]}')
                lines += news

    msg = '\n'.join(lines)
    with open('/tmp/line_report.txt', 'w') as f:
        f.write(msg)
    print(msg)


if __name__ == '__main__':
    main()
