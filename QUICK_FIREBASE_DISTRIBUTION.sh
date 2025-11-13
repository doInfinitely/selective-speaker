#!/bin/bash
# Quick Firebase App Distribution Setup

echo "🚀 Setting up Firebase App Distribution..."

# Install Firebase CLI if not installed
if ! command -v firebase &> /dev/null; then
    echo "📦 Installing Firebase CLI..."
    npm install -g firebase-tools
fi

# Login
echo "🔐 Logging into Firebase..."
firebase login

# Get your Firebase App ID
echo ""
echo "⚠️  NEED YOUR FIREBASE APP ID"
echo "1. Go to: https://console.firebase.google.com/"
echo "2. Select project: selective-speaker"
echo "3. Go to Project Settings → General"
echo "4. Find your Android app"
echo "5. Copy the App ID (format: 1:123456789:android:abc123def456)"
echo ""
read -p "Enter your Firebase App ID: " APP_ID

# Upload APK
echo "📤 Uploading APK to Firebase..."
firebase appdistribution:distribute \
  android/app/build/outputs/apk/release/app-release.apk \
  --app "$APP_ID" \
  --release-notes "Initial beta release of Selective Speaker

Features:
- Voice enrollment
- AI-powered selective transcription
- Location tagging
- Audio playback

Install instructions will be emailed to testers." \
  --groups "testers"

echo ""
echo "✅ Done! Now add testers in Firebase Console:"
echo "https://console.firebase.google.com/project/selective-speaker/appdistribution"

