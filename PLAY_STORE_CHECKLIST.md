# Google Play Store Submission Checklist

Use this checklist to track your progress toward Play Store submission.

## 📋 Pre-Submission Checklist

### Account Setup
- [ ] Create Google Play Developer account - [Sign up here](https://play.google.com/console/signup)
- [ ] Pay $25 registration fee
- [ ] Complete identity verification (24-48 hours)
- [ ] Accept Developer Distribution Agreement

### App Assets (Required)

#### Built Files
- [x] **App Bundle (AAB)** - `android/app/build/outputs/bundle/release/app-release.aab` ✅
- [x] **Signing key** - `android/selective-speaker-release-key.jks` ✅

#### Graphics (Need to Create)
- [ ] **Screenshots** (min 2, max 8)
  - Size: 1080x1920 or 1920x1080 pixels
  - Format: PNG or JPEG
  - Recommended: 4-6 screenshots showing key features
  
- [ ] **Feature Graphic** (required)
  - Size: 1024x500 pixels
  - Format: PNG or JPEG
  - Use [Canva](https://canva.com) for easy creation
  
- [ ] **High-res Icon** (required)
  - Size: 512x512 pixels
  - Format: PNG with transparency
  - Extract from app icon or create new

#### Store Listing Text (Ready to Copy)
- [x] **App name** - "Selective Speaker" ✅
- [x] **Short description** (80 chars) - See GOOGLE_PLAY_SUBMISSION.md ✅
- [x] **Full description** (4000 chars) - See GOOGLE_PLAY_SUBMISSION.md ✅
- [x] **Category** - Productivity ✅

### Legal & Privacy

#### Privacy Policy (Required)
- [x] **Privacy policy written** - See PRIVACY_POLICY.md ✅
- [ ] **Privacy policy hosted online** (must be publicly accessible HTTPS URL)
  - Option 1: GitHub Pages (free)
  - Option 2: Your own website
  - Option 3: Firebase Hosting
- [ ] **Privacy policy URL added to Play Console**

#### Test Account (Required)
- [ ] **Create test account** for reviewers
  - Email: ________________
  - Password: ________________
- [ ] **Verify test account works** (sign in and test all features)

### Content & Compliance

#### Content Rating
- [ ] **Complete content rating questionnaire**
  - Violence: NO
  - Sexual content: NO
  - Language: NO
  - User interaction: YES (recording)
  - Location sharing: YES (optional)
  - Expected rating: Everyone or Everyone 10+

#### Data Safety (Required)
- [ ] **Complete data safety form**
  - Declare: Email, voice recordings, location
  - Purpose: Authentication, transcription, context
  - Third parties: AssemblyAI, Firebase, Cloudinary
  - Encryption: YES
  - Deletion: YES (users can delete data)

#### App Access
- [ ] **Provide test account credentials** for reviewer access
- [ ] **Verify backend is running** (Railway deployment active)

### Optional (But Recommended)

- [ ] **Promo video** (30 sec - 2 min showing app features)
- [ ] **TV banner** (1280x720) if planning Android TV support
- [ ] **Wear OS support** (if applicable)

---

## 🎨 Asset Creation Guide

### How to Take Screenshots

**Option 1: From Your Phone**
1. Install the app: `cd android && ./gradlew installRelease`
2. Open the app and navigate to key screens
3. Take screenshots (Power + Volume Down on most Android devices)
4. Transfer to computer via USB or cloud storage

**Option 2: From Android Studio Emulator**
1. Start emulator: `cd android && emulator -avd Pixel_6_Pro_API_34`
2. Install app: `./gradlew installRelease`
3. Click camera icon in emulator controls to capture
4. Screenshots saved to: `~/Screenshots/`

**Recommended Screenshots:**
1. Sign-in screen (clean, welcoming)
2. Main screen with some utterances displayed
3. Recording in progress
4. Enrollment screen (voice training)
5. Playback/detail view of an utterance
6. Settings or profile screen (optional)

### How to Create Feature Graphic

**Using Canva (Recommended for Non-Designers):**

1. Go to [Canva.com](https://canva.com)
2. Click "Custom size" → 1024 x 500 px
3. Design your graphic:
   - Add app name: "Selective Speaker"
   - Add tagline: "AI-Powered Voice Transcription"
   - Use microphone icon or waveform graphic
   - Keep it clean and professional
   - Use brand colors (if you have them)
4. Download as PNG

**Tips:**
- Keep text readable at small sizes
- Use high contrast colors
- Don't clutter with too much text
- Show what the app does visually

### How to Create High-Res Icon

Your app icon is in the app, but Play Store needs 512x512 PNG.

**Option 1: Export from Android Studio**
1. Right-click `android/app/src/main/res/drawable/ic_notification.xml`
2. Export as PNG at 512x512

**Option 2: Create New Icon**
- Use [Icon Kitchen](https://icon.kitchen/) - free icon generator
- Or design in Canva/Figma at 512x512

---

## 📤 Hosting Privacy Policy (Choose One)

### Option A: GitHub Pages (Free, Easy)

```bash
# 1. Create a new public repo or use existing
# 2. In your repo settings, enable GitHub Pages
# 3. Convert privacy policy to HTML or use as-is
cp PRIVACY_POLICY.md privacy.md
git add privacy.md
git commit -m "Add privacy policy"
git push

# URL will be: https://yourusername.github.io/repo-name/privacy
```

### Option B: Firebase Hosting (Free)

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and init
firebase login
cd /Users/remy/Code/gauntlet_ai/selective-speaker
firebase init hosting

# Create public/privacy.html from PRIVACY_POLICY.md
# Then deploy
firebase deploy --only hosting

# URL will be: https://your-project.web.app/privacy.html
```

### Option C: Use Your Own Website

If you have a personal website or domain, just upload the privacy policy there.

---

## 🚀 Submission Steps (In Order)

### 1. Complete Play Console Setup (30 min)
- [ ] Create app in Play Console
- [ ] Fill out app details (name, category, etc.)

### 2. Upload Assets (1 hour)
- [ ] Upload screenshots
- [ ] Upload feature graphic
- [ ] Upload high-res icon
- [ ] Add store listing text

### 3. Complete Questionnaires (30 min)
- [ ] Content rating
- [ ] Data safety
- [ ] App access & test account

### 4. Upload App (10 min)
- [ ] Go to Production → Create release
- [ ] Upload AAB file
- [ ] Add release notes
- [ ] Review and rollout

### 5. Submit for Review (5 min)
- [ ] Review all sections
- [ ] Confirm everything is complete
- [ ] Click "Send for review"

---

## ⏱️ Timeline Estimate

| Task | Time Required |
|------|---------------|
| Developer account setup | 24-48 hours (verification) |
| Taking screenshots | 15-30 minutes |
| Creating graphics | 30-60 minutes |
| Writing/reviewing text | 15 minutes (already done!) |
| Hosting privacy policy | 15-30 minutes |
| Creating test account | 5 minutes |
| Filling out forms | 30-45 minutes |
| Uploading everything | 20-30 minutes |
| **First submission review** | **3-7 days** |

---

## 🎯 Quick Start (Do These First)

1. **[ ] Create Play Developer account** - Do this NOW (takes 1-2 days to verify)
2. **[ ] Take screenshots** - Install app on phone and capture
3. **[ ] Host privacy policy** - Use GitHub Pages (easiest)
4. **[ ] Create test account** - Sign up in your app with a test email

Then you'll be ready to complete the submission when your account is verified!

---

## 📧 Test Account Template

When providing test account to Google reviewers, use this format:

```
Test Account Credentials:

Email: reviewer.test@gmail.com
Password: TestPassword123!

Instructions for reviewers:
1. Sign in with the credentials above
2. Complete voice enrollment (tap "Enroll" and speak for 15 seconds)
3. Grant microphone and location permissions when prompted
4. Tap "Start Recording" to begin
5. Speak normally for 10-20 seconds
6. Tap "Stop Recording"
7. Wait 10-15 seconds for transcription to complete
8. View transcribed utterances in the main feed
9. Tap play button to hear audio playback

Note: The app requires an internet connection for transcription.
Backend API is hosted at: https://web-production-f942c.up.railway.app
```

---

## 🆘 Common Issues & Solutions

**"Can't upload AAB"**
- ✅ File is at: `android/app/build/outputs/bundle/release/app-release.aab`
- Check version code (must be unique for each upload)
- Ensure you've completed all required sections first

**"Privacy policy not accessible"**
- URL must be publicly accessible (no login required)
- Must be HTTPS, not HTTP
- Test in incognito browser window

**"Screenshots wrong size"**
- Must be 1080x1920 or 1920x1080 pixels exactly
- Can't be smaller than 320px on shortest side
- Can't be larger than 3840px on longest side

**"App crashes for reviewer"**
- Test with the exact credentials you provided
- Verify backend is running (check Railway dashboard)
- Make sure test account has completed enrollment

---

## ✅ Final Pre-Submission Check

Before clicking "Send for review", verify:

- [ ] All dashboard tasks show green checkmarks
- [ ] Test account works (you've personally tested it)
- [ ] Privacy policy URL is accessible
- [ ] Screenshots show actual app content (no placeholder images)
- [ ] Store listing has no typos
- [ ] AAB is uploaded
- [ ] Backend API is running
- [ ] You've read and accepted all Play Store policies

---

## 🎉 You're Ready!

**Your AAB is built:**
```
android/app/build/outputs/bundle/release/app-release.aab
```

**Next steps:**
1. Create Play Developer account (do this first!)
2. Work through this checklist
3. Submit when everything is complete

**Good luck! 🚀**

