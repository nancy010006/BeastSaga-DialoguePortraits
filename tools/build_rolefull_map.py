# 產出 portrait_map.json:角色中文名 → rolefull_立繪包名(官方 ShowCharacter 用)
# 依據 actors.json(parse_db.py 產出)+ StreamingAssets 的 rolefull_* 清單,全拼比對
import json
import os
import re
from pypinyin import lazy_pinyin, Style

HERE = os.path.dirname(os.path.abspath(__file__))

ROLEFULL = [
    "rolefull_buzhou", "rolefull_dutongzi", "rolefull_fu", "rolefull_houqianchong",
    "rolefull_kuzhong", "rolefull_langyuan", "rolefull_lu", "rolefull_luxi",
    "rolefull_maochunye", "rolefull_maohualai", "rolefull_sanli", "rolefull_shexing",
    "rolefull_shixiao", "rolefull_shou", "rolefull_shusanniang", "rolefull_tuqianqian",
    "rolefull_wangyou", "rolefull_wuchang", "rolefull_xianglingshuang",
    "rolefull_xueshan", "rolefull_zanglinglong",
]

# 多音字/特殊拼法修正(遊戲用的拼法)
PINYIN_FIX = {
    "藏": "zang",  # 藏玲珑 → zanglinglong(pypinyin 預設 cang)
    "柒": "xi",    # 若角色叫鹿柒而包叫 luxi
}

with open(os.path.join(HERE, "actors.json"), encoding="utf-8") as f:
    actors = list(json.load(f).keys())

def full_pinyin(name):
    clean = re.sub(r"[((].*?[))]", "", name).strip()
    parts = []
    for ch in clean:
        if ch in PINYIN_FIX:
            parts.append(PINYIN_FIX[ch])
        else:
            py = lazy_pinyin(ch)
            parts.append(py[0] if py else "")
    return "".join(parts)

suffixes = {r[len("rolefull_"):]: r for r in ROLEFULL}
final = {}
used = set()
for name in actors:
    if not name:
        continue
    fp = full_pinyin(name)
    if fp in suffixes:
        final.setdefault(name, suffixes[fp])
        used.add(fp)

print("=== 比對結果 ===")
for name, r in sorted(final.items(), key=lambda x: x[1]):
    print(f"{name:14s} -> {r}")
print("\n=== 沒對到角色的立繪包 ===")
for sfx, r in suffixes.items():
    if sfx not in used:
        print(" ", r)

with open(os.path.join(HERE, "..", "portrait_map.json"), "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)
print(f"\nportrait_map.json 已產出,共 {len(final)} 筆")
