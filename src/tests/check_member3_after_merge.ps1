# Run from src: powershell -ExecutionPolicy Bypass -File tests/check_member3_after_merge.ps1
$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $PSScriptRoot
$localPython = Join-Path $sourceRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $localPython) {
    $pythonExe = $localPython
} else {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
}

Push-Location -LiteralPath $sourceRoot
try {
    & $pythonExe -m tests.audit_team_security --shapes workflow,single,orchestrator --out reports/team_security.json
    $securityExitCode = $LASTEXITCODE
    & $pythonExe -m lab8.check_submission
    $submissionExitCode = $LASTEXITCODE
    if ($securityExitCode -ne 0 -or $submissionExitCode -ne 0) {
        Write-Output 'Checks need attention. Read the audit summary and every FAIL above before submitting.'
        exit 1
    }
    Write-Output 'Security audit PASS; check_submission 0 FAIL.'
} finally {
    Pop-Location
}
