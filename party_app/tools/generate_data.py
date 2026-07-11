#!/usr/bin/env python3
"""
把「遊戲」試算表匯出的 CSV 轉成 party_app/data.js。

用法：
    python3 tools/generate_data.py <game.csv> > data.js

CSV 欄位：暱稱, 生日, 另一半或是朋友, ＩＧ, 配對朋友, 配對朋友的提示

安全設計：
- 配對答案不以明文存在前端，改存 SHA-256(SALT + 正規化暱稱)。
- 對方暱稱與 IG 以答案衍生的 XOR 金鑰流加密，答對才解得開。
- 每人接受多組「別名」（例：NortonWu（翊羣/小祥）可輸入 nortonwu / 翊羣 / 小祥），
  若別名會對到兩個以上不同的人則自動剔除，避免歧義。
"""
import csv
import hashlib
import json
import re
import sys
import unicodedata
from base64 import b64encode

SALT = "pa1017-shuiwei"

# 試算表手誤修正：配對朋友欄位 -> 名單上的正確暱稱
TARGET_FIXES = {"彩霖": "彥霖"}


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


def main(csv_path: str):
    with open(csv_path, encoding="utf-8") as f:
        rows = [r for r in csv.reader(f)][1:]
    people = []
    for r in rows:
        name, birthday, _friends, ig, target, hint = (c.strip() for c in r[:6])
        target = TARGET_FIXES.get(target, target)
        people.append({"name": name, "birthday": birthday, "ig": ig,
                       "target": target, "hint": hint})

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

    out = []
    for p in people:
        entry = {"name": p["name"], "birthday": p["birthday"], "ig": p["ig"]}
        if p["target"]:
            assert p["target"] in names, f"配對朋友不在名單中: {p['target']}"
            t = next(q for q in people if q["name"] == p["target"])
            payload = {"n": t["name"], "ig": t["ig"]}
            entry["quest"] = {
                "hint": p["hint"],
                "answers": [{"h": sha256_hex(SALT + a), "p": encrypt(payload, a)}
                            for a in sorted(aliases_of[t["name"]])],
            }
        out.append(entry)

    print("// 由 tools/generate_data.py 自動產生，請勿手改；資料來源：Drive「遊戲」試算表")
    print(f"window.PARTY_SALT = {json.dumps(SALT)};")
    print("window.PARTY_PEOPLE = " +
          json.dumps(out, ensure_ascii=False, indent=1) + ";")
    ok = sum(1 for p in out if "quest" in p)
    print(f"// {len(out)} 位參與者，{ok} 位有配對任務", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
