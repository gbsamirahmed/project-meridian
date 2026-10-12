param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$DataRoot,
    [Parameter(Mandatory=$true)][string]$Execution,
    [switch]$ProbeDeadline,
    [double]$ElapsedOffset = 5,
    [int]$InitialVertices = 0
)
$ErrorActionPreference = 'Stop'
throw 'Historical launcher-only supervision is disabled. Genuine continuation requires new owner approval and a reviewed job-tree entry point; see contour-pipeline-recovery.md.'
$ownerRoot = [IO.Path]::GetFullPath((Join-Path $DataRoot 'experiments/atlas/source-aware-contours-v1'))
$executionPath = [IO.Path]::GetFullPath($Execution)
if (-not $executionPath.StartsWith($ownerRoot + [IO.Path]::DirectorySeparatorChar)) {
    throw 'Execution must be a fresh child of the approved experiment root'
}
$label = if ($ProbeDeadline) { 'deadline-probe' } else { 'genuine-supervision' }
$stdout = Join-Path $executionPath ($label + '.stdout.txt')
$stderr = Join-Path $executionPath ($label + '.stderr.txt')
$receipt = Join-Path $executionPath ($label + '.json')
if ((Test-Path -LiteralPath $stdout) -or (Test-Path -LiteralPath $stderr) -or (Test-Path -LiteralPath $receipt)) {
    throw 'Supervision outputs already exist; never overwrite earlier evidence'
}
$parent = [Diagnostics.Process]::GetCurrentProcess()
$parent.Refresh()
if ($parent.PeakWorkingSet64 -gt 128MB) { throw 'Supervisor memory exceeds reserved allowance' }
$arguments = if ($ProbeDeadline) {
    @('-B','-c','"import time; time.sleep(60)"')
} else {
    $worker = Join-Path $PSScriptRoot 'rerun.py'
    $processing = Join-Path $executionPath 'processing'
    if (Test-Path -LiteralPath $processing) { throw 'Genuine processing directory must be fresh' }
    @('-B',('"' + $worker + '"'),'--owner-approved-riffelhorn',
      '--data-root',('"' + $DataRoot + '"'),'--output',('"' + $processing + '"'),
      '--budget-root',('"' + $ownerRoot + '"'),'--initial-vertices',"$InitialVertices",
      '--elapsed-offset',"$ElapsedOffset",'--working-set-ceiling',"$(384MB)")
}
$clock = [Diagnostics.Stopwatch]::StartNew()
$limit = if ($ProbeDeadline) { 0.75 } else { 1200 - $ElapsedOffset }
$process = Start-Process -FilePath $Python -ArgumentList $arguments -WindowStyle Hidden `
    -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$workerPeak = 0L
$parentPeak = $parent.PeakWorkingSet64
$reason = $null
$nextStorageCheck = 0.0
$bytes = 0L
try {
    while (-not $process.HasExited) {
        $process.Refresh(); $parent.Refresh()
        $workerPeak = [Math]::Max($workerPeak,$process.PeakWorkingSet64)
        $parentPeak = [Math]::Max($parentPeak,$parent.PeakWorkingSet64)
        if ($clock.Elapsed.TotalSeconds -ge $nextStorageCheck) {
            $bytes = 0L
            foreach ($file in [IO.Directory]::EnumerateFiles($ownerRoot,'*',[IO.SearchOption]::AllDirectories)) {
                $bytes += [IO.FileInfo]::new($file).Length
            }
            $nextStorageCheck = $clock.Elapsed.TotalSeconds + 1
            [GC]::Collect()
        }
        if ($parentPeak -gt 128MB -or ($parentPeak+$workerPeak) -gt 512MB) { $reason = 'Aggregate working-set ceiling' }
        elseif ($bytes -gt 150000000) { $reason = 'Overall scratch ceiling' }
        elseif ($clock.Elapsed.TotalSeconds -ge $limit) { $reason = 'Wall-time deadline' }
        if ($reason) { $process.Kill(); break }
        Start-Sleep -Milliseconds 100
    }
    $process.WaitForExit(); $process.Refresh(); $parent.Refresh()
    $parentPeak = [Math]::Max($parentPeak,$parent.PeakWorkingSet64)
    $clock.Stop()
    $result = [ordered]@{probe=[bool]$ProbeDeadline; stopReason=$reason; exitCode=$process.ExitCode;
        elapsedSeconds=$clock.Elapsed.TotalSeconds; precedingSecondsCharged=$ElapsedOffset;
        workerSampledPeakBytes=$workerPeak; supervisorPeakBytes=$parentPeak;
        aggregatePeakUpperBoundBytes=$parentPeak+$workerPeak; processingThreads=1;
        workerResidentMaximumBytes=384MB; supervisorAllowanceBytes=128MB;
        requests=0; stdoutBytes=(Get-Item -LiteralPath $stdout).Length;
        stderrBytes=(Get-Item -LiteralPath $stderr).Length}
    $result | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding utf8NoBOM
    $result | ConvertTo-Json -Compress | Write-Output
} finally {
    if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit() }
    $process.Dispose()
}
if ($ProbeDeadline) {
    if ($reason -ne 'Wall-time deadline') { throw 'Deadline probe did not demonstrate forced termination' }
} elseif ($reason -or $result.exitCode -ne 0) {
    exit 2
}
