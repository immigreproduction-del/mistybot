$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\transfer-railway-memory.ps1" -LibraryOnly
$python = (Get-Command python.exe -ErrorAction Stop).Source
$folder = Join-Path ([IO.Path]::GetTempPath()) ('misty-test-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $folder

function Assert-Test {
    param([bool]$Value, [string]$Message)
    if (-not $Value) { throw $Message }
}

$arguments = @('', 'C:\folder with spaces\', 'a"b', 'backslash\"quote', 'simple')
$reply = Invoke-Captured $python (@('-c', 'import sys,json; print(json.dumps(sys.argv[1:]))') + $arguments)
Assert-Test ($reply.ExitCode -eq 0) 'Native quoting failed.'
$decoded = $reply.Output | ConvertFrom-Json
Assert-Test ($decoded.Count -eq $arguments.Count) 'Empty argument lost.'
for ($i = 0; $i -lt $arguments.Count; $i++) {
    Assert-Test ($decoded[$i] -ceq $arguments[$i]) "Argument $i changed."
}

$stdin = "import sys`nprint('MISTY_RESULT:' + 'x' * 200000)`nsys.stderr.write('stderr-test')`n"
$reply = Invoke-Captured $python @('-') $stdin
Assert-Test ($reply.ExitCode -eq 0 -and $reply.Output.StartsWith('MISTY_RESULT:')) 'stdin or output corrupted.'
Assert-Test ($reply.Output.Length -gt 200000 -and $reply.Error -eq 'stderr-test') 'Large output or stderr lost.'
$reply = Invoke-Captured $python @('-c', 'import os; print(os.getcwd())')
Assert-Test ($reply.Output.Trim() -eq (Get-Location).ProviderPath) 'Working directory lost.'

$key = Join-Path $folder 'key with spaces'
$reply = Invoke-Captured (Get-Command ssh-keygen.exe).Source @('-t', 'ed25519', '-f', $key, '-N', '', '-C', 'local-test-only')
Assert-Test ($reply.ExitCode -eq 0 -and (Test-Path -LiteralPath "$key.pub")) "Non-interactive key generation failed: $($reply.Error)"

$receipt = 'MISTY_RESULT:{"ok":true,"operation":"restore","transfer_id":"test-id","sha256":"abc"}'
$result = Read-TransferResult $receipt 'restore' 'test-id'
Assert-Test ($result.sha256 -eq 'abc') 'Receipt rejected.'
foreach ($bad in @('no result', ($receipt + "`n" + $receipt), $receipt.Replace('test-id', 'other-id'), $receipt.Replace('true', 'false'))) {
    $rejected = $false
    try { $null = Read-TransferResult $bad 'restore' 'test-id' } catch { $rejected = $true }
    Assert-Test $rejected 'Invalid receipt accepted.'
}

$source = Join-Path $folder 'source.json'
[IO.File]::WriteAllText($source, '{"474146761091579921":{"permanent_memory":["test"]}}')
$hash = Assert-MemoryFile $source
$export = [pscustomobject]@{data=[Convert]::ToBase64String([IO.File]::ReadAllBytes($source)); sha256=$hash}
$destination = Join-Path $folder 'received.json'
Save-Export $export $destination
Assert-Test ((Assert-MemoryFile $destination) -ceq $hash) 'Export changed.'
$export.sha256 = '0' * 64
$badDestination = Join-Path $folder 'corrupt.json'
$rejected = $false
try { Save-Export $export $badDestination } catch { $rejected = $true }
Assert-Test ($rejected -and -not (Test-Path $badDestination)) 'Corrupt export accepted.'

$rejected = $false
try { $null = Invoke-Captured $python @('-c', 'import time; time.sleep(15)') -TimeoutSeconds 1 } catch { $rejected = $true }
Assert-Test $rejected 'Timeout not enforced.'

Write-Host 'OK : Windows arguments, empty passphrase, stdin, large output, working directory, receipts, hashes, timeout.'
Write-Host "Local test fixtures: $folder"
