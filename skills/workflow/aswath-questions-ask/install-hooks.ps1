<#
Registers the write-guard hooks into ~/.claude/settings.json.

    powershell -NoProfile -File install-hooks.ps1
    powershell -NoProfile -File install-hooks.ps1 -Remove

Idempotent: running it twice does not double the entries.
#>
param([switch]$Remove)

$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'hooks\install_hooks.py'
$args = @($script)
if ($Remove) { $args += '--remove' }
& python @args
exit $LASTEXITCODE
