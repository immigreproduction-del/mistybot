[CmdletBinding()]
param([switch]$LibraryOnly)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-MemoryFile {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path
    if ($item.PSIsContainer -or $item.Length -lt 2 -or $item.Length -gt 20MB) {
        throw 'Fichier absent, vide ou trop volumineux (maximum 20 Mo).'
    }
    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $data = $raw | ConvertFrom-Json
    if (-not $raw.TrimStart().StartsWith('{') -or $null -eq $data -or $data -isnot [pscustomobject]) {
        throw 'La memoire doit etre un objet JSON, pas une liste ou du texte.'
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Invoke-Railway {
    param([string[]]$Arguments)
    & $script:RailwayExe @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Railway a echoue. La sauvegarde locale est conservee.' }
}

function Connect-Service {
    param([string]$Label)
    Write-Host "`n=== Compte $Label ===" -ForegroundColor Cyan
    & $script:RailwayExe whoami | Out-Host
    $connected = $LASTEXITCODE -eq 0
    if (-not $connected -or (Read-Host 'Est-ce le bon compte ? O/N') -notmatch '^(o|oui)$') {
        if ($connected) { Invoke-Railway @('logout') }
        Invoke-Railway @('login')
        Invoke-Railway @('whoami')
        if ((Read-Host 'Confirmer ce compte ? O/N') -notmatch '^(o|oui)$') { throw 'Compte non confirme.' }
    }
    Write-Host 'Selectionne le workspace, projet, environnement ET service.'
    Invoke-Railway @('link')
    Invoke-Railway @('status')
    if ((Read-Host "Confirmer ce service comme $Label ? O/N") -notmatch '^(o|oui)$') {
        throw 'Service non confirme.'
    }
}

function Get-Identity {
    Write-Host 'Cle SSH : colle son chemin, ou Entree pour creer une nouvelle cle dediee.'
    $path = (Read-Host 'Chemin de la cle privee').Trim().Trim('"')
    if ($path) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Cle introuvable.' }
        return $path
    }
    $folder = Join-Path $env:USERPROFILE '.ssh'
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    $path = Join-Path $folder ('misty-transfer-' + [guid]::NewGuid().ToString('N'))
    Write-Host 'Choisis une passphrase ou appuie deux fois sur Entree. Aucune cle existante ne sera remplacee.'
    & ssh-keygen -t ed25519 -f $path -C 'mistybot-memory-transfer'
    if ($LASTEXITCODE -ne 0) { throw 'Creation de cle interrompue.' }
    Write-Host "Cle conservee : $path"
    return $path
}

function Open-GuidedSsh {
    param([string]$Commands)
    $identity = Get-Identity
    Set-Clipboard -Value ($Commands -replace "`r`n", "`n")
    Write-Host @'
Les commandes sont dans le presse-papiers.
1. Accepte l'enregistrement de la cle si Railway le demande.
2. A l'invite root@... colle avec Ctrl+V, puis Entree.
3. Copie le resultat du terminal (les marqueurs inclus).
4. Ecris exit pour revenir ici. Ne copie rien d'autre entre-temps.
Ne publie pas la sortie : elle peut contenir la memoire du serveur.
'@ -ForegroundColor Yellow
    & $script:RailwayExe ssh -i $identity
    if ($LASTEXITCODE -ne 0) {
        throw 'SSH indisponible : verifier le service ONLINE, le compte et la cle. Aucun succes presume.'
    }
    Read-Host 'Resultat copie ? Appuie sur Entree pour le verifier' | Out-Null
    return (Get-Clipboard -Raw)
}

function Import-SourceReceipt {
    param([string]$Receipt, [string]$Destination)
    $matches = [regex]::Matches($Receipt, '(?m)^MISTY_SOURCE_BEGIN\r?\n([A-Za-z0-9+/=\s]+?)\r?\nMISTY_SOURCE_END\r?\n([a-fA-F0-9]{64})(?:\s|$)')
    if ($matches.Count -eq 0) { throw 'Sortie source incomplete. Aucun fichier de memoire valide importe.' }
    $match = $matches[$matches.Count - 1]
    $bytes = [Convert]::FromBase64String(($match.Groups[1].Value -replace '\s', ''))
    $partial = "$Destination.partial"
    [IO.File]::WriteAllBytes($partial, $bytes)
    $hash = Assert-MemoryFile $partial
    if ($hash -ne $match.Groups[2].Value.ToLowerInvariant()) { throw 'Empreinte source differente. Copie rejetee.' }
    Move-Item -LiteralPath $partial -Destination $Destination
}

function Get-InstallCommands {
    param([string]$Path, [string]$TransferId)
    $hash = Assert-MemoryFile $Path
    $bytes = [IO.File]::ReadAllBytes($Path)
    $buffer = [IO.MemoryStream]::new()
    $gzip = [IO.Compression.GZipStream]::new($buffer, [IO.Compression.CompressionMode]::Compress, $true)
    try { $gzip.Write($bytes, 0, $bytes.Length) } finally { $gzip.Dispose() }
    $payload = [Convert]::ToBase64String($buffer.ToArray())
    $buffer.Dispose()
    if ($payload.Length -gt 200000) { throw 'Memoire trop volumineuse pour un collage SSH fiable. Aucune installation preparee.' }
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add(@'
(
set -eu
umask 077
v=${RAILWAY_VOLUME_MOUNT_PATH:?Volume non monte}
[ "$v" = /app/data ] || { echo 'MISTY_ERROR: montage attendu /app/data'; exit 1; }
for f in /proc/[0-9]*/cmdline; do
  [ -r "$f" ] || continue
  if tr '\000' '\n' < "$f" | grep -Eq '(^|/)main\.py$'; then
    echo 'MISTY_ERROR: bot actif. Deployer la cible avec sleep infinity avant de restaurer.'
    exit 1
  fi
done
t=$(mktemp -d "$v/.misty-transfer.XXXXXXXX")
trap 'rm -f "$t/payload.b64" "$t/payload.gz" "$t/memory.json"; rmdir "$t"' EXIT
'@)
    for ($i = 0; $i -lt $payload.Length; $i += 900) {
        $chunk = $payload.Substring($i, [Math]::Min(900, $payload.Length - $i))
        $lines.Add(('printf ''%s'' ''{0}'' >> "$t/payload.b64"' -f $chunk))
    }
    $tail = @'
base64 -d "$t/payload.b64" > "$t/payload.gz"
gzip -d -c "$t/payload.gz" > "$t/memory.json"
actual=$(sha256sum "$t/memory.json")
actual=${actual%% *}
[ "$actual" = '__HASH__' ] || { echo 'MISTY_ERROR: empreinte incorrecte, cible intacte'; exit 1; }
b="$v/memory-before-transfer-__ID__.json"
[ ! -e "$b" ] || { echo 'MISTY_ERROR: sauvegarde deja presente, ne pas rejouer'; exit 1; }
if [ -e "$v/memory.json" ]; then
  cp -p "$v/memory.json" "$b"
  cmp -s "$v/memory.json" "$b" || exit 1
fi
mv "$t/memory.json" "$v/memory.json"
actual=$(sha256sum "$v/memory.json")
actual=${actual%% *}
[ "$actual" = '__HASH__' ] || { echo 'MISTY_ERROR: fichier modifie apres installation'; exit 1; }
printf '\nMISTY_TRANSFER_OK:__ID__:%s\n' "$actual"
echo "Sauvegarde cible si elle existait : $b"
)
'@
    $lines.Add($tail.Replace('__HASH__', $hash).Replace('__ID__', $TransferId))
    return ($lines -join "`n")
}

function Test-InstallReceipt {
    param([string]$Receipt, [string]$TransferId, [string]$Hash)
    $expected = [regex]::Escape("MISTY_TRANSFER_OK:${TransferId}:$Hash")
    return [regex]::IsMatch($Receipt, "(?m)^$expected\r?$")
}

if ($LibraryOnly) { return }
try {
    $script:RailwayExe = (Get-Command railway.cmd -ErrorAction Stop).Source
    $backupRoot = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Mistybot Railway Backups'
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Set-Location -LiteralPath $backupRoot
    $id = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
    Write-Host "MISTYBOT - SAUVEGARDE ET RESTAURATION`nDossier : $backupRoot" -ForegroundColor Cyan
    Write-Host "1. Recuperer une memoire depuis Railway`n2. Reprendre une sauvegarde locale (aucun acces a l'ancien compte)"
    $mode = Read-Host 'Choix 1 ou 2'
    $source = Join-Path $backupRoot "memory-source-$id.json"
    if ($mode -eq '2') {
        $files = @(Get-ChildItem -LiteralPath $backupRoot -Filter 'memory-source-*.json' | Sort-Object LastWriteTime -Descending)
        for ($i = 0; $i -lt $files.Count; $i++) { Write-Host "$($i + 1). $($files[$i].Name) ($($files[$i].Length) octets)" }
        $choice = (Read-Host 'Numero de sauvegarde ou chemin complet').Trim().Trim('"')
        $number = 0
        if ([int]::TryParse($choice, [ref]$number) -and $number -ge 1 -and $number -le $files.Count) {
            $choice = $files[$number - 1].FullName
        }
        $null = Assert-MemoryFile $choice
        Copy-Item -LiteralPath $choice -Destination $source
    } elseif ($mode -eq '1') {
        Connect-Service 'SOURCE'
        Write-Host 'Essai SFTP unique. Si le service est SLEEPING ou arrete, il faut le reveiller pour lire sa memoire.'
        $partial = "$source.partial"
        & $script:RailwayExe service files download /app/data/memory.json $partial --overwrite | Out-Host
        if ($LASTEXITCODE -eq 0) {
            $null = Assert-MemoryFile $partial
            Move-Item -LiteralPath $partial -Destination $source
        } else {
            Write-Host 'SFTP indisponible. Passage au secours SSH guide.' -ForegroundColor Yellow
            $commands = @'
(
set -eu
umask 077
v=${RAILWAY_VOLUME_MOUNT_PATH:?Volume non monte}
t=$(mktemp)
trap 'rm -f "$t"' EXIT
cp "$v/memory.json" "$t"
printf '\nMISTY_SOURCE_BEGIN\n'
base64 "$t"
printf '\nMISTY_SOURCE_END\n'
sha256sum "$t"
)
'@
            Import-SourceReceipt (Open-GuidedSsh $commands) $source
        }
    } else { throw 'Choix annule.' }
    $hash = Assert-MemoryFile $source
    Write-Host "`nSAUVEGARDE LOCALE VALIDE : $source`nSHA256 : $hash" -ForegroundColor Green
    if ((Read-Host 'Installer cette sauvegarde sur un autre service maintenant ? O/N') -notmatch '^(o|oui)$') { exit 0 }
    Connect-Service 'CIBLE'
    Write-Host @'
La restauration remplace toute la memoire cible par cette sauvegarde.
Avant de continuer : deployer la CIBLE avec sleep infinity, volume monte sur /app/data.
Le processus du bot doit etre arrete, mais le service doit etre ONLINE pour SSH.
Si la cible dort, la reveiller puis reprendre. Ne pas relancer main.py pendant la copie.
La memoire cible existante sera sauvegardee sur son volume avant remplacement.
'@ -ForegroundColor Yellow
    if ((Read-Host 'Ecris RESTAURER pour confirmer la cible et son remplacement') -cne 'RESTAURER') { throw 'Restauration annulee.' }
    $commands = Get-InstallCommands $source $id
    $receipt = Open-GuidedSsh $commands
    if (-not (Test-InstallReceipt $receipt $id $hash)) {
        throw 'Installation NON CONFIRMEE. Conserver la cible en maintenance et verifier le resultat SSH. La sauvegarde locale reste disponible (choix 2).'
    }
    Write-Host "`nTRANSFERT VERIFIE : empreinte source et cible identiques." -ForegroundColor Green
    Write-Host "Sauvegarde locale : $source"
    Write-Host "Arrete l'ancien bot. Retire sleep infinity sur la cible puis redeploie pour charger la memoire."
    Write-Host 'Conserve les sauvegardes. Aucun service ne sera arrete automatiquement.'
} catch {
    Write-Host "`nOPERATION INTERROMPUE : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Conserve les sauvegardes. Reprends avec le choix 2 si la source a deja ete recuperee.'
    exit 1
}
