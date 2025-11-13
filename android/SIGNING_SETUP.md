# Android App Signing Setup

## Generate Signing Key (One-time setup)

Run this command to create a signing key:

```bash
keytool -genkey -v -keystore selective-speaker-release-key.jks \
  -alias selective-speaker -keyalg RSA -keysize 2048 -validity 10000
```

You'll be prompted for:
- **Keystore password** - Choose a strong password
- **Key password** - Can be the same as keystore password
- **Name, Organization, etc.** - Fill in your details

**IMPORTANT:** 
- Keep the `.jks` file and passwords safe!
- Without them, you can't update the app later
- Don't commit the `.jks` file to git

## Configure Gradle for Signing

Add to `android/app/build.gradle.kts`:

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("../selective-speaker-release-key.jks")
            storePassword = System.getenv("KEYSTORE_PASSWORD") ?: "your-keystore-password"
            keyAlias = "selective-speaker"
            keyPassword = System.getenv("KEY_PASSWORD") ?: "your-key-password"
        }
    }
    
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

## Build Signed APK

```bash
cd android
export KEYSTORE_PASSWORD="your-password"
export KEY_PASSWORD="your-password"
./gradlew assembleRelease
```

The signed APK will be at: `app/build/outputs/apk/release/app-release.apk`

