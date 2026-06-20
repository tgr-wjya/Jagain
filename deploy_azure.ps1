$SUFFIX = Get-Random -Minimum 1000 -Maximum 9999
$RG_NAME = "rg-jagain-chatbot"
$LOCATION = "eastus2"
$OPENAI_NAME = "openai-jagain-$SUFFIX"
$SEARCH_NAME = "search-jagain-$SUFFIX"

Write-Host "Creating Resource Group: $RG_NAME..."
az group create --name $RG_NAME --location $LOCATION

Write-Host "Creating Azure OpenAI Service: $OPENAI_NAME..."
az cognitiveservices account create --name $OPENAI_NAME --resource-group $RG_NAME --kind OpenAI --sku S0 --location $LOCATION --yes

Write-Host "Deploying gpt-4o model..."
az cognitiveservices account deployment create --name $OPENAI_NAME --resource-group $RG_NAME --deployment-name gpt-4o --model-name gpt-4o --model-version "2024-05-13" --model-format CognitiveServices --scale-settings-scale-type "Standard" --capacity 10

Write-Host "Deploying text-embedding-3-small model..."
az cognitiveservices account deployment create --name $OPENAI_NAME --resource-group $RG_NAME --deployment-name text-embedding-3-small --model-name text-embedding-3-small --model-version "1" --model-format CognitiveServices --scale-settings-scale-type "Standard" --capacity 20

Write-Host "Creating Azure AI Search Service: $SEARCH_NAME (Free Tier)..."
az search service create --name $SEARCH_NAME --resource-group $RG_NAME --sku Free --location $LOCATION

Write-Host "Retrieving endpoints and keys..."
$OPENAI_KEY = (az cognitiveservices account keys list --name $OPENAI_NAME --resource-group $RG_NAME --query key1 -o tsv)
$OPENAI_ENDPOINT = (az cognitiveservices account show --name $OPENAI_NAME --resource-group $RG_NAME --query properties.endpoint -o tsv)
$SEARCH_KEY = (az search admin-key show --service-name $SEARCH_NAME --resource-group $RG_NAME --query primaryKey -o tsv)
$SEARCH_ENDPOINT = "https://$SEARCH_NAME.search.windows.net"

Write-Host "Writing environment variables to .env..."
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
$ENV_CONTENT | Out-File -FilePath ".env" -Encoding utf8
Write-Host "Azure Deployment complete! Check your generated .env file."
