#!/usr/bin/env python3
"""
把「遊戲」試算表匯出的 CSV 轉成 party_app/data.js。

用法：
    python3 tools/generate_data.py <game.csv> [replies.csv] > data.js

game.csv 欄位：暱稱, 生日, 另一半或是朋友, ＩＧ, 配對朋友, 配對朋友的提示[, 新朋友]
（新朋友欄非空白即視為新朋友）
replies.csv（選用）：報名表單回覆，取「喝酒」「特殊技能」欄產生名片破冰話題。

安全設計：
- 配對答案不以明文存在前端，改存 SHA-256(SALT + 正規化暱稱)。
- 對方暱稱與 IG 以答案衍生的 XOR 金鑰流加密，答對才解得開。
- 每人接受多組「別名」（例：NortonWu（翊羣/小祥）可輸入 nortonwu / 翊羣 / 小祥），
  若別名會對到兩個以上不同的人則自動剔除，避免歧義。
- 卡關救援提示（星座月份 / IG 開頭）為明文，屬刻意設計的體驗保底。
"""
import csv
import hashlib
import json
import re
import sys
import unicodedata
from base64 import b64encode

SALT = "pa1017-shuiwei"

# 試算表手誤修正：配對朋友欄位 -> 名單上的正確暱稱（目前無）
TARGET_FIXES = {}

ZODIAC = [("摩羯", 120), ("水瓶", 219), ("雙魚", 321), ("牡羊", 420), ("金牛", 521), ("雙子", 621),
          ("巨蟹", 723), ("獅子", 823), ("處女", 923), ("天秤", 1023), ("天蠍", 1122), ("射手", 1222),
          ("摩羯", 1232)]

GENERIC_TOPICS = [
    "🌍 問我最近一次出國去哪",
    "🎬 問我最近在追的劇或動漫",
    "🏖️ 問我今年最想去的地方",
    "🍜 問我的口袋美食名單",
    "🎶 問我 KTV 必點歌單",
    "📸 問我手機相簿最新一張照片",
]

SKIP_SKILL = {"無", "沒有", "没有", "no", "nope", "沒", "沒有哈哈"}

# 分組拼圖：隊徽 + 通關暗號（依隊伍人數取同長度的暗號，人數改變時自動重分）
PUZZLE_EMBLEMS = ["🦊", "🐯", "🐼", "🦁", "🐸", "🐺", "🐨", "🐰", "🦄", "🐙", "🦖", "🐳"]
PUZZLE_PHRASES = {
    5: ["明年還要來", "小柯請喝酒", "埔里山傳說"],
    6: ["今晚喝到天亮", "水尾泳池派對", "拔雕英雄集結", "深夜賓果之王",
        "泳褲不能亂脫", "乾杯不准偷跑", "路見不秤相見", "宵夜我全都要",
        "帥哥配酒配山"],
}


def build_puzzle(people, rng):
    """seeded 洗牌 -> 均分成隊 -> 每人拿暗號的一個字。回傳 {暱稱: puzzle資訊}"""
    names = [p["name"] for p in people]
    rng.shuffle(names)
    n = len(names)
    n_groups = (n + 5) // 6
    base, extra = divmod(n, n_groups)      # extra 組多 1 人
    sizes = [base + 1] * extra + [base] * (n_groups - extra)
    pools = {k: list(v) for k, v in PUZZLE_PHRASES.items()}
    out, i = {}, 0
    for g, size in enumerate(sizes):
        assert pools.get(size), f"缺少 {size} 字的拼圖暗號，請在 PUZZLE_PHRASES 補充"
        phrase = pools[size].pop(0)
        assert len(phrase) == size
        h = sha256_hex(SALT + norm(phrase))
        emblem = PUZZLE_EMBLEMS[g % len(PUZZLE_EMBLEMS)]
        for pos, name in enumerate(names[i:i + size]):
            out[name] = {"team": emblem, "size": size, "pos": pos + 1,
                         "char": phrase[pos], "h": h}
        i += size
    return out


def zodiac_of(birthday: str) -> str:
    m, d = (int(x) for x in birthday.split("/")[1:3])
    md = m * 100 + d
    return next(n for n, until in ZODIAC if md < until)


def load_replies(path):
    """報名表 -> {正規化暱稱: {'alcohol':…, 'skill':…}}"""
    rows = list(csv.reader(open(path, encoding="utf-8")))
    h = rows[0]
    i_name = 1
    i_alc = next((i for i, c in enumerate(h) if "喝酒" in c), None)
    i_skill = next((i for i, c in enumerate(h) if "特殊技能" in c), None)
    out = {}
    for r in rows[1:]:
        if len(r) <= i_name or not r[i_name].strip():
            continue
        out[norm(r[i_name])] = {
            "alcohol": r[i_alc].strip() if i_alc is not None and len(r) > i_alc else "",
            "skill": r[i_skill].strip() if i_skill is not None and len(r) > i_skill else "",
        }
    return out


def topics_for(p, reply, rng_seed):
    """名片破冰話題：技能 / 酒量 / 星座，補足 3 條。"""
    t = []
    if p.get("new"):
        t.append("🌱 我是新朋友，快來跟我聊")
    skill = (reply or {}).get("skill", "")
    if skill and skill.lower() not in SKIP_SKILL and len(skill) <= 14:
        t.append(f"🎯 我的隱藏技能：{skill}")
    alc = (reply or {}).get("alcohol", "")
    if "爛醉" in alc:
        t.append("🍻 我超會喝，敢跟我拚嗎？")
    elif "不碰酒" in alc:
        t.append("🧃 我不喝酒，聊天不用灌我")
    if len(t) < 3:
        t.append(f"✨ {zodiac_of(p['birthday'])}座本人，測試我準不準")
    i = rng_seed
    while len(t) < 3:
        t.append(GENERIC_TOPICS[i % len(GENERIC_TOPICS)])
        i += 1
    return t[:3]


def norm(s: str) -> str:
    """NFKC -> 小寫 -> 只留字母與數字（各語言皆可），需與 app.js 的 norm() 一致。"""
    s = unicodedata.normalize("NFKC", s).lower()
    return "".join(c for c in s if unicodedata.category(c)[0] in ("L", "N"))


def tokens(raw: str):
    """取出暱稱中的字詞片段當候選別名。"""
    nfkc = unicodedata.normalize("NFKC", raw)
    runs = re.findall(r"[^\W_]+", nfkc, re.UNICODE)
    out = []
    for r in runs:
        out.append(r)
        # 中英混寫再拆一層（ERIC歐 -> ERIC / 歐）
        out.extend(re.findall(r"[A-Za-z0-9]+|[^\x00-\x7F]+", r))
    return out


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def keystream(key_base: str, n: int) -> bytes:
    out = b""
    i = 0
    while len(out) < n:
        out += hashlib.sha256(f"{key_base}:{i}".encode("utf-8")).digest()
        i += 1
    return out[:n]


def encrypt(payload: dict, alias_norm: str) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ks = keystream(SALT + alias_norm + "|k", len(data))
    return b64encode(bytes(a ^ b for a, b in zip(data, ks))).decode("ascii")


def main(csv_path, replies_path=None):
    with open(csv_path, encoding="utf-8") as f:
        rows = [r for r in csv.reader(f)][1:]
    replies = load_replies(replies_path) if replies_path else {}
    people = []
    for r in rows:
        name, birthday, _friends, ig, target, hint = (c.strip() for c in r[:6])
        target = TARGET_FIXES.get(target, target)
        people.append({"name": name, "birthday": birthday, "ig": ig,
                       "target": target, "hint": hint,
                       "new": bool(len(r) > 6 and r[6].strip())})

    names = {p["name"] for p in people}
    canon = {}
    for p in people:
        c = norm(p["name"])
        assert c and c not in canon, f"正規化後暱稱重複或為空: {p['name']}"
        canon[c] = p["name"]

    # 別名 -> 人，剔除對到多人的歧義別名（但本名正規化結果一定保留）
    alias_map = {}
    for p in people:
        cands = {norm(t) for t in tokens(p["name"])}
        cands.add(norm(p["name"]))
        for a in cands:
            if len(a) >= 2 or a == norm(p["name"]):
                alias_map.setdefault(a, set()).add(p["name"])
    aliases_of = {p["name"]: [] for p in people}
    for a, owners in alias_map.items():
        if len(owners) == 1:
            aliases_of[next(iter(owners))].append(a)
        else:
            for o in owners:
                if a == norm(o):  # 本名不可被剔除
                    aliases_of[o].append(a)

    import random
    puzzle = build_puzzle(people, random.Random(SALT + "|puzzle"))

    out = []
    matched = 0
    for idx, p in enumerate(people):
        entry = {"name": p["name"], "birthday": p["birthday"], "ig": p["ig"]}
        if p["new"]:
            entry["new"] = True
        reply = replies.get(norm(p["name"]))
        if reply:
            matched += 1
        entry["topics"] = topics_for(p, reply, idx)
        entry["puzzle"] = puzzle[p["name"]]
        if p["target"]:
            assert p["target"] in names, f"配對朋友不在名單中: {p['target']}"
            t = next(q for q in people if q["name"] == p["target"])
            payload = {"n": t["name"], "ig": t["ig"]}
            entry["quest"] = {
                "hint": p["hint"],
                "answers": [{"h": sha256_hex(SALT + a), "p": encrypt(payload, a)}
                            for a in sorted(aliases_of[t["name"]])],
                # 卡關救援：答錯 5 次 / 10 次由前端顯示
                "r1": f"他是{zodiac_of(t['birthday'])}座、{int(t['birthday'].split('/')[1])} 月壽星",
                "r2": f"IG 帳號開頭是「{t['ig'][:3]}…」",
            }
        out.append(entry)

    print("// 由 tools/generate_data.py 自動產生，請勿手改；資料來源：Drive「遊戲」試算表")
    print(f"window.PARTY_SALT = {json.dumps(SALT)};")
    print("window.PARTY_PEOPLE = " +
          json.dumps(out, ensure_ascii=False, indent=1) + ";")
    ok = sum(1 for p in out if "quest" in p)
    nf = sum(1 for p in out if p.get("new"))
    print(f"// {len(out)} 位參與者，{ok} 位有配對任務，{nf} 位新朋友，"
          f"{matched} 位對上報名表話題", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
