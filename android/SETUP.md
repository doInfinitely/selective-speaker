# Android App Setup Guide

## Quick Start

### 1. Install Android Studio

Download from: https://developer.android.com/studio

### 2. Open Project

```bash
cd /Users/remy/Code/gauntlet_ai/selective-speaker/android
```

Then: **File > Open** in Android Studio and select the `android` folder.

### 3. Configure Backend URL

**Option A: Using Physical Device (Recommended)**

1. Get your computer's IP address:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. Update `app/build.gradle.kts`:
   ```kotlin
   buildConfigField("String", "API_BASE_URL", "\"http://YOUR_IP:8000\"")
   ```

**Option B: Using Emulator**

Use the special emulator IP:
```kotlin
buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000\"")
```

**Option C: Using ngrok (Best for testing)**

1. Install ngrok: https://ngrok.com/download
2. Start ngrok tunnel:
   ```bash
   ngrok http 8000
   ```
3. Copy the https URL (e.g., `https://abc123.ngrok.io`)
4. Update build.gradle.kts with ngrok URL

### 4. Sync Gradle

In Android Studio:
- Click "Sync Project with Gradle Files" (elephant icon)
- Wait for dependencies to download

### 5. Add Icons (Optional)

The app needs launcher icons. You can:

**Option A: Use Android Studio's Asset Studio**
1. Right-click `res` folder
2. New > Image Asset
3. Choose icon and generate

**Option B: Use placeholder**
- App will use default Android icon for now

### 6. Connect Device

**Physical Device:**
1. Enable Developer Options on phone
2. Enable USB Debugging
3. Connect via USB
4. Allow USB debugging prompt on phone

**Emulator:**
1. Tools > Device Manager
2. Create new device (Pixel 6, API 34)
3. Start emulator

### 7. Run

Click ▶️ **Run** button or press `Shift + F10`

## First Run

1. App will request permissions - **Grant All**
2. Tap "Start Recording" to begin
3. Tap "Refresh" to see transcribed utterances

## Troubleshooting

### Gradle Sync Failed

```bash
# In android folder
./gradlew clean build
```

### Can't Connect to Backend

- Ensure backend is running: `uvicorn app.main:app`
- Check firewall allows port 8000
- Ping your computer IP from phone
- Use ngrok for guaranteed connectivity

### Permissions Denied

Settings > Apps > Selective Speaker > Permissions > Enable all

### Build Errors

1. File > Invalidate Caches > Invalidate and Restart
2. Delete `.gradle` and `.idea` folders
3. Sync again

## Development

### Key Files

- `MainActivity.kt` - Main screen
- `RecordingService.kt` - Background recording
- `ApiClient.kt` - Backend communication
- `build.gradle.kts` - Dependencies and config

### Testing

```bash
# Run tests
./gradlew test

# Run on device
./gradlew installDebug
```

### Logs

View logs in Android Studio:
- View > Tool Windows > Logcat
- Filter by "SelectiveSpeaker"

## Next Steps

- [ ] Test enrollment flow
- [ ] Test continuous recording
- [ ] Verify transcriptions appear
- [ ] Test audio playback
- [ ] Check battery usage

## Need Help?

Check logs in Logcat for detailed error messages!

