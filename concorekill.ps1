# Windows process cleanup helper shared by the Python and Java runtimes.
# Registry format: PID|START_TIME_UNIX_MS. PID-only entries use legacy validation.

$ErrorActionPreference = 'Stop'
$registryPath = Join-Path $PSScriptRoot 'concorekill_pids.txt'

if (-not (Test-Path -LiteralPath $registryPath)) {
    Write-Output 'No PID registry found. Nothing to kill.'
    exit 0
}

if (-not ('ConcoreNativeMethods' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class ConcoreNativeMethods
{
    // PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr OpenProcess(uint desiredAccess, bool inheritHandle, uint processId);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GetProcessTimes(
        IntPtr processHandle,
        out long creationTime,
        out long exitTime,
        out long kernelTime,
        out long userTime);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool TerminateProcess(IntPtr processHandle, uint exitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr handle);
}
'@
}

$remaining = New-Object 'System.Collections.Generic.List[string]'
$failed = $false
$stream = $null
$locked = $false

try {
    $stream = [System.IO.File]::Open(
        $registryPath,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::ReadWrite
    )

    # Coordinate with Python msvcrt.locking and Java FileChannel.lock().
    $lockDeadline = [DateTime]::UtcNow.AddSeconds(30)
    while (-not $locked) {
        try {
            $stream.Lock(0, 2147483647)
            $locked = $true
        }
        catch [System.IO.IOException] {
            if ([DateTime]::UtcNow -ge $lockDeadline) {
                throw
            }
            Start-Sleep -Milliseconds 100
        }
    }

    $stream.Position = 0
    $reader = [System.IO.StreamReader]::new(
        $stream, [System.Text.Encoding]::UTF8, $true, 1024, $true
    )
    $lines = New-Object 'System.Collections.Generic.List[string]'
    while ($null -ne ($line = $reader.ReadLine())) {
        $lines.Add($line)
    }
    $reader.Dispose()

    $desiredAccess = [uint32]0x00101001
    $unixEpochFileTime = 116444736000000000L

    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $fields = $line.Split([char]'|')
        $targetPid = [uint32]0

        if ($fields.Length -gt 2 -or
            -not [uint32]::TryParse($fields[0], [ref]$targetPid) -or
            $targetPid -eq 0) {
            Write-Output ('Preserving invalid registry entry: ' + $line)
            $remaining.Add($line)
            $failed = $true
            continue
        }

        $handle = [ConcoreNativeMethods]::OpenProcess(
            $desiredAccess, $false, $targetPid
        )

        if ($handle -eq [IntPtr]::Zero) {
            $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
            if ($errorCode -eq 87 -or $errorCode -eq 1168) {
                Write-Output ('Skipping exited PID ' + $targetPid)
            }
            else {
                Write-Output ('Unable to open PID ' + $targetPid + ': Windows error ' + $errorCode)
                $remaining.Add($line)
                $failed = $true
            }
            continue
        }

        try {
            $creationTime = [long]0
            $exitTime = [long]0
            $kernelTime = [long]0
            $userTime = [long]0

            if (-not [ConcoreNativeMethods]::GetProcessTimes(
                $handle,
                [ref]$creationTime,
                [ref]$exitTime,
                [ref]$kernelTime,
                [ref]$userTime
            )) {
                $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
                throw "GetProcessTimes failed: Windows error $errorCode"
            }

            $actualStartMs = [long][Math]::Floor(
                ($creationTime - $unixEpochFileTime) / 10000.0
            )

            if ($fields.Length -eq 2 -and -not [string]::IsNullOrWhiteSpace($fields[1])) {
                $expectedStartMs = [long]0
                $parsed = [long]::TryParse(
                    $fields[1],
                    [Globalization.NumberStyles]::Integer,
                    [Globalization.CultureInfo]::InvariantCulture,
                    [ref]$expectedStartMs
                )
                if (-not $parsed) {
                    Write-Output ('Preserving invalid timestamp for PID ' + $targetPid)
                    $remaining.Add($line)
                    $failed = $true
                    continue
                }
            }
            elseif ($fields.Length -eq 1) {
                # Backward compatibility for old PID-only entries. Compare the
                # CIM creation time with the already-open native process handle.
                $candidate = Get-CimInstance -ClassName Win32_Process `
                    -Filter ('ProcessId=' + $targetPid) -ErrorAction Stop

                if (-not $candidate -or $candidate.CommandLine -notmatch '(?i)concore') {
                    Write-Output ('Skipping unidentified legacy PID ' + $targetPid)
                    continue
                }

                $expectedStartMs = ([DateTimeOffset]::new(
                    $candidate.CreationDate.ToUniversalTime()
                )).ToUnixTimeMilliseconds()
            }
            else {
                Write-Output ('Preserving invalid registry entry: ' + $line)
                $remaining.Add($line)
                $failed = $true
                continue
            }

            if ($actualStartMs -ne $expectedStartMs) {
                Write-Output ('Skipping stale PID ' + $targetPid)
                continue
            }

            # Identity validation and termination operate on this same handle.
            if (-not [ConcoreNativeMethods]::TerminateProcess($handle, 1)) {
                $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
                throw "TerminateProcess failed: Windows error $errorCode"
            }

            $waitResult = [ConcoreNativeMethods]::WaitForSingleObject($handle, 5000)
            if ($waitResult -ne 0) {
                throw "Process $targetPid did not signal termination within five seconds"
            }

            Write-Output ('Killing concore process ' + $targetPid)
        }
        catch {
            Write-Output ('Unable to stop PID ' + $targetPid + ': ' + $_.Exception.Message)
            $remaining.Add($line)
            $failed = $true
        }
        finally {
            [void][ConcoreNativeMethods]::CloseHandle($handle)
        }
    }

    # Keep the registry file itself. Deleting it after unlocking could race
    # with a newly starting node appending a fresh registration.
    $remainingText = ''
    if ($remaining.Count -gt 0) {
        $remainingText = [string]::Join(
            [Environment]::NewLine,
            $remaining.ToArray()
        ) + [Environment]::NewLine
    }

    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($remainingText)
    $stream.SetLength(0)
    $stream.Position = 0
    if ($bytes.Length -gt 0) {
        $stream.Write($bytes, 0, $bytes.Length)
    }
    $stream.Flush()
}
catch {
    Write-Output ('Kill script failed: ' + $_.Exception.Message)
    $failed = $true
}
finally {
    if ($stream) {
        if ($locked) {
            try {
                $stream.Unlock(0, 2147483647)
            }
            catch {
                Write-Output ('Registry unlock failed: ' + $_.Exception.Message)
                $failed = $true
            }
        }
        $stream.Dispose()
    }
}

if ($failed) {
    exit 1
}
exit 0
