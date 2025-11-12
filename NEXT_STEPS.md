# 🚀 Next Steps to Deploy

You're 90% done! Here's what's left in order:

---

## Step 1: Create Firebase Project (10 minutes)

### 1.1. Create Project
1. Go to https://console.firebase.google.com/
2. Click "Add project" or "Create a project"
3. Name it: `selective-speaker` or whatever you prefer
4. Disable Google Analytics (not needed for this app)
5. Click "Create project"

### 1.2. Enable Authentication
1. In Firebase Console, click "Authentication" in left sidebar
2. Click "Get started"
3. Click "Sign-in method" tab
4. Enable "Email/Password"
5. Click "Save"

### 1.3. Get Service Account Key (for Backend)
1. Click the gear icon ⚙️ → "Project settings"
2. Go to "Service accounts" tab
3. Click "Generate new private key"
4. Save the JSON file as `firebase-service-account.json`
5. **Keep this file safe** - don't commit to git!

### 1.4. Register Android App (for Mobile)
1. In Firebase Console, click the Android icon to add an Android app
2. Package name: `ai.gauntlet.selectivespeaker`
3. App nickname: `Selective Speaker`
4. Leave SHA-1 blank for now (can add later for Google Sign-In)
5. Click "Register app"
6. Download `google-services.json`
7. **Save this for Step 3**

---

## Step 2: Deploy to Railway (15 minutes)

### 2.1. Create Railway Account
1. Go to https://railway.app
2. Sign up with your GitHub account
3. Authorize Railway to access your repos

### 2.2. Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `selective-speaker` repository
4. Railway will detect it's a Python app

### 2.3. Add PostgreSQL Database
1. In your project, click "New" button
2. Select "Database" → "PostgreSQL"
3. Railway automatically creates it and sets `DATABASE_URL`

### 2.4. Set Environment Variables

Click on your web service → "Variables" tab → "Raw Editor", paste this:

```env
ENV=production
STORAGE_ROOT=/app/data

ASSEMBLYAI_API_KEY=<your-assemblyai-key>
ASSEMBLYAI_WEBHOOK_SECRET=<generate-a-random-secret>
WEBHOOK_BASE_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}

AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1

HUGGINGFACE_TOKEN=<your-hf-token>

USE_CLOUDINARY=true
CLOUDINARY_CLOUD_NAME=dqklnveay
CLOUDINARY_API_KEY=777945456343547
CLOUDINARY_API_SECRET=ZpmIRkRks2qjVujN9HFXma0PasI
CLOUDINARY_FOLDER=selective-speaker

PAD_MS=0
ENROLL_DOMINANCE=0.8
SEGMENT_GAP_MS=500
SEGMENT_MIN_MS=1000
SEGMENT_MIN_CHARS=6
USE_MAJORITY_SPEAKER=false
```

**Note:** Railway's `${{RAILWAY_PUBLIC_DOMAIN}}` will auto-fill with your domain!

### 2.5. Upload Firebase Service Account

Railway doesn't have file upload, so use this workaround:

**Option 1 - Base64 Encode (Recommended):**

On your local machine:
```bash
cd /Users/remy/Code/gauntlet_ai/selective-speaker
base64 firebase-service-account.json | tr -d '\n'
```

Copy the output, then add to Railway variables:
```env
FIREBASE_SERVICE_ACCOUNT_BASE64=<paste-the-long-base64-string>
```

Then I'll update the code to decode it.

**Option 2 - Use Environment Variable:**
Paste the entire JSON content as a single line (not recommended, messy).

### 2.6. Deploy!
1. Railway deploys automatically
2. Check "Deployments" tab for logs
3. Once deployed, click "Settings" → "Generate Domain"
4. Your URL: `https://your-app.up.railway.app`

### 2.7. Test It!
```bash
curl https://your-app.up.railway.app/health
# Should return: {"status":"healthy"}
```

---

## Step 3: Update Android App (25 minutes)

### 3.1. Add google-services.json
1. Copy the `google-services.json` from Step 1.4
2. Put it in: `/Users/remy/Code/gauntlet_ai/selective-speaker/android/app/`
3. Verify it's there: `ls android/app/google-services.json`

### 3.2. Update Backend URL

Edit `android/app/build.gradle.kts`, find this line:
```kotlin
buildConfigField("String", "API_BASE_URL", "\"http://10.10.0.202:8000\"")
```

Change to:
```kotlin
buildConfigField("String", "API_BASE_URL", "\"https://your-app.up.railway.app\"")
```

### 3.3. Add Firebase SDK Dependencies

Your `android/app/build.gradle.kts` needs these (I'll add them):
```kotlin
dependencies {
    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.7.0"))
    implementation("com.google.firebase:firebase-auth-ktx")
    implementation("com.google.firebase:firebase-analytics-ktx")
    
    // ... existing dependencies
}
```

And in `android/build.gradle.kts`:
```kotlin
plugins {
    id("com.google.gms.google-services") version "4.4.0" apply false
}
```

### 3.4. Implement Sign-In Flow

I'll create a `SignInActivity.kt` that:
- Shows email/password fields
- Signs in with Firebase
- Gets ID token
- Stores token for API calls

### 3.5. Update API Client

Modify `ApiClient.kt` to send auth token:
```kotlin
private val authInterceptor = Interceptor { chain ->
    val token = getFirebaseToken() // Get from SharedPreferences
    val request = chain.request().newBuilder()
        .addHeader("Authorization", "Bearer $token")
        .build()
    chain.proceed(request)
}
```

---

## Quick Commands Reference

**Check Cloudinary:**
```bash
# Already done! ✅
```

**Deploy to Railway:**
```bash
# 1. Go to railway.app
# 2. Connect GitHub
# 3. Set environment variables
# 4. Deploy!
```

**Test Production API:**
```bash
curl https://your-app.up.railway.app/health
curl https://your-app.up.railway.app/utterances  # Will return 401 without auth
```

---

## Timeline

- **Step 1 (Firebase):** 10 minutes
- **Step 2 (Railway):** 15 minutes  
- **Step 3 (Android):** 25 minutes

**Total:** ~50 minutes to fully deployed and working!

---

## What to Do Right Now

**Choice A - Deploy Backend First (Recommended):**
1. ✅ Cloudinary (Done!)
2. Create Firebase project (10 min)
3. Deploy to Railway (15 min)
4. Test backend works
5. Then update Android app

**Choice B - Complete Firebase First:**
1. ✅ Cloudinary (Done!)
2. Create Firebase project (10 min)
3. Add Firebase to Android (25 min)
4. Deploy to Railway (15 min)

I recommend **Choice A** so you can test the backend immediately!

---

## Ready?

Tell me when you've:
1. Created the Firebase project
2. Got the service account JSON

Then I'll help you deploy to Railway!

