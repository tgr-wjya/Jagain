# manage_agent.ps1
# Script to easily put the Jagain Anti-Scam agent to sleep (deactivate revision) or wake it up (activate revision).

param (
    [Parameter(Mandatory=$true, HelpMessage="Action to perform: start (wake), stop (sleep), or status")]
    [ValidateSet("start", "wake", "stop", "sleep", "status")]
    [string]$Action
)

# Set error action preference to Stop so the script terminates immediately on script error
$ErrorActionPreference = "Stop"

# Helper function to check if the last external CLI command succeeded
function Check-CommandSuccess {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Azure CLI command failed with exit code $LASTEXITCODE. Halting execution." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "Scanning for Jagain Anti-Scam Container App..." -ForegroundColor Cyan
$appInfoJson = az containerapp list --only-show-errors --query "[?name=='jagain-anti-scam']" -o json
Check-CommandSuccess

$appInfo = $appInfoJson | ConvertFrom-Json
if ($appInfo.Count -eq 0 -or $null -eq $appInfo) {
    Write-Host "Error: Could not find any Container App named 'jagain-anti-scam' in the current subscription." -ForegroundColor Red
    exit 1
}

# Extract app details
$appName = $appInfo[0].name
$resourceGroup = $appInfo[0].resourceGroup
$fqdn = $appInfo[0].properties.configuration.ingress.fqdn

Write-Host "Found Jagain Agent in Resource Group: $resourceGroup" -ForegroundColor Green
Write-Host "FQDN: https://$fqdn" -ForegroundColor Green

if ($Action -eq "status") {
    Write-Host "`nFetching agent revision status..." -ForegroundColor Cyan
    $revisionsJson = az containerapp revision list -n $appName -g $resourceGroup --all --only-show-errors -o json
    Check-CommandSuccess
    $revisions = $revisionsJson | ConvertFrom-Json
    
    Write-Host "`nRevision Status:" -ForegroundColor Yellow
    Write-Host "----------------" -ForegroundColor Yellow
    foreach ($rev in $revisions) {
        $activeStr = if ($rev.properties.active) { "ACTIVE" } else { "INACTIVE" }
        $color = if ($rev.properties.active) { "Green" } else { "Red" }
        Write-Host "Revision: $($rev.name)" -NoNewline
        Write-Host " | State: $activeStr" -ForegroundColor $color -NoNewline
        Write-Host " | Running: $($rev.properties.runningState) | Traffic: $($rev.properties.trafficWeight)%"
    }
}
elseif ($Action -eq "stop" -or $Action -eq "sleep") {
    Write-Host "`nPutting Jagain Agent to sleep..." -ForegroundColor Cyan
    
    # Find all currently active revisions
    $revisionsJson = az containerapp revision list -n $appName -g $resourceGroup --all --only-show-errors -o json
    Check-CommandSuccess
    $revisions = $revisionsJson | ConvertFrom-Json
    
    $activeCount = 0
    foreach ($rev in $revisions) {
        if ($rev.properties.active) {
            Write-Host "Deactivating revision: $($rev.name)..." -ForegroundColor Yellow
            $null = az containerapp revision deactivate -n $appName -g $resourceGroup --revision $rev.name --only-show-errors
            Check-CommandSuccess
            $activeCount++
        }
    }
    
    if ($activeCount -eq 0) {
        Write-Host "Agent is already asleep (no active revisions)." -ForegroundColor Yellow
    } else {
        Write-Host "Success: Jagain Agent is now asleep!" -ForegroundColor Green
    }
}
elseif ($Action -eq "start" -or $Action -eq "wake") {
    Write-Host "`nWaking up Jagain Agent..." -ForegroundColor Cyan
    
    # Get the latest revision name of the container app
    $showInfoJson = az containerapp show -n $appName -g $resourceGroup --only-show-errors -o json
    Check-CommandSuccess
    $showInfo = $showInfoJson | ConvertFrom-Json
    $latestRev = $showInfo.properties.latestRevisionName
    
    Write-Host "Activating latest revision: $latestRev..." -ForegroundColor Yellow
    $null = az containerapp revision activate -n $appName -g $resourceGroup --revision $latestRev --only-show-errors
    Check-CommandSuccess
    
    Write-Host "Success: Jagain Agent is now awake and ready!" -ForegroundColor Green
    Write-Host "You can access the agent at: https://$fqdn" -ForegroundColor Green
}
