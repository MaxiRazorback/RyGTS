param(
    [string]$GameExe = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'GTSport.exe'),
    [string]$Title = 'Gran Turismo Sport (RyGT)'
)
$ErrorActionPreference = 'Stop'

$db = Join-Path $env:LOCALAPPDATA 'AMD\CN\gmdb.blb'
if (-not (Test-Path $db)) {
    Write-Host 'AMD Software: Adrenalin Edition was not found (no game list in AMD\CN).'
    exit 1
}
$GameExe = [System.IO.Path]::GetFullPath($GameExe)
if (-not (Test-Path $GameExe)) {
    Write-Host "GTSport.exe was not found at $GameExe. Run Set up first, or pass -GameExe <path>."
    exit 1
}

# Never close or start AMD Software: with its window open, the next start tries again.
if (Get-Process RadeonSoftware -ErrorAction SilentlyContinue) {
    Write-Host 'AMD Software is open; the game list was left alone.'
    exit 3
}

$text = [System.IO.File]::ReadAllText($db)
$data = $text | ConvertFrom-Json
if (-not $data.games -or $data.games.Count -eq 0) {
    Write-Host 'The Adrenalin game list has no entries to copy the format from; add the game once in Adrenalin (Gaming > Add a game) instead.'
    exit 1
}
Copy-Item $db "$db.rygt-backup" -Force

$existing = $data.games | Where-Object { $_.exe_path -ieq $GameExe -or $_.title -eq $Title } | Select-Object -First 1
if ($existing) {
    $entry = $existing
} else {
    $entry = $data.games[0] | ConvertTo-Json -Depth 20 | ConvertFrom-Json
    $entry.guid = '{' + [guid]::NewGuid().ToString() + '}'
    $entry.amdId = -1
    foreach ($name in 'averageFPS', 'percentile95_msec', 'last_played_mins', 'total_played_mins', 'week_played_mins') {
        if ($entry.PSObject.Properties[$name]) { $entry.$name = 0 }
    }
    foreach ($name in 'lastlaunchtime', 'lastperformancereporttime', 'arguments', 'commandline',
                      'image_info', 'install_location', 'lnk_path', 'rendering_process') {
        if ($entry.PSObject.Properties[$name]) { $entry.$name = '' }
    }
    foreach ($name in 'colors', 'overdrive', 'cvdcList') {
        if ($entry.PSObject.Properties[$name]) { $entry.$name = @() }
    }
    foreach ($name in 'profileCustomized', 'is_favourite', 'uninstalled', 'hidden') {
        if ($entry.PSObject.Properties[$name]) { $entry.$name = 'FALSE' }
    }
    $data.games = @($data.games) + $entry
}
$entry.title = $Title
$entry.exe_path = $GameExe
$entry.manual = 'TRUE'
$entry.profileEnabled = 'TRUE'
$entry.hidden = 'FALSE'

$json = $data | ConvertTo-Json -Depth 50
[System.IO.File]::WriteAllText($db, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "$(if ($existing) { 'Updated' } else { 'Added' }) '$Title' -> $GameExe"
Write-Host "Backup of the previous list: $db.rygt-backup"
