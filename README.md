# 灵兽江湖 对话立绘插件(DialoguePortraits)

《灵兽江湖》(Beast Saga)的对话立绘插件:**每一句**对话都显示说话者的官方手绘立绘,
不再只有少数重要剧情才看得到。谁说话就切换成谁,对话结束自动收起,大幅提升对话沉浸感。

- 完全使用游戏内建的立绘显示机制(与官方剧情演出同一套指令),观感与官方一致
- 官方剧情自己有立绘/演出安排时,插件自动让位,不会打架
- **不修改任何游戏文件**,移除后 100% 还原
- 立绘素材用的是游戏本地已有的 21 张官方手绘立绘,本插件不包含任何游戏素材

## 下载安装(玩家)

1. 到 [Releases](../../releases) 下载最新的 `對話立繪外掛-完整安裝包-vX.X.X.zip`
2. 解压,把「**安裝內容(全部複製到遊戲根目錄)**」资料夹里的全部内容
   复制到游戏根目录(`BeastSaga.exe` 所在的资料夹,
   默认 `C:\Program Files (x86)\Steam\steamapps\common\Beast Saga\`)
3. 启动游戏。**第一次启动会多花 1~2 分钟**(框架初始化,只有第一次),
   会出现滚动文字的控制台窗口,属正常现象
4. 找主要角色(猫春也、兔千千、猴千冲……)对话,立绘就会出现

> 防毒软体可能对 `winhttp.dll` 误报,这是 BepInEx 框架的注入方式造成的已知误报,
> 加入白名单即可(所有 BepInEx 系 Mod 都一样)。

### 移除 / 完全还原

删除游戏根目录下这些「新增物」即可(游戏原始文件从未被修改):
`winhttp.dll`、`doorstop_config.ini`、`changelog.txt`、`BepInEx\`、`dotnet\`

### 设定

第一次运行后可编辑 `游戏根目录\BepInEx\config\beastsaga.dialogueportraits.cfg`:

| 设定 | 默认 | 说明 |
|---|---|---|
| `HideOnUnmapped` | true | 没立绘的角色说话时收掉上一位的立绘 |
| `LogSpeakers` | true | 记录每句话的说话者(补全对照表用) |
| `Verbose` | true | 详细日志,稳定后可关 |

不想看到启动时的控制台窗口:`BepInEx\config\BepInEx.cfg` →
`[Logging.Console]` → `Enabled = false`。

### 补全立绘对照表

游戏共有 21 张官方立绘,目前已对上 17 个角色,还有 4 张
(`rolefull_lu` / `rolefull_xueshan` / `rolefull_dutongzi` / `rolefull_xianglingshuang`)
不确定对应的角色名。游玩时「说了话但没立绘」的角色会记录在
`BepInEx\plugins\DialoguePortraits\unmapped_speakers.txt`,
若发现疑似角色,在 `BepInEx\plugins\DialoguePortraits\portrait_map.json`
加一行(如 `"雪山": "rolefull_xueshan"`),重开游戏即生效。
欢迎回报让对照表更完整!其他角色是游戏本来就没画立绘。

## 自行编译(开发者)

环境:.NET 6 SDK 以上;已安装本插件并至少启动过一次的游戏
(编译引用 `游戏目录\BepInEx\interop\` 的组件,路径写在 `src/DialoguePortraits.csproj` 的 `GameDir`)。

```
cd src
dotnet build -c Release
```

产物 `src/bin/Release/DialoguePortraits.dll` 复制到
`游戏目录\BepInEx\plugins\DialoguePortraits\` 即可。

### 目录说明

| 路径 | 内容 |
|---|---|
| `src/` | 插件原始码(单文件 `Plugin.cs`) |
| `tools/parse_db.py` | 解析游戏对话数据库(`sharedassets0.assets`),产出角色表 |
| `tools/build_rolefull_map.py` | 拼音比对产出 `portrait_map.json` |
| `install.ps1` | 本机重部署脚本(游戏更新后用,`-Rebuild` 先重编译) |

### 运作原理(维护笔记)

- 游戏:Unity 2021.3.1f1 IL2CPP,对话系统 PixelCrushers Dialogue System,UI 为 FairyGUI
- 框架:BepInEx 6(IL2CPP,bleeding-edge)+ HarmonyX
- Harmony postfix `PixelCrushers.DialogueSystem.ConversationView.StartSubtitle`
  → 取 `subtitle.speakerInfo.nameInDatabase` 查 `portrait_map.json`
- 显示/切换:`GameDialogueHelper.ShowCharacter("rolefull_xxx+null")`,
  收回 `HideCharacter("null")`(与官方剧情序列的
  `SendMessage(ShowCharacter,rolefull_xxx+null,Dialogue)` 同一路径)
- `ConversationController.Close` postfix → 对话结束收立绘
- 剧情自己呼叫 `ShowCharacter`/`CreateFriendSet` 时(postfix 侦测非插件呼叫),
  该场对话插件整段让位
- 玩家/旁白(动画、嘴替等工具型说话者)说话时保留当前立绘不动
- 立绘素材:StreamingAssets 的 `rolefull_*` AssetBundle
  (可用官方 Mod 工具替换,能上创意工坊;插件只负责「每句都显示」的行为)

### 游戏更新后

1. 删除 `游戏目录\BepInEx\interop\`,启动一次游戏重新生成
2. 插件若失效:`install.ps1 -Rebuild` 重编译部署
3. 若掛勾点被改动(罕见),对照本节维护笔记修 `Plugin.cs`

## 免责声明

非官方插件,与游戏开发商无关。仅供单机游玩使用,不修改游戏文件、不含任何游戏素材。
本仓库代码采 MIT 授权;随 Release 附带的 [BepInEx](https://github.com/BepInEx/BepInEx)
为 LGPL-2.1 授权的开源项目。
