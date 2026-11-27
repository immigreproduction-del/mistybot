[CmdletBinding()]
param([switch]$LibraryOnly)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-MemoryFile {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path
    if ($item.PSIsContainer -or $item.Length -lt 2 -or $item.Length -gt 20MB) { throw 'Fichier absent, vide ou trop volumineux (maximum 20 Mo).' }
    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $data = $raw | ConvertFrom-Json
    if (-not $raw.TrimStart().StartsWith('{') -or $null -eq $data -or $data -isnot [pscustomobject]) { throw 'La memoire doit contenir un objet JSON.' }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function ConvertTo-NativeArgument {
    param([AllowEmptyString()][string]$Value)
    # Windows CRT quoting, including empty arguments and trailing backslashes.
    return '"' + ([regex]::Replace(([regex]::Replace($Value, '(\\*)"', '$1$1\"')), '(\\+)$', '$1$1')) + '"'
}

function Invoke-Captured {
    param([string]$Exe, [string[]]$Arguments, [string]$InputText = '', [int]$TimeoutSeconds = 120)
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Exe
    $info.WorkingDirectory = (Get-Location).ProviderPath
    $info.Arguments = (($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' ')
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = [Text.Encoding]::UTF8
    $info.StandardErrorEncoding = [Text.Encoding]::UTF8
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    $started = $false
    try {
        $started = $process.Start()
        $outputTask = $process.StandardOutput.ReadToEndAsync()
        $errorTask = $process.StandardError.ReadToEndAsync()
        $inputTask = $process.StandardInput.WriteAsync($InputText)
        $timer = [Diagnostics.Stopwatch]::StartNew()
        while (-not $inputTask.IsCompleted) {
            if ($timer.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw 'Delai de connexion depasse.' }
            Start-Sleep -Milliseconds 100
        }
        # Un programme qui se termine sans lire son entree ferme le canal : ce n'est pas une erreur,
        # le code de sortie et les sorties disent ce qui s'est passe.
        try { $null = $inputTask.GetAwaiter().GetResult() } catch [IO.IOException] { }
        try { $process.StandardInput.Close() } catch [IO.IOException] { }
        while (-not $process.WaitForExit(200)) {
            if ($timer.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw 'Delai de connexion depasse. La sauvegarde locale est conservee.' }
        }
        return [pscustomobject]@{ ExitCode = $process.ExitCode; Output = $outputTask.Result; Error = $errorTask.Result }
    } finally {
        if ($started -and -not $process.HasExited) { $process.Kill() }
        $process.Dispose()
    }
}

function Invoke-Railway {
    param([string[]]$Arguments)
    & $script:RailwayExe @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'Railway a echoue. La sauvegarde locale est conservee.' }
}

function Get-RailwayJson {
    param([string[]]$Arguments)
    $result = Invoke-Captured $script:RailwayExe ($Arguments + @('--json'))
    if ($result.ExitCode -ne 0) { throw "Railway : $($result.Error.Trim())" }
    return ($result.Output | ConvertFrom-Json)
}

function Connect-Service {
    param([string]$Label)
    Write-Host "`n=== Compte $Label ===" -ForegroundColor Cyan
    & $script:RailwayExe whoami
    $connected = $LASTEXITCODE -eq 0
    if (-not $connected -or (Read-Host 'Est-ce le bon compte ? O/N') -notmatch '^(o|oui)$') {
        if ($connected) { Invoke-Railway @('logout') }
        Invoke-Railway @('login')
        Invoke-Railway @('whoami')
        if ((Read-Host 'Confirmer ce compte ? O/N') -notmatch '^(o|oui)$') { throw 'Compte non confirme.' }
    }
    Write-Host 'Selectionne le workspace, projet, environnement ET le service mistybot.'
    Invoke-Railway @('link')
    Invoke-Railway @('status')
    if ((Read-Host "Confirmer ce service comme $Label ? O/N") -notmatch '^(o|oui)$') { throw 'Service non confirme.' }
}

function New-Connection {
    $account = Get-RailwayJson @('whoami')
    $email = [string]$account.email
    if (-not $email) { throw 'Impossible de reconnaitre le compte Railway connecte.' }
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $accountId = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($email.ToLowerInvariant())))).Replace('-', '').Substring(0, 24) }
    finally { $sha.Dispose() }
    $keyFolder = Join-Path $env:USERPROFILE '.ssh'
    $null = New-Item -ItemType Directory -Path $keyFolder -Force
    $key = Join-Path $keyFolder "mistybot-transfer-$accountId"
    if (-not (Test-Path -LiteralPath $key)) {
        Write-Host 'Creation automatique de la cle SSH pour ce compte...'
        $created = Invoke-Captured (Get-Command ssh-keygen.exe).Source @('-t', 'ed25519', '-f', $key, '-N', '', '-C', 'mistybot-memory-transfer')
        if ($created.ExitCode -ne 0) { throw "Creation de cle impossible : $($created.Error)" }
    }
    if (-not (Test-Path -LiteralPath "$key.registered")) {
        Write-Host 'Enregistrement de la cle SSH sur Railway...'
        $registered = Invoke-Captured $script:RailwayExe @('ssh', 'keys', 'add', '--key', "$key.pub", '--name', 'Mistybot memory transfer')
        if ($registered.ExitCode -ne 0) { throw "Enregistrement SSH refuse : $($registered.Error) $($registered.Output)" }
        [IO.File]::WriteAllText("$key.registered", $email)
    }
    $config = Join-Path $script:SessionFolder ('ssh-' + [guid]::NewGuid().ToString('N') + '.config')
    Write-Host 'Preparation de la connexion au service selectionne...'
    $configured = Invoke-Captured $script:RailwayExe @('ssh', 'config', '--path', $config, '--alias', 'misty-transfer', '--identity-file', $key)
    if ($configured.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $config)) {
        throw "Configuration SSH impossible. Verifie que le service selectionne est Online. $($configured.Error) $($configured.Output)"
    }
    return [pscustomobject]@{ Config = $config; Account = $email }
}

function Read-TransferResult {
    param([string]$Output, [string]$Operation, [string]$TransferId)
    $lines = @($Output -split '\r?\n' | Where-Object { $_.StartsWith('MISTY_RESULT:') })
    if ($lines.Count -ne 1) { throw 'Le serveur ne confirme pas le resultat. La sauvegarde locale est conservee.' }
    $result = $lines[0].Substring(13) | ConvertFrom-Json
    if ($result.operation -cne $Operation -or $result.transfer_id -cne $TransferId) { throw 'Confirmation SSH incoherente.' }
    if (-not $result.ok) { throw "Serveur : $($result.error)" }
    return $result
}

function Invoke-Remote {
    param($Connection, [hashtable]$Request)
    $requestJson = $Request | ConvertTo-Json -Depth 10 -Compress
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($requestJson))
    $helper = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'railway-memory-transfer.py'))
    $inputText = ($helper -replace "`r`n", "`n") + "`nrun(json.loads(base64.b64decode('$encoded')))`n"
    # Fixed shell command and ASCII stdin payload avoid Windows/SSH quoting and clipboard issues.
    $remoteCommand = 'if [ -x /app/.venv/bin/python ]; then exec /app/.venv/bin/python -; elif command -v python3 >/dev/null 2>&1; then exec python3 -; else exec python -; fi'
    $reply = Invoke-Captured (Get-Command ssh.exe).Source @('-F', $Connection.Config, '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=20', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=3', 'misty-transfer', $remoteCommand) $inputText
    if ($reply.Output -notmatch '(?m)^MISTY_RESULT:') { throw "Connexion SSH sans resultat. Verifie que le service est Online. $($reply.Error.Trim())" }
    $result = Read-TransferResult $reply.Output $Request.operation $Request.transfer_id
    if ($reply.ExitCode -ne 0) { throw "Connexion interrompue apres l'operation : $($reply.Error.Trim()). Reprendre avec la sauvegarde locale pour verifier." }
    return $result
}

function Save-Export {
    param($Result, [string]$Destination)
    $bytes = [Convert]::FromBase64String($Result.data)
    $partial = "$Destination.partial"
    [IO.File]::WriteAllBytes($partial, $bytes)
    if ((Assert-MemoryFile $partial) -cne $Result.sha256) { throw 'Sauvegarde recue corrompue : empreinte incorrecte.' }
    [IO.File]::Move($partial, $Destination)
}

function Select-Backup {
    param([string]$Folder)
    $seen = @{}
    $files = @(Get-ChildItem -LiteralPath $Folder -Filter 'memory-source-*.json' | Sort-Object CreationTime -Descending | Where-Object {
        try { $hash = Assert-MemoryFile $_.FullName } catch { return $false }
        if ($seen.ContainsKey($hash)) { return $false }
        $seen[$hash] = $true
        return $true
    })
    for ($i = 0; $i -lt $files.Count; $i++) { Write-Host "$($i + 1). $($files[$i].Name) ($($files[$i].Length) octets)" }
    $choice = (Read-Host 'Numero de sauvegarde ou chemin complet').Trim().Trim('"')
    $number = 0
    if ([int]::TryParse($choice, [ref]$number) -and $number -ge 1 -and $number -le $files.Count) { $choice = $files[$number - 1].FullName }
    $null = Assert-MemoryFile $choice
    return (Resolve-Path -LiteralPath $choice).Path
}

function Find-Railway {
    $native = Get-Command railway.exe -ErrorAction SilentlyContinue
    if ($native) { return $native.Source }
    $shim = Get-Command railway.cmd -ErrorAction Stop
    $candidate = Join-Path (Split-Path $shim.Source) 'node_modules\@railway\cli\bin\railway.exe'
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    throw 'Railway CLI introuvable. Installer ou mettre a jour avec npm.cmd install -g @railway/cli.'
}

if ($LibraryOnly) { return }
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$source = $null
try {
    $script:RailwayExe = Find-Railway
    $null = Get-Command ssh.exe, ssh-keygen.exe -ErrorAction Stop
    if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'railway-memory-transfer.py'))) { throw 'railway-memory-transfer.py doit rester a cote du .bat et du .ps1.' }
    $backupRoot = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Mistybot Railway Backups'
    $null = New-Item -ItemType Directory -Path $backupRoot -Force
    $script:SessionFolder = Join-Path $backupRoot '.transfer-session'
    $null = New-Item -ItemType Directory -Path $script:SessionFolder -Force
    Set-Location -LiteralPath $script:SessionFolder
    $id = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
    Write-Host 'MISTYBOT - TRANSFERT AUTOMATIQUE DE MEMOIRE' -ForegroundColor Cyan
    Write-Host "1. Recuperer la memoire actuelle depuis Railway`n2. Utiliser une sauvegarde deja presente sur ce PC"
    $mode = Read-Host 'Choix 1 ou 2'
    if ($mode -eq '1') {
        Connect-Service 'SOURCE'
        $connection = New-Connection
        Write-Host 'Telechargement de la memoire et verification...'
        $export = Invoke-Remote $connection @{ operation = 'export'; transfer_id = $id }
        $source = Join-Path $backupRoot "memory-source-$id.json"
        Save-Export $export $source
    } elseif ($mode -eq '2') { $source = Select-Backup $backupRoot }
    else { throw 'Choix annule.' }
    $hash = Assert-MemoryFile $source
    Write-Host "SAUVEGARDE VALIDE : $source" -ForegroundColor Green
    if ((Read-Host 'Installer sur un autre service maintenant ? O/N') -notmatch '^(o|oui)$') { exit 0 }
    Connect-Service 'CIBLE'
    Write-Host 'Sur le service CIBLE : volume /app/data et Start Command = sleep infinity, puis deployer et attendre Online.' -ForegroundColor Yellow
    Write-Host 'La memoire cible existante sera sauvegardee avant remplacement.'
    if ((Read-Host 'Ecris RESTAURER quand le service cible est pret') -cne 'RESTAURER') { throw 'Restauration annulee.' }
    $connection = New-Connection
    while ($true) {
        try { $null = Invoke-Remote $connection @{ operation = 'probe'; transfer_id = $id }; break }
        catch {
            Write-Host $_.Exception.Message -ForegroundColor Yellow
            if ((Read-Host 'Apres correction sur Railway : R pour reessayer, Entree pour quitter') -notmatch '^[rR]$') { throw }
            $connection = New-Connection
        }
    }
    Write-Host 'Envoi, sauvegarde de la cible et verification automatique...'
    $data = [Convert]::ToBase64String([IO.File]::ReadAllBytes($source))
    $result = Invoke-Remote $connection @{ operation = 'restore'; transfer_id = $id; sha256 = $hash; data = $data }
    if ($result.sha256 -cne $hash) { throw 'Empreintes differentes : transfert NON confirme.' }
    $receipt = Join-Path $backupRoot "transfer-verified-$id.json"
    [IO.File]::WriteAllText($receipt, ($result | ConvertTo-Json -Depth 10), (New-Object Text.UTF8Encoding($false)))
    Write-Host "`nTRANSFERT VERIFIE : la copie sur le volume est identique a la sauvegarde." -ForegroundColor Green
    Write-Host "Sauvegarde locale : $source`nConfirmation : $receipt"
    Write-Host 'Arrete ancien bot, remets python main.py sur le nouveau service puis redeploie.'
} catch {
    Write-Host "`nTRANSFERT NON CONFIRME : $($_.Exception.Message)" -ForegroundColor Red
    if ($source) { Write-Host "Sauvegarde conservee : $source" }
    Write-Host 'Laisse la cible avec sleep infinity. Relance le .bat et choisis 2 pour reprendre ta sauvegarde.'
    exit 1
}
