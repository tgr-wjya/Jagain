# Set error action preference to Stop so the script terminates immediately on script error
$ErrorActionPreference = "Stop"

# Helper function to check if the last external CLI command succeeded
function Check-CommandSuccess {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Azure CLI command failed with exit code $LASTEXITCODE. Halting execution." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# ==========================================
# STAGE 1: Configuration & Variables Setup
# ==========================================
# Generate a random suffix to ensure resource names are globally unique where required.
$SUFFIX = Get-Random -Minimum 1000 -Maximum 9999
$RG_NAME = "rg-jagain-chatbot"
$LOCATION = "eastus2"
$OPENAI_NAME = "openai-jagain-$SUFFIX"
$SEARCH_NAME = "search-jagain-$SUFFIX"

# ==========================================
# STAGE 2: Prerequisite Checks
# ==========================================
Write-Host "Checking prerequisites..."

# Verify if the Azure CLI ('az') is installed and available in the environment path.
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Azure CLI ('az') is not installed or not in the PATH." -ForegroundColor Red
    Write-Host "Please install it from https://aka.ms/installazurecliwindows before running this script." -ForegroundColor Red
    exit 1
}

# Verify if the user is currently authenticated/logged into their Azure account.
Write-Host "Checking Azure login status..."
$null = az account show 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: You are not logged in to Azure CLI." -ForegroundColor Red
    Write-Host "Please run 'az login' to authenticate with your Azure account first." -ForegroundColor Red
    exit 1
}

# ==========================================
# STAGE 3: Resource Group Creation
# ==========================================
Write-Host "Creating Resource Group: $RG_NAME in location $LOCATION..."
az group create --name $RG_NAME --location $LOCATION
Check-CommandSuccess

# ==========================================
# STAGE 4: Azure OpenAI Service & Model Deployment
# ==========================================
Write-Host "Creating Azure OpenAI Service account: $OPENAI_NAME..."
az cognitiveservices account create --name $OPENAI_NAME --resource-group $RG_NAME --kind OpenAI --sku S0 --location $LOCATION --yes
Check-CommandSuccess

Write-Host "Deploying gpt-4o model..."
az cognitiveservices account deployment create --name $OPENAI_NAME --resource-group $RG_NAME --deployment-name gpt-4o --model-name gpt-4o --model-version "2024-05-13" --model-format CognitiveServices --scale-settings-scale-type "Standard" --capacity 10
Check-CommandSuccess

Write-Host "Deploying text-embedding-3-small model..."
az cognitiveservices account deployment create --name $OPENAI_NAME --resource-group $RG_NAME --deployment-name text-embedding-3-small --model-name text-embedding-3-small --model-version "1" --model-format CognitiveServices --scale-settings-scale-type "Standard" --capacity 20
Check-CommandSuccess

# ==========================================
# STAGE 5: Azure AI Search Service Creation
# ==========================================
# WARNING: Azure allows only a single Free tier (sku: Free) Azure AI Search service per subscription.
# If a Free tier service already exists in this subscription, creation will fail.
Write-Host "WARNING: Azure AI Search allows only ONE Free tier service per subscription." -ForegroundColor Yellow
Write-Host "If you already have a Free search service, the following command will fail." -ForegroundColor Yellow

Write-Host "Creating Azure AI Search Service: $SEARCH_NAME (Free Tier)..."
az search service create --name $SEARCH_NAME --resource-group $RG_NAME --sku Free --location $LOCATION
Check-CommandSuccess

# ==========================================
# STAGE 6: Retrieve Credentials & Write .env
# ==========================================
Write-Host "Retrieving endpoints and keys..."

$OPENAI_KEY = (az cognitiveservices account keys list --name $OPENAI_NAME --resource-group $RG_NAME --query key1 -o tsv)
Check-CommandSuccess

$OPENAI_ENDPOINT = (az cognitiveservices account show --name $OPENAI_NAME --resource-group $RG_NAME --query properties.endpoint -o tsv)
Check-CommandSuccess

$SEARCH_KEY = (az search admin-key show --service-name $SEARCH_NAME --resource-group $RG_NAME --query primaryKey -o tsv)
Check-CommandSuccess

$SEARCH_ENDPOINT = "https://$SEARCH_NAME.search.windows.net"

# Construct .env file content
$ENV_CONTENT = @"
AZURE_OPENAI_API_KEY=$OPENAI_KEY
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_DEPLOYMENT_CHAT=gpt-4o
AZURE_OPENAI_DEPLOYMENT_EMBED=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT
AZURE_SEARCH_API_KEY=$SEARCH_KEY
AZURE_SEARCH_INDEX=sms-scams-index
"@

# Backup existing .env file if it already exists
$envPath = Join-Path $pwd ".env"
$bakPath = Join-Path $pwd ".env.bak"

if (Test-Path $envPath) {
    Write-Host "Warning: Existing .env file found. Renaming it to .env.bak to prevent overwriting." -ForegroundColor Yellow
    if (Test-Path $bakPath) {
        # Remove existing backup file first so renaming doesn't fail
        Remove-Item $bakPath -Force
    }
    Rename-Item -Path $envPath -NewName ".env.bak"
}

Write-Host "Writing environment variables to .env..."
# Write .env without UTF-8 BOM to ensure compatibility across all environments
[System.IO.File]::WriteAllText($envPath, $ENV_CONTENT)

Write-Host "Azure Deployment complete! Check your generated .env file."
