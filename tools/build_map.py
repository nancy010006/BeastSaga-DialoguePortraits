# 自動比對:角色中文名(拼音縮寫)→ DS 立繪 prefab,產出 portrait_map.json
# 依據:actors.json(parse_db.py 產出)+ DS prefab 清單 + createfriend_map.json 佐證
import json
import os
import re
from collections import Counter
from pypinyin import lazy_pinyin

HERE = os.path.dirname(os.path.abspath(__file__))

DS_PREFABS = [
    "DSAJ", "DSBZ", "DSDTZ", "DSF", "DSHQC", "DSL", "DSLX", "DSLY", "DSLY2",
    "DSLangY", "DSLangY1", "DSMCY", "DSMHL", "DSS", "DSSSN", "DSSX", "DSSheX",
    "DSTQQ", "DSWC", "DSWY", "DSXS", "DSZLL",
]

# 手動確認過的官方劇情佐證(createfriend_map.json 交叉統計)
EVIDENCE = {
    "DSHQC": "猴千冲",
    "DSTQQ": "兔千千",
    "DSZLL": "藏玲珑",
    "DSSheX": "蛇形",
    "DSSX": "狮逍",
    "DSMCY": "猫春也",
    "DSF": "福",
    "DSWY": "忘忧",
    "DSLY": "狼渊",
}

with open(os.path.join(HERE, "actors.json"), encoding="utf-8") as f:
    actors = list(json.load(f).keys())

def initials(name):
    """中文名 → 拼音首字母(小寫),如 猴千冲 -> hqc"""
    clean = re.sub(r"[((].*?[))]", "", name).strip()
    py = lazy_pinyin(clean)
    return "".join(w[0] for w in py if w), "".join(py)

# ds key(去掉 DS 前綴,小寫)→ prefab
candidates = {}
for p in DS_PREFABS:
    key = p[2:].lower()
    candidates[key] = p

matches = {}   # actor_name -> prefab
for name in actors:
    if not name or name in ("动画", "断点", "任务", "变量", "奖励", "选项", "战斗", "系统"):
        continue
    ini, full = initials(name)
    for key, prefab in candidates.items():
        base = key.rstrip("123")
        # 縮寫完全相符(hqc==hqc)或全拼開頭相符(langy → langying/langyuan…)
        if ini == base or (len(base) >= 4 and full.startswith(base)):
            matches.setdefault(name, []).append(prefab)

print("=== 自動比對結果 ===")
for name, prefabs in sorted(matches.items(), key=lambda x: x[1][0]):
    ev = " ← 劇情佐證" if any(EVIDENCE.get(p) == name for p in prefabs) else ""
    print(f"{name:20s} -> {','.join(prefabs)}{ev}")

# 產出最終表:劇情佐證優先,其次唯一比對
final = {}
for prefab, name in EVIDENCE.items():
    final[name] = prefab
for name, prefabs in matches.items():
    if name not in final and len(prefabs) == 1:
        final[name] = prefabs[0]

with open(os.path.join(HERE, "..", "portrait_map.json"), "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)
print(f"\nportrait_map.json 已產出,共 {len(final)} 筆")
