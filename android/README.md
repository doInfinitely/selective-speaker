# Selective Speaker Android App

Always-on selective speaker recording Android application.

## Features

- 🎤 **Always-On Recording** - Continuous background audio capture
- 🗣️ **Voice Enrollment** - One-time setup to identify your voice
- 🤖 **Cloud Transcription** - AssemblyAI integration with speaker diarization
- 🔊 **Audio Playback** - Listen to your transcribed utterances
- 📍 **Location Tagging** - GPS coordinates for each recording
- 🔒 **Privacy-First** - Only your speech is transcribed and stored

## Setup

### Prerequisites

- Android Studio Arctic Fox or later
- Android SDK 26+ (API level 26)
- Physical Android device (emulator may not work for audio recording)

### Configuration

1. **Update Backend URL:**
   
   Edit `app/build.gradle.kts`:
   ```kotlin
   buildConfigField("String", "API_BASE_URL", "\"http://YOUR_SERVER_IP:8000\"")
   ```
   
   For local testing:
   - Emulator: `http://10.0.2.2:8000`
   - Physical device: `http://YOUR_COMPUTER_IP:8000`

2. **Get ngrok URL (for physical device):**
   ```bash
   ngrok http 8000
   ```
   Then update `API_BASE_URL` with the ngrok URL.

### Build & Run

1. Open project in Android Studio:
   ```bash
   cd /path/to/selective-speaker/android
   # Open in Android Studio
   ```

2. Sync Gradle files

3. Connect Android device via USB (enable USB debugging)

4. Click Run (▶️) or press Shift+F10

## Usage

### First Time Setup

1. **Grant Permissions**
   - Microphone access
   - Location access
   - Notification access

2. **Enroll Your Voice**
   - Tap "Enroll Voice"
   - Record ~15-20 seconds of your speech
   - Read the provided phrase

3. **Start Recording**
   - Tap "Start Recording"
   - App will continuously record in 30-second chunks
   - Only YOUR speech will be transcribed

### Viewing Transcripts

- Tap "Refresh" to load latest utterances
- Tap ▶️ button to play audio of any utterance
- Scroll through your speech history

## Architecture

```
SelectiveSpeaker/
├── api/                    # Retrofit API client
├── service/                # Background recording service
├── ui/                     # Activities and adapters
│   ├── MainActivity        # Main screen
│   └── UtterancesAdapter   # RecyclerView adapter
└── SelectiveSpeakerApp     # Application class
```

## Permissions

| Permission | Purpose |
|------------|---------|
| `RECORD_AUDIO` | Capture audio from microphone |
| `INTERNET` | Upload to backend API |
| `ACCESS_FINE_LOCATION` | GPS tagging for utterances |
| `FOREGROUND_SERVICE` | Keep recording in background |
| `POST_NOTIFICATIONS` | Show recording notification |

## Troubleshooting

### "Cannot connect to server"

- Check `API_BASE_URL` in build.gradle.kts
- Ensure backend server is running
- For physical device, use ngrok or same WiFi network

### "Permissions denied"

- Go to Settings > Apps > Selective Speaker > Permissions
- Enable all required permissions

### "Recording not working"

- Check if another app is using microphone
- Restart the app
- Check Logcat for errors

## TODO

- [ ] Implement enrollment flow UI
- [ ] Add audio playback functionality
- [ ] Implement VAD (Voice Activity Detection)
- [ ] Add chunk upload to backend
- [ ] Handle network errors gracefully
- [ ] Add settings screen
- [ ] Implement audio compression
- [ ] Add battery optimization handling

## License

MIT

