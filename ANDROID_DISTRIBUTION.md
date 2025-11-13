# Android App Distribution Guide

Your signed APK is ready to distribute! Choose your distribution method:

---

## 🚀 Option 1: Firebase App Distribution (RECOMMENDED for Beta Testing)

**Best for:** Sharing with testers quickly (like TestFlight for Android)

### Step 1: Install Firebase CLI

```bash
npm install -g firebase-tools
firebase login
```

### Step 2: Initialize Firebase App Distribution

```bash
cd android
firebase init hosting
# Select your Firebase project: selective-speaker
```

### Step 3: Upload APK to Firebase

```bash
firebase appdistribution:distribute \
  app/build/outputs/apk/release/app-release.apk \
  --app YOUR_FIREBASE_APP_ID \
  --groups testers \
  --release-notes "Initial beta release of Selective Speaker"
```

**To find your Firebase App ID:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `selective-speaker`
3. Go to **Project Settings** → **General**
4. Under "Your apps", find your Android app
5. Copy the **App ID** (format: `1:123456789:android:abc123def456`)

### Step 4: Invite Testers

1. Go to Firebase Console → **App Distribution**
2. Click **Testers & Groups**
3. Add tester emails
4. They'll receive an email with download link

**Testers will need to:**
- Install the Firebase App Distribution app from Play Store
- Accept your invitation
- Download and install your app

---

## 📱 Option 2: Direct APK Distribution

**Best for:** Quick sharing with a few people

### Share the APK file:

**Location:** `android/app/build/outputs/apk/release/app-release.apk`

**Methods:**
- Email the APK file
- Upload to Dropbox/Google Drive and share link
- Use a file transfer service

**Recipients must:**
1. Enable "Install from Unknown Sources" on their Android device:
   - Go to **Settings** → **Security** → **Install unknown apps**
   - Enable for their browser/file manager
2. Download the APK
3. Tap to install

---

## 🏪 Option 3: Google Play Store (Full Production Release)

**Best for:** Public release to millions of users

### Requirements:
- **$25 one-time registration fee**
- **Privacy policy** (required)
- **App content rating**
- **Store listing** (screenshots, description, icon)

### Steps:

#### 1. Create Developer Account
1. Go to [Google Play Console](https://play.google.com/console)
2. Pay $25 registration fee
3. Complete account setup

#### 2. Create App
1. Click **Create app**
2. Fill in app details:
   - **App name:** Selective Speaker
   - **Default language:** English
   - **App or Game:** App
   - **Free or Paid:** Free

#### 3. Prepare Store Listing

**Required assets:**
- **App icon:** 512x512 PNG
- **Feature graphic:** 1024x500 PNG
- **Screenshots:** At least 2 phone screenshots
- **Short description:** Max 80 characters
- **Full description:** Up to 4000 characters

**Example short description:**
```
Record conversations and transcribe only your speech with AI-powered speaker recognition.
```

**Example full description:**
```
Selective Speaker is an intelligent voice recording app that uses advanced AI to transcribe only your voice from conversations.

KEY FEATURES:
• Voice enrollment - Train the app to recognize your voice
• Selective transcription - Only transcribes your speech
• Speaker verification - Uses AI to filter out other voices
• Location tagging - See where each recording was made
• Playback - Listen to individual utterances
• Firebase authentication - Secure, private recordings

PERFECT FOR:
• Meeting notes
• Interview recordings
• Personal voice journals
• Conversation logging

Your recordings are secure and private, stored only for your account.
```

#### 4. Build App Bundle (AAB) for Play Store

Play Store requires AAB format (not APK):

```bash
cd android
./gradlew bundleRelease
```

The AAB will be at: `app/build/outputs/bundle/release/app-release.aab`

#### 5. Upload to Play Console

1. Go to **Production** → **Create new release**
2. Upload the AAB file
3. Add release notes
4. Review and roll out

#### 6. Complete Questionnaires

You'll need to complete:
- **App content** (what data you collect)
- **Target audience** (age rating)
- **Privacy policy** (URL to your privacy policy)
- **App access** (requires login)

#### 7. Submit for Review

- Initial review takes **2-7 days**
- Updates are typically reviewed within **24 hours**

---

## 🎯 Recommended Approach

### For Now: Firebase App Distribution
- **Fastest** way to get the app in testers' hands
- **Free** and easy to use
- Perfect for beta testing
- Can add/remove testers easily

### Later: Google Play Store
- Once you've tested with Firebase
- When you're ready for public release
- Requires more setup but reaches wider audience

---

## 📝 Next Steps for Firebase Distribution

1. **Install Firebase CLI:**
   ```bash
   npm install -g firebase-tools
   ```

2. **Get your Firebase App ID** from Firebase Console

3. **Run the upload command:**
   ```bash
   firebase appdistribution:distribute \
     android/app/build/outputs/apk/release/app-release.apk \
     --app YOUR_APP_ID \
     --groups testers
   ```

4. **Invite testers** via Firebase Console

---

## 🔒 Security Notes

**Important:**
- The signing key (`selective-speaker-release-key.jks`) is in your `android/` folder
- **Password:** `SelectiveSpeaker2024!`
- **Keep this file safe!** Without it, you can't update the app
- It's already in `.gitignore` so it won't be committed to git
- **Back it up** to a secure location

---

## 🆘 Need Help?

**Common Issues:**

1. **"App not installed" error**
   - Uninstall any debug versions first
   - Clear cache and try again

2. **Firebase upload fails**
   - Make sure you're logged in: `firebase login`
   - Check your Firebase App ID is correct

3. **Play Store rejection**
   - Usually due to missing privacy policy or content rating
   - Address the specific issues mentioned in rejection email

---

Let me know which distribution method you want to use and I'll help you set it up! 🚀

