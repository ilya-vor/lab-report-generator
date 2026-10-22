<#
Экспорт DOCX в PDF через Microsoft Word (COM).
Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File to_pdf.ps1 -Path report.docx -Out report.pdf
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Out
)
$ErrorActionPreference = "Stop"

$full = (Resolve-Path $Path).Path
if ([System.IO.Path]::IsPathRooted($Out)) { $target = $Out }
else { $target = Join-Path $PWD $Out }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($full, $false, $false)
    foreach ($toc in @($doc.TablesOfContents)) { $toc.Update() }
    try { $doc.Fields.Update() | Out-Null } catch {}
    $doc.Repaginate()
    # 17 = wdFormatPDF
    $doc.SaveAs([ref]$target, [ref]17)
    $doc.Close($false)
}
finally { $word.Quit() }
Write-Host "PDF: $target"
