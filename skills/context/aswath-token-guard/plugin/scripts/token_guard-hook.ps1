param([string]$Event = '')
# Windows wrapper for the token guard hook. stdout is the injection channel,
# so it is not redirected.
if (-not $Event) { $Event = $args[0] }
$script = Join-Path $PSScriptRoot 'token_guard_hook.py'
$payload = [Console]::In.ReadToEnd()
$tmp = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($tmp, $payload)
try {
  & python $script --event $Event --payload-file $tmp
} catch { }
finally {
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}
exit 0
