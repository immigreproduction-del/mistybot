[CmdletBinding()]
param(
    [string]$SourceSshCommand,
    [string]$TargetSshCommand
)

$ErrorActionPreference = "Stop"
$RemoteMemoryPath = "/app/data/memory.json"
$BackupRoot = Join-Path $env:USERPROFILE "Desktop\Mistybot Railway Backups"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$SourceBackup = Join-Path $BackupRoot "memory-source-$Timestamp.json"
$TargetCheck = Join-Path $BackupRoot "memory-target-check-$Timestamp.json"

function Write-Step {
    param([string]$Message)

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor DarkCyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor DarkCyan
}

function Read-SshCommand {
    param(
        [string]$Label,
        [string]$ProvidedCommand
    )

    $command = $ProvidedCommand
    while ([string]::IsNullOrWhiteSpace($command)) {
        Write-Host "Dans Railway, ouvre le service $Label, clique sur les trois points," -ForegroundColor Gray
        Write-Host "choisis 'Copy SSH Command', puis colle la commande ci-dessous." -ForegroundColor Gray
        $command = Read-Host "Commande SSH $Label"
    }

    $uuid = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    $projectMatch = [regex]::Match($command, "(?i)--project(?:=|\s+)($uuid)")
    $environmentMatch = [regex]::Match($command, "(?i)--environment(?:=|\s+)($uuid)")
    $serviceMatch = [regex]::Match($command, "(?i)--service(?:=|\s+)($uuid)")

    if (-not $projectMatch.Success -or -not $environmentMatch.Success -or -not $serviceMatch.Success) {
        throw "La commande SSH $Label ne contient pas les trois identifiants Railway attendus."
    }

    return [pscustomobject]@{
        Project = $projectMatch.Groups[1].Value
        Environment = $environmentMatch.Groups[1].Value
        Service = $serviceMatch.Groups[1].Value
    }
}

function Invoke-RailwayChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [int]$Attempts = 1
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        & $script:RailwayExe @Arguments
        if ($LASTEXITCODE -eq 0) {
            return
        }

        if ($attempt -lt $Attempts) {
            $delay = 3 * $attempt
            Write-Warning "Railway a echoue. Nouvelle tentative dans $delay secondes ($attempt/$Attempts)."
            Start-Sleep -Seconds $delay
        }
    }

    throw "La commande Railway a echoue apres $Attempts tentative(s)."
}

function Confirm-RailwayAccount {
    param([string]$Label)

    Write-Host "Compte Railway actuellement connecte :" -ForegroundColor Gray
    & $script:RailwayExe whoami
    $answer = Read-Host "Est-ce bien le compte $Label ? (O/N)"

    if ($answer -notmatch "^(o|oui|y|yes)$") {
        & $script:RailwayExe logout | Out-Host
        Write-Host "Connecte-toi maintenant au compte Railway $Label dans la page qui va s'ouvrir." -ForegroundColor Yellow
        Invoke-RailwayChecked -Arguments @("login")
        Invoke-RailwayChecked -Arguments @("whoami")
    }
}

function Link-RailwayService {
    param(
        [pscustomobject]$Ids,
        [string]$Label
    )

    Write-Host "Connexion au service $Label..." -ForegroundColor Gray
    Invoke-RailwayChecked -Arguments @(
        "link",
        "-p", $Ids.Project,
        "-e", $Ids.Environment,
        "-s", $Ids.Service
    )
}

function Assert-ValidJson {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Fichier introuvable : $Path"
    }

    $file = Get-Item -LiteralPath $Path
    if ($file.Length -le 0) {
        throw "Le fichier est vide : $Path"
    }

    try {
        Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json | Out-Null
    }
    catch {
        throw "Le fichier n'est pas un JSON valide : $Path"
    }
}

try {
    $railwayCommand = Get-Command railway.cmd -ErrorAction SilentlyContinue
    if (-not $railwayCommand) {
        throw "railway.cmd est introuvable. Installe ou reconnecte Railway CLI avant de relancer."
    }
    $script:RailwayExe = $railwayCommand.Source

    Write-Host "TRANSFERT DE LA MEMOIRE MISTYBOT" -ForegroundColor Magenta
    Write-Host "Le script copie uniquement /app/data/memory.json." -ForegroundColor Gray
    Write-Host "Il ne supprime rien et ne coupe aucun worker." -ForegroundColor Gray

    Write-Step "1/5 - Identification des deux services"
    $sourceIds = Read-SshCommand -Label "SOURCE (ancien Railway)" -ProvidedCommand $SourceSshCommand
    $targetIds = Read-SshCommand -Label "CIBLE (nouveau Railway)" -ProvidedCommand $TargetSshCommand

    if ($sourceIds.Service -eq $targetIds.Service) {
        throw "Le service source et le service cible sont identiques. Transfert annule."
    }

    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    Set-Location -LiteralPath $BackupRoot

    Write-Step "2/5 - Sauvegarde depuis l'ancien Railway"
    Confirm-RailwayAccount -Label "SOURCE"
    Link-RailwayService -Ids $sourceIds -Label "source"

    Invoke-RailwayChecked -Arguments @(
        "service", "files", "download",
        $RemoteMemoryPath,
        $SourceBackup,
        "--overwrite"
    ) -Attempts 3

    Assert-ValidJson -Path $SourceBackup
    $sourceFile = Get-Item -LiteralPath $SourceBackup
    $sourceHash = (Get-FileHash -LiteralPath $SourceBackup -Algorithm SHA256).Hash
    Write-Host "Sauvegarde source valide : $($sourceFile.Length) octets" -ForegroundColor Green
    Write-Host "SHA256 source : $sourceHash" -ForegroundColor Green
    Write-Host "Sauvegarde locale : $SourceBackup" -ForegroundColor Green

    Write-Step "3/5 - Connexion au nouveau compte Railway"
    Write-Host "Le script va deconnecter le compte source." -ForegroundColor Yellow
    Read-Host "Appuie sur Entree pour continuer"
    & $script:RailwayExe logout | Out-Host
    Write-Host "Connecte-toi au compte Railway CIBLE dans la page qui va s'ouvrir." -ForegroundColor Yellow
    Invoke-RailwayChecked -Arguments @("login")
    Invoke-RailwayChecked -Arguments @("whoami")
    Link-RailwayService -Ids $targetIds -Label "cible"

    Write-Step "4/5 - Envoi vers le nouveau volume"
    Write-Host "Le volume cible doit etre monte sur /app/data et son service doit fonctionner." -ForegroundColor Gray
    $confirmation = Read-Host "Ecris TRANSFERER pour remplacer $RemoteMemoryPath sur la cible"
    if ($confirmation -cne "TRANSFERER") {
        throw "Confirmation incorrecte. Aucun fichier n'a ete envoye sur la cible."
    }

    Invoke-RailwayChecked -Arguments @(
        "service", "files", "upload",
        $SourceBackup,
        $RemoteMemoryPath,
        "--overwrite"
    ) -Attempts 3

    Write-Step "5/5 - Verification automatique du transfert"
    Invoke-RailwayChecked -Arguments @(
        "service", "files", "download",
        $RemoteMemoryPath,
        $TargetCheck,
        "--overwrite"
    ) -Attempts 3

    Assert-ValidJson -Path $TargetCheck
    $targetFile = Get-Item -LiteralPath $TargetCheck
    $targetHash = (Get-FileHash -LiteralPath $TargetCheck -Algorithm SHA256).Hash

    if ($sourceFile.Length -ne $targetFile.Length) {
        throw "Les tailles source et cible sont differentes. L'ancien worker reste intact."
    }
    if ($sourceHash -ne $targetHash) {
        throw "Les empreintes SHA256 sont differentes. L'ancien worker reste intact."
    }

    Write-Host ""
    Write-Host "TRANSFERT VERIFIE A 100 %" -ForegroundColor Green
    Write-Host "Taille : $($targetFile.Length) octets" -ForegroundColor Green
    Write-Host "SHA256 : $targetHash" -ForegroundColor Green
    Write-Host "Sauvegarde conservee ici : $SourceBackup" -ForegroundColor Green
    Write-Host "Tu peux maintenant arreter l'ancien worker, puis demarrer le nouveau." -ForegroundColor Cyan
    exit 0
}
catch {
    Write-Host ""
    Write-Host "TRANSFERT INTERROMPU" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Aucun worker n'a ete arrete ou supprime par ce script." -ForegroundColor Yellow
    if (Test-Path -LiteralPath $SourceBackup) {
        Write-Host "La sauvegarde locale reste disponible ici : $SourceBackup" -ForegroundColor Yellow
    }
    exit 1
}
