#!/usr/bin/env python3
"""
交易日誌 → 回測系統 同步 + LINE 通知

流程：
  1. 從 GitHub 抓最新 data.js（網站「資料更新」匯入後自動 commit 的）
  2. 更新 holdings.csv（非 ETF 持股 → 回測系統格式）
  3. 跑 engine.py scan 檢查目前持股的訊號（含破月線警示）
  4. 若已設定 line_config.json → 摘要推送 LINE

用法：
  /opt/homebrew/bin/python3 sync_and_notify.py           # 完整流程
  /opt/homebrew/bin/python3 sync_and_notify.py --no-scan # 跳過掃描（快）

LINE 設定（一次性）：在本目錄建立 line_config.json：
  { "channel_token": "你的 Channel Access Token", "user_id": "你的 User ID" }
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_URL = 'https://raw.githubusercontent.com/kodada55123/trading/master/data.js'
PYTHON = '/opt/homebrew/bin/python3'

sys.path.insert(0, BASE)
from engine import TICKER_MAP, resolve  # noqa: E402


LOCAL_REPO = os.path.expanduser('~/Desktop/trading')


def fetch_data_js():
    """優先抓 GitHub raw；被限流時改用本機 repo（先 git pull 更新）"""
    try:
        req = urllib.request.Request(DATA_URL)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        print(f'   （GitHub 抓取失敗 {e}，改用本機 repo）')
        subprocess.run(['git', '-C', LOCAL_REPO, 'pull', '--quiet'],
                       capture_output=True, timeout=60)
        with open(os.path.join(LOCAL_REPO, 'data.js')) as f:
            return f.read()


def parse_block(src, name):
    """從 data.js 抽出一個陣列區塊的物件列表（格式為 generateDataJS 產生的單行物件）"""
    m = re.search(rf'const {name} = \[(.*?)\n\];', src, re.S)
    if not m:
        return []
    items = []
    for line in m.group(1).split('\n'):
        line = line.strip().rstrip(',')
        if not line.startswith('{'):
            continue
        obj = {}
        for key, val in re.findall(r'(\w+):("(?:[^"\\]|\\.)*"|-?[\d.]+)', line):
            obj[key] = json.loads(val) if val.startswith('"') else (float(val) if '.' in val else int(float(val)))
        if obj:
            items.append(obj)
    return items


def update_holdings(positions):
    rows = ['股名,ticker,成本,股數']
    unresolved = []
    for p in positions:
        if p.get('type') == 'ETF':
            continue
        name = p['stock'].replace('-', '')  # TICKER_MAP 用「世芯KY」不帶連字號
        ticker = resolve(name) or resolve(p['stock'])
        if not ticker:
            unresolved.append(p['stock'])
            ticker = '?'
        rows.append(f"{p['stock']},{ticker},{p['avgCost']},{int(p['shares'])}")
    path = os.path.join(BASE, 'holdings.csv')
    with open(path, 'w') as f:
        f.write('\n'.join(rows) + '\n')
    return path, unresolved


def run_scan(stock_names):
    """跑 engine.py scan，回傳 (完整輸出, 破月線警示列表)"""
    names = ','.join(n.replace('-', '') for n in stock_names)
    try:
        out = subprocess.run(
            [PYTHON, os.path.join(BASE, 'engine.py'), 'scan', '--stocks', names],
            capture_output=True, text=True, timeout=600).stdout
    except Exception as e:
        return f'(scan 執行失敗: {e})', []
    warns = [l.strip() for l in out.split('\n') if '破月線' in l or '⚠️' in l]
    return out, warns


def send_line(text):
    cfg_path = os.path.join(BASE, 'line_config.json')
    if not os.path.exists(cfg_path):
        return 'LINE 未設定（缺 line_config.json），略過推送'
    cfg = json.load(open(cfg_path))
    body = json.dumps({
        'to': cfg['user_id'],
        'messages': [{'type': 'text', 'text': text[:4900]}],
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.line.me/v2/bot/message/push', data=body, method='POST',
        headers={'Content-Type': 'application/json',
                 'Authorization': f"Bearer {cfg['channel_token']}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return f'LINE 推送成功（HTTP {r.status}）'
    except urllib.error.HTTPError as e:
        return f'LINE 推送失敗: HTTP {e.code} {e.read().decode()[:200]}'


def main():
    no_scan = '--no-scan' in sys.argv
    print('① 抓取 GitHub 最新 data.js …')
    src = fetch_data_js()
    m = re.search(r'const LAST_UPDATED = "([^"]+)"', src)
    updated = m.group(1) if m else '?'
    positions = parse_block(src, 'POSITIONS')
    trades = parse_block(src, 'TRADES')
    print(f'   資料日期 {updated}｜持倉 {len(positions)} 檔｜交易 {len(trades)} 筆')

    print('② 更新 holdings.csv …')
    path, unresolved = update_holdings(positions)
    stocks = [p['stock'] for p in positions if p.get('type') != 'ETF']
    print(f'   已寫入 {path}（{len(stocks)} 檔非 ETF）')
    if unresolved:
        print(f'   ⚠️ ticker 未解析: {"、".join(unresolved)}')

    # 摘要
    total_pnl = sum(p['pnl'] for p in positions)
    total_val = sum(p['value'] for p in positions)
    today = date.today().isoformat()
    today_trades = [t for t in trades if t['date'] == today]
    pos_lines = [f"  {p['stock']} {'+' if p['pct'] >= 0 else ''}{p['pct']}%"
                 for p in sorted(positions, key=lambda x: x['pct'])
                 if p.get('type') != 'ETF']

    scan_warns = []
    if not no_scan and stocks:
        print('③ 掃描持股訊號（約 1 分鐘）…')
        out, scan_warns = run_scan(stocks)
        print(out)
    else:
        print('③ 略過掃描')

    msg = '\n'.join(filter(None, [
        f'📊 交易日誌更新 {updated}',
        f'投組現值 {total_val:,.0f}（未實現 {"+" if total_pnl >= 0 else ""}{total_pnl:,.0f}）',
        f'今日成交 {len(today_trades)} 筆' if today_trades else '',
        '── 個股持倉 ──',
        *pos_lines,
        ('── 訊號警示 ──\n' + '\n'.join(scan_warns)) if scan_warns else '',
    ]))
    print('④ ' + send_line(msg))
    print('\n完成 ✅')


if __name__ == '__main__':
    main()
