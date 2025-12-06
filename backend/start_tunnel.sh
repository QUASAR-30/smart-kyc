#!/bin/bash
echo "🚀 Starting Ngrok Tunnel..."
echo "⚠️  Copy the HTTPS URL below (e.g., https://xyz.ngrok-free.app)"
echo "👉 You must update your Genuka App Redirect URI with: <YOUR_HTTPS_URL>/auth/callback"
echo "👉 You must also update your backend .env file with VITE_BACKEND_CALLBACK_URL=<YOUR_HTTPS_URL>/auth/callback"
echo ""
npx ngrok http 8000
