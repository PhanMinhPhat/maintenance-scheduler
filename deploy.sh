#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting deployment process..."

# Check for Heroku CLI
if ! command -v heroku &> /dev/null; then
    echo "Installing Heroku CLI..."
    brew tap heroku/brew && brew install heroku
fi

# Check for Azure CLI
if ! command -v az &> /dev/null; then
    echo "Installing Azure CLI..."
    brew install azure-cli
fi

# Backend Deployment (Heroku)
echo "📦 Deploying backend to Heroku..."

# Login to Heroku if needed
heroku login

# Create Heroku app if it doesn't exist
if ! heroku apps:info maintenance-scheduler-api &> /dev/null; then
    echo "Creating Heroku app..."
    heroku create maintenance-scheduler-api
fi

# Add PostgreSQL addon
echo "Adding PostgreSQL database..."
heroku addons:create heroku-postgresql:hobby-dev -a maintenance-scheduler-api

# Set environment variables
echo "Configuring environment variables..."
heroku config:set FLASK_ENV=production -a maintenance-scheduler-api
heroku config:set CORS_ORIGINS=https://maintenance-scheduler-ui.azurestaticapps.net -a maintenance-scheduler-api

# Push to Heroku
echo "Pushing code to Heroku..."
git push heroku main

# Frontend Deployment (Azure Static Web Apps)
echo "📦 Deploying frontend to Azure Static Web Apps..."

# Login to Azure
az login

# Create resource group if it doesn't exist
az group create --name maintenance-scheduler --location "East US"

# Build UI5 application
echo "Building UI5 application..."
cd ui/webapp
npm install
ui5 build preload --clean-dest

# Deploy to Azure Static Web Apps
echo "Deploying to Azure Static Web Apps..."
az staticwebapp create \
  --name maintenance-scheduler-ui \
  --resource-group maintenance-scheduler \
  --source ui/webapp/dist \
  --location "East US" \
  --branch main \
  --api-location "" \
  --app-location "dist" \
  --output-location "dist"

echo "✅ Deployment complete!"
echo "Backend URL: https://maintenance-scheduler-api.herokuapp.com"
echo "Frontend URL: https://maintenance-scheduler-ui.azurestaticapps.net"