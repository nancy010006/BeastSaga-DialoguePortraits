# 灵兽江湖 对话立绘插件 一键安装/重装脚本
# 游戏更新后执行本脚本即可重新套用(需先手动开一次游戏让 BepInEx 重新生成 interop,再执行本脚本重编译)
# 用法:在本目录开 PowerShell 执行 .\install.ps1   (加 -Rebuild 会先重新编译)
param([switch]$Rebuild)

$GameDir  = "C:\Program Files (x86)\Steam\steamapps\common\Beast Saga"
$Here     = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginDir = Join-Path $GameDir "BepInEx\plugins\DialoguePortraits"

# 1. BepInEx 不在就先解压
if (-not (Test-Path (Join-Path $GameDir "BepInEx\core"))) {
    Write-Host "BepInEx 不存在,解压安装中..."
    Expand-Archive -Path (Join-Path $Here "BepInEx-be785.zip") -DestinationPath $GameDir -Force
    Write-Host "请先启动一次游戏(生成 interop 组件,约 1-2 分钟),然后重新执行本脚本" -ForegroundColor Yellow
    exit
}

# 2. 需要重编译时(游戏更新后建议加 -Rebuild)
if ($Rebuild) {
    Write-Host "重新编译插件..."
    dotnet build (Join-Path $Here "src\DialoguePortraits.csproj") -c Release
    if ($LASTEXITCODE -ne 0) { Write-Host "编译失败" -ForegroundColor Red; exit 1 }
}

# 3. 部署
New-Item -ItemType Directory -Force $PluginDir | Out-Null
Copy-Item (Join-Path $Here "src\bin\Release\DialoguePortraits.dll") $PluginDir -Force
Copy-Item (Join-Path $Here "portrait_map.json") $PluginDir -Force
Write-Host "已部署到 $PluginDir" -ForegroundColor Green
