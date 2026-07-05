using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using Il2CppInterop.Runtime;
using PixelCrushers.DialogueSystem;
using UnityEngine;

namespace DialoguePortraits;

/// <summary>
/// 灵兽江湖(Beast Saga)对话立绘插件。
/// 完全走官方机制:重要剧情对话显示手绘立绘用的是
/// GameDialogueHelper.ShowCharacter("rolefull_角色拼音+null") / HideCharacter("null"),
/// 本插件在「每一句」对话时自动帮说话者调用同一套指令。
/// 立绘素材是 StreamingAssets 的 rolefull_* AssetBundle(可被创意工坊 Mod 替换)。
/// </summary>
[BepInPlugin(PluginGuid, PluginName, PluginVersion)]
public class Plugin : BasePlugin
{
    public const string PluginGuid = "beastsaga.dialogueportraits";
    public const string PluginName = "DialoguePortraits";
    public const string PluginVersion = "1.2.0";

    internal static ManualLogSource Logger;
    internal static Dictionary<string, string> PortraitMap = new();
    internal static ConfigEntry<bool> LogSpeakers;
    internal static ConfigEntry<bool> Verbose;
    internal static ConfigEntry<bool> HideOnUnmapped;
    internal static string PluginDir;

    public override void Load()
    {
        Logger = Log;
        PluginDir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);

        HideOnUnmapped = Config.Bind("General", "HideOnUnmapped", true,
            "轮到没有立绘的角色说话时,把上一位的立绘收掉(false=保留)");
        LogSpeakers = Config.Bind("Debug", "LogSpeakers", true, "把每句话的说话者名字写进日志(用来补全对照表)");
        Verbose = Config.Bind("Debug", "Verbose", true, "输出详细诊断日志");

        LoadPortraitMap();
        Harmony.CreateAndPatchAll(typeof(Patches), PluginGuid);
        Logger.LogInfo($"{PluginName} {PluginVersion} 已载入,立绘对照 {PortraitMap.Count} 笔");
    }

    private void LoadPortraitMap()
    {
        var path = Path.Combine(PluginDir, "portrait_map.json");
        if (!File.Exists(path))
        {
            Logger.LogWarning($"找不到 {path},立绘将全部不显示");
            return;
        }
        try
        {
            PortraitMap = JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(path));
        }
        catch (Exception e)
        {
            Logger.LogError($"portrait_map.json 解析失败: {e.Message}");
        }
    }
}

internal static class Patches
{
    // 我们自己叫出来的立绘(rolefull 名);null = 目前没显示
    private static string _shownRole;
    // 剧情序列自己在控制立绘/演出 → 这段对话插件不插手
    private static bool _storyControlsScene;
    private static bool _selfCall;
    private static readonly HashSet<string> _loggedUnmapped = new();

    // 旁白/工具型说话者与玩家:说话时不动当前立绘(对话对象继续显示)
    private static readonly HashSet<string> _keepCurrent = new()
    {
        "动画", "断点", "任务", "变量", "奖励", "选项", "战斗", "系统", "旁白",
    };

    private static void Dbg(string msg)
    {
        if (Plugin.Verbose.Value) Plugin.Logger.LogInfo("[dbg] " + msg);
    }

    private static GameDialogueHelper FindHelper()
    {
        var obj = UnityEngine.Object.FindObjectOfType(Il2CppType.Of<GameDialogueHelper>());
        if (obj != null) return obj.TryCast<GameDialogueHelper>();
        var all = Resources.FindObjectsOfTypeAll(Il2CppType.Of<GameDialogueHelper>());
        return all.Length > 0 ? all[0].TryCast<GameDialogueHelper>() : null;
    }

    // ---- 剧情接管侦测:剧情自己 Show/Hide 立绘或叫演员上台时,插件让位 ----

    [HarmonyPostfix]
    [HarmonyPatch(typeof(GameDialogueHelper), nameof(GameDialogueHelper.ShowCharacter))]
    private static void OnStoryShowCharacter(string parmeter)
    {
        if (_selfCall) return;
        Dbg($"剧情 ShowCharacter({parmeter}),让位");
        _storyControlsScene = true;
        _shownRole = null; // 画面上的立绘现在归剧情管
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(GameDialogueHelper), nameof(GameDialogueHelper.CreateFriendSet))]
    private static void OnStoryCreateFriend(string friendName, string ps, bool isCallBack)
    {
        if (_selfCall) return;
        Dbg($"剧情 CreateFriendSet({friendName}),让位");
        _storyControlsScene = true;
        HideOwnPortrait();
    }

    // ---- 主流程 ----

    [HarmonyPostfix]
    [HarmonyPatch(typeof(ConversationView), nameof(ConversationView.StartSubtitle))]
    private static void OnStartSubtitle(Subtitle subtitle)
    {
        try
        {
            ShowPortraitFor(subtitle);
        }
        catch (Exception e)
        {
            Plugin.Logger.LogError($"OnStartSubtitle: {e}");
        }
    }

    private static void ShowPortraitFor(Subtitle subtitle)
    {
        if (subtitle == null) return;
        var speaker = subtitle.speakerInfo;
        if (speaker == null) return;

        string name = speaker.nameInDatabase;
        if (string.IsNullOrEmpty(name)) return;

        if (Plugin.LogSpeakers.Value)
            Plugin.Logger.LogInfo($"[speaker] {name} (isPlayer={speaker.isPlayer})");

        if (_storyControlsScene) return;

        // 玩家或旁白说话:保留当前立绘(对话对象继续站在画面上)
        if (speaker.isPlayer || _keepCurrent.Contains(name) || name.Contains("嘴替"))
            return;

        if (!Plugin.PortraitMap.TryGetValue(name, out var role))
        {
            LogUnmapped(name);
            if (Plugin.HideOnUnmapped.Value) HideOwnPortrait();
            return;
        }
        if (role == _shownRole) return;

        var helper = FindHelper();
        if (helper == null)
        {
            Plugin.Logger.LogWarning("找不到 GameDialogueHelper,无法显示立绘");
            return;
        }

        _selfCall = true;
        try
        {
            if (_shownRole != null)
            {
                Dbg("HideCharacter(null)");
                helper.HideCharacter("null");
            }
            Dbg($"ShowCharacter({role}+null)");
            helper.ShowCharacter(role + "+null");
            _shownRole = role;
        }
        finally
        {
            _selfCall = false;
        }
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(ConversationController), nameof(ConversationController.Close))]
    private static void OnConversationClose()
    {
        Dbg("对话结束");
        HideOwnPortrait();
        _storyControlsScene = false;
    }

    private static void HideOwnPortrait()
    {
        if (_shownRole == null) return;
        var helper = FindHelper();
        if (helper != null)
        {
            _selfCall = true;
            try { helper.HideCharacter("null"); }
            catch (Exception e) { Dbg($"HideCharacter 异常: {e.Message}"); }
            finally { _selfCall = false; }
        }
        _shownRole = null;
    }

    private static void LogUnmapped(string name)
    {
        if (!_loggedUnmapped.Add(name)) return;
        Plugin.Logger.LogInfo($"[unmapped speaker] {name}");
        try
        {
            File.AppendAllText(
                Path.Combine(Plugin.PluginDir, "unmapped_speakers.txt"),
                name + Environment.NewLine);
        }
        catch { /* 记录失败不影响游戏 */ }
    }
}
