<#
Updates fields and Table of Contents in a DOCX using Microsoft Word (COM).
Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File update_fields.ps1 -Path report.docx
#>
param(
    [Parameter(Mandatory = $true)][string]$Path
)
$ErrorActionPreference = "Stop"

$full = (Resolve-Path $Path).Path
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($full, $false, $false)
    foreach ($toc in @($doc.TablesOfContents)) { $toc.Update() }
    try { $doc.Fields.Update() | Out-Null } catch {}
    $doc.Repaginate()
    $doc.Save()
    $doc.Close($false)
}
finally {
    $word.Quit()
}
Write-Host "Fields and TOC updated: $Path"
