param([string]$Event = '')
if (-not $Event) { $Event = $args[0] }
$script = Join-Path $PSScriptRoot 'write_guard.py'
$payload = [Console]::In.ReadToEnd()
$tmp = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($tmp, $payload)
$code = 0
try {
    & python $script --event $Event --payload-file $tmp
    $code = $LASTEXITCODE
} catch {
    $code = 0
} finally {
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}
# Exit 2 blocks the tool call; the reason goes back to the agent on stderr.
exit $code
