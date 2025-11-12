# Firebase Authentication Setup

## Backend Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing
3. Enable Authentication → Sign-in method → Email/Password (or Google)

### 2. Get Service Account Key

1. Go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save the JSON file as `firebase-service-account.json` in project root
4. **DO NOT commit this file to git** (already in `.gitignore`)

### 3. Update `.env`

Add to your `.env` file:

```bash
# Firebase Authentication
FIREBASE_SERVICE_ACCOUNT_KEY=./firebase-service-account.json
```

## Android Setup

### 1. Add Firebase to Android App

1. In Firebase Console, add an Android app
2. Package name: `ai.gauntlet.selectivespeaker`
3. Download `google-services.json`
4. Place it in `android/app/` directory

### 2. Add Firebase Dependencies

Already added in `app/build.gradle.kts`:
- `com.google.firebase:firebase-auth`
- `com.google.firebase:firebase-bom`

### 3. Authentication Flow

The app will:
1. Sign in user with Email/Password (or Google)
2. Get Firebase ID token
3. Send token in `Authorization: Bearer <token>` header
4. Backend verifies token and gets user UID

## Development Mode

**Currently**: Backend allows requests without auth token (returns `dev-uid`)

**Before Production**: Remove the dev-mode fallback in `app/dependencies.py`

```python
# In get_current_user_uid():
if not authorization:
    # TODO: Remove this line for production!
    raise HTTPException(status_code=401, detail="Authorization required")
```

## Testing

Test with curl:
```bash
# Without auth (dev mode)
curl http://localhost:8000/utterances

# With auth (production)
curl -H "Authorization: Bearer <firebase-token>" http://localhost:8000/utterances
```

