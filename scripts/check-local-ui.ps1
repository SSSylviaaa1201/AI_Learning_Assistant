$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$reportPath = Join-Path $projectRoot 'local-ui-check.txt'
$result = @(
    'AI Learning Assistant Local Web Interface Check'
    "Time (local): $([DateTimeOffset]::Now.ToString('o'))"
    "Time (UTC): $([DateTimeOffset]::UtcNow.ToString('o'))"
    "Machine: $env:COMPUTERNAME"
    "Operating system: $([Environment]::OSVersion.VersionString)"
    "CPU architecture: $env:PROCESSOR_ARCHITECTURE"
    'Tested URL: http://127.0.0.1:14242/ui/'
    'Execution location: local Windows computer'
)
try {
    $health = Invoke-RestMethod 'http://127.0.0.1:14242/health' -TimeoutSec 15
    $ui = Invoke-WebRequest 'http://127.0.0.1:14242/ui/' -UseBasicParsing -TimeoutSec 15
    if ($health.status -ne 'ok' -or $ui.StatusCode -ne 200) { throw 'Unexpected health or UI response' }
    $result += 'Health: {"status":"ok"}'
    $result += "UI HTTP status: $($ui.StatusCode)"
    $result += 'Result: PASS'
    $result += 'Browser rendering is checked separately; HTTP success alone is not visual verification.'
} catch {
    $result += "Result: FAIL - $($_.Exception.Message)"
    $result | Set-Content -LiteralPath $reportPath -Encoding utf8
    $result | Write-Output
    exit 1
}
$result | Set-Content -LiteralPath $reportPath -Encoding utf8
$result | Write-Output
