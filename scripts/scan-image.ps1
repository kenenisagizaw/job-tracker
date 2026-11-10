param(
    [string]$Image = "job-tracker-api:latest"
)

$ErrorActionPreference = "Stop"
trivy image --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed $Image
