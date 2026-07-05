# 解析 Beast Saga 的 DialogueDatabase(sharedassets0.assets)
# 產出:actors.json(角色表)、createfriend_map.json(DS 立繪 × 說話者交叉表)
# 用法:python -X utf8 parse_db.py [遊戲目錄]
import UnityPy
import struct
import sys
import json
import re
import os

GAME = sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files (x86)\Steam\steamapps\common\Beast Saga"
ASSETS = os.path.join(GAME, "BeastSaga_Data", "sharedassets0.assets")
OUT = os.path.dirname(os.path.abspath(__file__))


def extract_strings(raw):
    """走訪 Unity 序列化資料,抽出 4-byte 對齊、長度前綴的 UTF-8 字串 (offset, text)。"""
    out = []
    i = 0
    n = len(raw)
    while i + 4 <= n:
        l = struct.unpack_from("<I", raw, i)[0]
        if 1 <= l <= 2000 and i + 4 + l <= n:
            s = raw[i + 4 : i + 4 + l]
            try:
                t = s.decode("utf-8")
                if all(c.isprintable() or c in "\n\r\t" for c in t):
                    out.append((i, t))
                    i = (i + 4 + l + 3) & ~3
                    continue
            except UnicodeDecodeError:
                pass
        i += 4
    return out


def parse_db(raw, db_name):
    ss = extract_strings(raw)
    # --- 角色表:序列中第一段連續的 Name/.../IsPlayer 群組 ---
    # 角色記錄:int id 位於 'Name' 標題的長度前綴往前 8 bytes
    actors = {}  # id -> name
    i = 0
    while i < len(ss):
        off, t = ss[i]
        if t == "Name" and i + 1 < len(ss):
            # 檢查此群組內接下來 12 個字串內有沒有 IsPlayer(角色欄位特徵)
            window = [x[1] for x in ss[i : i + 14]]
            if "IsPlayer" in window:
                aid = struct.unpack_from("<i", raw, off - 8)[0]
                name = ss[i + 1][1]
                if name == "CustomFieldType_Text":  # Name 值為空字串被略過
                    name = ""
                if 0 < aid < 10000 and aid not in actors:
                    actors[aid] = name
        if t == "Dialogue Text" or t == "Title":
            break  # 進入對話區,角色表結束
        i += 1

    # --- 對話項:配對 Actor id 與含 CreateFriend/UnFriend 的 Sequence ---
    hits = []
    cur_actor = None
    cur_conversant = None
    for idx, (off, t) in enumerate(ss):
        if t == "Actor" and idx + 1 < len(ss) and ss[idx + 1][1].isdigit():
            cur_actor = int(ss[idx + 1][1])
        elif t == "Conversant" and idx + 1 < len(ss) and ss[idx + 1][1].isdigit():
            cur_conversant = int(ss[idx + 1][1])
        elif t == "Sequence" and idx + 1 < len(ss):
            seq = ss[idx + 1][1]
            for m in re.finditer(r"SendMessage\((CreateFriend|UnFriend|NPCForward|SpineAnim),(DS\w+)", seq):
                hits.append(
                    {
                        "db": db_name,
                        "command": m.group(1),
                        "ds_prefab": m.group(2),
                        "actor_id": cur_actor,
                        "actor_name": actors.get(cur_actor, "?"),
                        "conversant_id": cur_conversant,
                        "conversant_name": actors.get(cur_conversant, "?"),
                    }
                )
    return actors, hits


def main():
    env = UnityPy.load(ASSETS)
    all_actors = {}  # name -> {dbs, ids}
    all_hits = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        raw = bytes(obj.get_raw_data())
        if raw.count(b"IsPlayer") < 3:  # 不是對話資料庫
            continue
        ss_head = extract_strings(raw[:64])
        db_name = ss_head[-1][1] if ss_head else str(obj.path_id)
        actors, hits = parse_db(raw, db_name)
        print(f"{db_name}: {len(actors)} actors, {len(hits)} DS-command hits")
        for aid, name in actors.items():
            if name:
                all_actors.setdefault(name, []).append(f"{db_name}:{aid}")
        all_hits.extend(hits)

    with open(os.path.join(OUT, "actors.json"), "w", encoding="utf-8") as f:
        json.dump(all_actors, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "createfriend_map.json"), "w", encoding="utf-8") as f:
        json.dump(all_hits, f, ensure_ascii=False, indent=1)

    # 統計:每個 DS prefab 最常一起出現的說話者
    from collections import Counter

    pairs = Counter()
    for h in all_hits:
        for who in (h["actor_name"], h["conversant_name"]):
            if who not in ("?", "狼九思", ""):
                pairs[(h["ds_prefab"], who)] += 1
    print("\n=== DS prefab × 說話者 出現次數 ===")
    for (ds, who), c in sorted(pairs.items()):
        print(f"{ds:20s} {who:20s} {c}")


if __name__ == "__main__":
    main()
