<#
Runs the full report pipeline: scheme -> docx -> field/TOC update.
Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File build_all.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File build_all.ps1 -Report "my_report.docx"
#>
param([string]$Report = "")
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
Set-Location $here

python generate_scheme.py
if ($LASTEXITCODE -ne 0) { throw "generate_scheme.py failed" }

python build_report_docx.py
if ($LASTEXITCODE -ne 0) { throw "build_report_docx.py failed" }

if ([string]::IsNullOrEmpty($Report)) {
    $Report = (Get-ChildItem -File -Filter *.docx |
        Where-Object { $_.Name -ne "report_template.docx" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1).Name
}

& (Join-Path $here "update_fields.ps1") -Path (Join-Path $here $Report)
Write-Host "Done: $Report"
