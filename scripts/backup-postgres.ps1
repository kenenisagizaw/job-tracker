param(
    [string]$OutputDirectory = ".\backups"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$output = Join-Path $OutputDirectory "job_tracker-$timestamp.sql"

docker compose exec -T db sh -c `
    'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges' |
    Out-File -Encoding utf8 $output

Write-Output "Backup written to $output"
