# Parse the TMDL semantic model with Microsoft's TOM TmdlSerializer (ships with Power BI Desktop).
# Usage (Windows PowerShell 5.1):  powershell -File scripts\validate_tmdl.ps1
param(
  [string]$ModelDir = "$PSScriptRoot\..\dashboard\FDA_Recall_Dashboard.SemanticModel\definition",
  [string]$PbiBin = "C:\Program Files\Microsoft Power BI Desktop\bin"
)
$ErrorActionPreference = "Stop"
$candidates = @("Microsoft.PowerBI.Tabular.dll", "Microsoft.AnalysisServices.Server.Tabular.dll")
$loaded = $false
foreach ($c in $candidates) {
  $p = Join-Path $PbiBin $c
  if (Test-Path $p) {
    try { [void][Reflection.Assembly]::LoadFrom($p); $loaded = $true } catch { Write-Host "could not load $c : $_" }
  }
}
if (-not $loaded) { throw "No TOM assembly found in $PbiBin" }
$ser = [AppDomain]::CurrentDomain.GetAssemblies() | ForEach-Object { try { $_.GetTypes() } catch { $_.Exception.Types } } |
  Where-Object { $_ -and $_.Name -eq "TmdlSerializer" } | Select-Object -First 1
if (-not $ser) { throw "TmdlSerializer type not found" }
Write-Host "Using $($ser.FullName) from $($ser.Assembly.GetName().Name)"
$db = $ser.GetMethod("DeserializeDatabaseFromFolder", [type[]]@([string])).Invoke($null, @((Resolve-Path $ModelDir).Path))
$m = $db.Model
Write-Host ("Parsed OK: {0} tables, {1} relationships, {2} measures, {3} expressions" -f `
  $m.Tables.Count, $m.Relationships.Count, (($m.Tables | ForEach-Object { $_.Measures.Count }) | Measure-Object -Sum).Sum, $m.Expressions.Count)
