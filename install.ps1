#Requires -Version 5.1
<#
  Link every aswath-* skill in this repo into the harness skill directories.
  Links, not copies: edit the repo, every harness sees it.
#>
[CmdletBinding()]
param(
    [ValidateSet('all', 'claude', 'commandcode', 'agents')]
    [string]$Target = 'all',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$skills = Join-Path $repo 'skills'

if (-not (Test-Path $skills)) { throw "No skills/ directory beside install.ps1 ($repo)" }

$targets = @{
    claude       = Join-Path $HOME '.claude\skills'
    commandcode  = Join-Path $HOME '.commandcode\skills'
    agents       = Join-Path $HOME '.agents\skills'
}
$selected = if ($Target -eq 'all') { $targets.Keys } else { @($Target) }

$linked = 0
$skipped = 0

foreach ($t in $selected) {
    $destRoot = $targets[$t]
    if (-not (Test-Path $destRoot)) {
        New-Item -ItemType Directory -Path $destRoot -Force | Out-Null
    }

    foreach ($skillDir in Get-ChildItem $skills -Directory) {
        foreach ($s in Get-ChildItem $skillDir.FullName -Directory) {
            $dest = Join-Path $destRoot $s.Name

            if (Test-Path $dest) {
                $item = Get-Item $dest -Force
                $isLink = $item.LinkType -in @('Junction', 'SymbolicLink')
                if (-not $isLink -and -not $Force) {
                    Write-Host ("skip  {0}  ({1} exists, not a link)" -f $s.Name, $t) -ForegroundColor DarkYellow
                    $skipped++
                    continue
                }
                if ($isLink -and -not $Force) {
                    $skipped++
                    continue
                }
                Remove-Item $dest -Force -Recurse
            }

            New-Item -ItemType Junction -Path $dest -Target $s.FullName | Out-Null
            Write-Host ("link  {0}  ->  {1}" -f $s.Name, $t) -ForegroundColor Green
            $linked++
        }
    }
}

Write-Host ""
Write-Host ("linked {0}, skipped {1}" -f $linked, $skipped)
Write-Host "Invoke any skill directly: /aswath-token-guard"
