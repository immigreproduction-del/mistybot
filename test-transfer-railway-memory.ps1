$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\transfer-railway-memory.ps1" -LibraryOnly
$testFolder = Join-Path ([IO.Path]::GetTempPath()) ('misty-transfer-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testFolder | Out-Null
$source = Join-Path $testFolder 'source.json'
[IO.File]::WriteAllText($source, '{"474146761091579921":{"permanent_memory":["test"]}}')
$hash = Assert-MemoryFile $source
$commands = Get-InstallCommands $source 'test123'
$parts = [regex]::Matches($commands, "printf '%s' '([A-Za-z0-9+/=]+)'")
$payload = ($parts | ForEach-Object { $_.Groups[1].Value }) -join ''
$compressed = [IO.MemoryStream]::new([Convert]::FromBase64String($payload))
$gzip = [IO.Compression.GZipStream]::new($compressed, [IO.Compression.CompressionMode]::Decompress)
$reader = [IO.StreamReader]::new($gzip)
try { $decoded = $reader.ReadToEnd() } finally { $reader.Dispose(); $compressed.Dispose() }
if ($decoded -cne [IO.File]::ReadAllText($source)) { throw 'Payload corrompu.' }
if (-not (Test-InstallReceipt "MISTY_TRANSFER_OK:test123:$hash" 'test123' $hash)) { throw 'Confirmation refusee.' }
if (Test-InstallReceipt "echo MISTY_TRANSFER_OK:test123:$hash" 'test123' $hash) { throw 'Commande confondue avec une confirmation.' }
if (Test-InstallReceipt "MISTY_TRANSFER_OK:autre:$hash" 'test123' $hash) { throw 'Ancienne confirmation acceptee.' }
$encoded = [Convert]::ToBase64String([IO.File]::ReadAllBytes($source))
$receipt = "MISTY_SOURCE_BEGIN`n$encoded`nMISTY_SOURCE_END`n$hash  /tmp/test`n"
$destination = Join-Path $testFolder 'import.json'
Import-SourceReceipt $receipt $destination
if ((Assert-MemoryFile $destination) -ne $hash) { throw 'Import different.' }
$rejected = $false
try { Import-SourceReceipt ($receipt.Replace($hash, ('0' * 64))) (Join-Path $testFolder 'bad.json') } catch { $rejected = $true }
if (-not $rejected) { throw 'Corruption acceptee.' }
$invalid = Join-Path $testFolder 'invalid.json'
[IO.File]::WriteAllText($invalid, '[]')
$rejected = $false
try { Assert-MemoryFile $invalid | Out-Null } catch { $rejected = $true }
if (-not $rejected) { throw 'Mauvaise structure acceptee.' }
Write-Host 'OK : compression, import, empreintes, confirmations, rejet des fichiers invalides.'
Write-Host "Fixtures de test : $testFolder"
