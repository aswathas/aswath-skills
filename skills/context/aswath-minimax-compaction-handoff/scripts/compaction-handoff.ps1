$ErrorActionPreference = 'SilentlyContinue'
$python = 'C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe'
$script = 'C:\Users\ADMIN\.minimax\compaction-handoff.py'
if (-not (Test-Path $python)) {
  $python = 'python'
}
if (-not (Test-Path $script)) {
  exit 0
}
# stdin is inherited by the child process unchanged, so the hook payload bytes
# reach the Python worker exactly as the runtime sent them.
& $python $script
exit $LASTEXITCODE
