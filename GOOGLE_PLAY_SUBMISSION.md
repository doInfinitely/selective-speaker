# Google Play Store Submission Guide

## ✅ What You Have Ready

- ✅ **Signed AAB:** `android/app/build/outputs/bundle/release/app-release.aab`
- ✅ **App Icon:** Already in the app
- ✅ **Firebase Authentication:** Configured
- ✅ **Backend API:** Deployed on Railway

---

## 📋 Requirements Checklist

### Required Before Submission

- [ ] Google Play Developer Account ($25 one-time fee)
- [ ] Privacy Policy (see `PRIVACY_POLICY.md`)
- [ ] App screenshots (at least 2)
- [ ] Feature graphic (1024x500)
- [ ] High-res icon (512x512)
- [ ] Store listing text
- [ ] Content rating questionnaire
- [ ] Data safety form

---

## 🚀 Step-by-Step Submission Process

### Step 1: Create Google Play Developer Account

1. **Go to:** [Google Play Console](https://play.google.com/console/signup)
2. **Sign in** with your Google account
3. **Pay $25** registration fee (one-time, credit card)
4. **Complete identity verification** (required)
5. **Accept Developer Distribution Agreement**

⏰ **Time:** 24-48 hours for verification

---

### Step 2: Create New App

1. **Open** [Google Play Console](https://play.google.com/console)
2. **Click** "Create app"
3. **Fill in details:**
   - **App name:** Selective Speaker
   - **Default language:** English (United States)
   - **App or Game:** App
   - **Free or Paid:** Free
   - **Declarations:** Check all boxes (you agree to policies)

---

### Step 3: Prepare Store Listing Assets

#### A. Screenshots (Required)

**Need:** At least 2 phone screenshots

**Specifications:**
- **Size:** 1080x1920 or 1920x1080 (portrait or landscape)
- **Format:** PNG or JPEG
- **Max file size:** 8MB each

**How to capture:**
1. Open the app on your phone
2. Take screenshots of key features:
   - Sign-in screen
   - Main recording screen (with some utterances)
   - Enrollment screen
   - Playback/utterance view

**Or use Android Studio's emulator:**
```bash
# Start emulator
cd android
./gradlew installRelease
# Then take screenshots using the camera button in emulator
```

#### B. Feature Graphic (Required)

**Size:** 1024x500 pixels
**Format:** PNG or JPEG

**Suggestion:** Use a simple design with:
- App name "Selective Speaker"
- Tagline: "AI-Powered Voice Transcription"
- Clean gradient background
- Microphone icon

**Tools:**
- [Canva](https://www.canva.com/) - Free, easy to use
- Figma - More advanced
- Photoshop/GIMP - If you have design software

#### C. High-Res Icon (Required)

**Size:** 512x512 pixels
**Format:** PNG (32-bit with alpha)

Extract your app icon and upscale it, or use the existing drawable:
```bash
# Your icon is in: android/app/src/main/res/drawable/ic_notification.xml
# You'll need to export it as 512x512 PNG
```

---

### Step 4: Write Store Listing

#### Short Description (Max 80 characters)
```
AI voice recorder that transcribes only your speech from conversations
```

#### Full Description (Max 4000 characters)

```
Selective Speaker uses advanced AI to record conversations and transcribe only your voice, filtering out background noise and other speakers.

🎯 KEY FEATURES

✓ Voice Enrollment
Train the app to recognize your unique voice in seconds. Our AI learns your vocal patterns for accurate speaker identification.

✓ Selective Transcription
Record conversations, meetings, or interviews and get transcripts of only what YOU said. Perfect for personal notes without capturing others' words.

✓ Speaker Verification
Advanced AI-powered speaker embeddings ensure only your speech is transcribed, even in noisy environments with multiple people talking.

✓ Location Context
Each recording is tagged with your location, so you always remember where the conversation took place.

✓ Secure & Private
All recordings are encrypted and stored securely in your personal account. Only you can access your transcriptions.

✓ Easy Playback
Listen back to any utterance with a single tap. Review your notes anytime, anywhere.

📱 PERFECT FOR

• Meeting notes and action items
• Interview recordings (your questions/responses)
• Personal voice journal
• Lecture notes (your questions/comments)
• Phone call summaries
• Brainstorming sessions

🔒 PRIVACY FIRST

We take your privacy seriously:
- End-to-end encryption for all recordings
- Firebase authentication for secure login
- Your data is never shared or sold
- Delete recordings anytime
- GDPR compliant

🚀 HOW IT WORKS

1. Sign up with email (Firebase authentication)
2. Enroll your voice (15-20 seconds)
3. Start recording any conversation
4. Get instant transcripts of YOUR speech only
5. Review, search, and playback anytime

💡 TECHNOLOGY

Powered by:
- AssemblyAI for speech recognition
- Pyannote.audio for speaker identification
- Advanced AI speaker embeddings
- Real-time voice activity detection

⚡ REQUIREMENTS

- Android 8.0 (Oreo) or higher
- Microphone permission (for recording)
- Internet connection (for transcription)
- Location permission (optional, for context)

📧 SUPPORT

Questions or feedback? Email us at: support@selectivespeaker.app

🌟 Try Selective Speaker today and never miss an important word again!
```

#### App Category
```
Productivity
```

#### Tags (up to 5)
```
voice recorder, transcription, AI, speech-to-text, meeting notes
```

---

### Step 5: Upload App Bundle

1. **In Play Console**, go to **Production** → **Create new release**
2. **Click** "Upload"
3. **Select:** `android/app/build/outputs/bundle/release/app-release.aab`
4. **Add Release Notes:**

```
Initial release of Selective Speaker

Features:
- Voice enrollment for speaker recognition
- AI-powered selective transcription
- Secure Firebase authentication
- Location tagging for recordings
- Audio playback of individual utterances
- Clean, intuitive interface

Thank you for trying Selective Speaker!
```

5. **Click** "Next"

---

### Step 6: Content Rating

1. **Go to:** Content Rating section
2. **Start Questionnaire**
3. **Answer questions:**

**Your app category:** Utility, Productivity, Communication, or Business Tools

**Key questions:**
- Does your app contain violence? **NO**
- Does your app contain sexual content? **NO**
- Does your app contain language? **NO** (just transcription)
- Does your app contain controlled substances? **NO**
- Does your app allow user interaction? **YES** (recording)
- Does your app share user location? **YES** (optional)
- Does your app have age restrictions? **NO** (all ages)

**Result:** Should get **Everyone** or **Everyone 10+** rating

---

### Step 7: Data Safety Section

**CRITICAL:** This is required. Answer honestly about what data you collect.

#### What data does your app collect?

**✅ Personal Information**
- Email address (for Firebase auth)

**✅ Voice or Audio**
- Voice recordings (core feature)
- Audio files

**✅ Location**
- Approximate location (GPS coordinates for context)

**✅ Account Info**
- User ID
- Authentication tokens

#### How is data used?

- **App functionality** (transcription, storage)
- **Authentication** (Firebase)

#### Is data shared with third parties?

**YES:**
- AssemblyAI (for transcription) - processing only
- Firebase (for authentication and storage)
- Railway/Render (backend hosting)

#### Is data encrypted?

**YES:**
- Data is encrypted in transit (HTTPS)
- Data is encrypted at rest (Firebase/PostgreSQL)

#### Can users request data deletion?

**YES:**
- Users can delete recordings from the app
- Users can request account deletion

---

### Step 8: Privacy Policy (REQUIRED)

**You MUST host a privacy policy online.** I've created one for you in `PRIVACY_POLICY.md`.

**To host it:**

**Option A: GitHub Pages (Free)**
1. Create a new repo or use existing
2. Enable GitHub Pages in repo settings
3. Upload privacy policy as `privacy.html`
4. URL: `https://yourusername.github.io/selective-speaker/privacy.html`

**Option B: Your own website**
Host it anywhere you have a domain.

**Option C: Firebase Hosting (Free)**
```bash
firebase init hosting
# Copy PRIVACY_POLICY.md as privacy.html
firebase deploy
```

**Then paste the URL in Play Console.**

---

### Step 9: App Access

**Does your app require login?**
**YES** - Firebase authentication required

**Provide test account for reviewers:**
- **Email:** `reviewer@selectivespeaker.app` (or create a test account)
- **Password:** [Create a test account and provide credentials]

⚠️ **IMPORTANT:** Create a real test account they can use to review the app!

---

### Step 10: Complete All Tasks

In Play Console, go through the dashboard and complete:

- [ ] Store listing (text, screenshots, graphics)
- [ ] App content (content rating, target audience)
- [ ] Privacy policy URL
- [ ] App access (test account)
- [ ] Ads (declare if your app has ads - NO for this app)
- [ ] Upload app bundle
- [ ] Pricing & distribution (countries where available)

---

### Step 11: Submit for Review

1. **Review** all sections in the dashboard
2. **Check** that all tasks are marked as complete
3. **Click** "Send for review"
4. **Wait** for review (typically 2-7 days for first submission)

---

## ⏱️ Timeline

- **Account creation:** 24-48 hours (verification)
- **Asset preparation:** 2-4 hours (screenshots, graphics, text)
- **First review:** 3-7 days
- **Subsequent updates:** 1-2 days

---

## 📝 After Submission

**You'll be notified via email when:**
- Review starts
- App is approved/rejected
- App goes live on Play Store

**If rejected:**
- Read the rejection reason carefully
- Fix the issues mentioned
- Resubmit (usually reviewed faster)

**Common rejection reasons:**
1. Missing or inadequate privacy policy
2. Incorrect data safety declarations
3. App crashes during review (provide stable test account!)
4. Misleading store listing
5. Missing content rating

---

## 🎯 Next Steps

### Immediate (Do Now):

1. **Create Play Console account** ($25 fee)
2. **Take app screenshots** (use your phone or emulator)
3. **Create feature graphic** (use Canva)
4. **Create test account** for reviewers
5. **Host privacy policy** (GitHub Pages)

### During Submission (2-3 hours):

6. **Fill out store listing** (use text above)
7. **Complete content rating** questionnaire
8. **Fill out data safety** form
9. **Upload AAB** file
10. **Submit for review**

### After Approval (1-2 days):

11. **Monitor reviews** and respond
12. **Fix any reported bugs**
13. **Plan updates** and new features

---

## 🆘 Need Help?

**Common Issues:**

**"Bundle upload failed"**
- Ensure signing key is correct
- Check version code (increment for updates)

**"Privacy policy not accessible"**
- Make sure URL is publicly accessible
- Must be HTTPS (not HTTP)

**"App crashes during review"**
- Ensure test account works
- Check backend is running (Railway)
- Test thoroughly before submission

**"Data safety declarations unclear"**
- Be specific about what data you collect
- Explain why you collect it
- Be honest about third-party sharing

---

## 🎉 You're Ready!

Your AAB is built and signed. Follow the steps above to get your app on the Play Store!

**File location:**
```
android/app/build/outputs/bundle/release/app-release.aab
```

**Good luck with your submission! 🚀**

