# 用 Mono.Cecil 檢視 interop 組件中的掛勾點簽名
# 用法:.\dump_types.ps1 -Filter "CreateFriend" -CecilPath "路徑\Mono.Cecil.dll"
# (Mono.Cecil.dll 可從 UABEA 或 NuGet 取得;路徑不可含非 ASCII 字元,否則 Add-Type 會失敗)
param(
    [string]$Filter = "CreateFriend",
    [Parameter(Mandatory = $true)][string]$CecilPath,
    [string]$InteropDir = "C:\Program Files (x86)\Steam\steamapps\common\Beast Saga\BepInEx\interop"
)
Add-Type -Path $CecilPath

foreach ($asmName in @("Assembly-CSharp.dll", "Dialogue.dll", "Model.Runtime.dll")) {
    $asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly((Join-Path $InteropDir $asmName))
    foreach ($type in $asm.MainModule.GetTypes()) {
        $hitMethods = @($type.Methods | Where-Object { $_.Name -like "*$Filter*" })
        if ($type.Name -like "*$Filter*" -or $hitMethods.Count -gt 0) {
            Write-Output "== $asmName :: $($type.FullName)"
            foreach ($m in $hitMethods) {
                $params = ($m.Parameters | ForEach-Object { "$($_.ParameterType.Name) $($_.Name)" }) -join ", "
                Write-Output "   $($m.ReturnType.Name) $($m.Name)($params)"
            }
        }
    }
    $asm.Dispose()
}
