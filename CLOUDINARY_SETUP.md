# Cloudinary Setup Guide

Cloudinary provides free cloud storage for audio files (up to 25GB/month on free tier).

## 1. Create Cloudinary Account

1. Go to [https://cloudinary.com/users/register/free](https://cloudinary.com/users/register/free)
2. Sign up for a free account
3. Verify your email

## 2. Get Your Credentials

1. Go to Dashboard: [https://cloudinary.com/console](https://cloudinary.com/console)
2. You'll see your credentials:
   - **Cloud Name**: `your-cloud-name`
   - **API Key**: `123456789012345`
   - **API Secret**: `xxxxx-xxxxxxxxxxxxxx`

## 3. Add to Environment Variables

### For Local Development (`.env`):

```bash
# Cloudinary Settings
USE_CLOUDINARY=false  # Keep as false for local development
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_FOLDER=selective-speaker
```

### For Production (Railway/Render):

Set these environment variables in your hosting platform:

```bash
USE_CLOUDINARY=true
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_FOLDER=selective-speaker
```

## 4. How It Works

### Development Mode (`USE_CLOUDINARY=false`):
- Files stored locally in `./data/`
- Fast, no network calls
- Good for testing

### Production Mode (`USE_CLOUDINARY=true`):
- Files uploaded to Cloudinary
- Accessible from anywhere
- Automatic CDN delivery
- Files organized in `selective-speaker/` folder

## 5. File Organization

Cloudinary will organize files like:
```
selective-speaker/
  ├── enrollment_12345.wav
  ├── chunk_67890.wav
  └── chunk_11111.wav
```

## 6. Usage Limits (Free Tier)

- **Storage**: 25 GB
- **Bandwidth**: 25 GB/month
- **Transformations**: 25,000/month

For this app:
- Each audio file: ~1MB (30 seconds)
- Can store ~25,000 files
- Should be plenty for initial users!

## 7. Upgrade Path

If you exceed limits:
- **Plus Plan**: $89/month (100GB storage, 100GB bandwidth)
- **Advanced Plan**: $249/month (200GB, 200GB)

## 8. Testing

Test upload locally:

```python
from app.services.cloud_storage import upload_audio_file
from pathlib import Path

# This will use local storage (USE_CLOUDINARY=false)
url = upload_audio_file(Path("data/test.wav"))
print(f"Uploaded: {url}")
```

## 9. Security Notes

- **Never commit** your `.env` file with real credentials
- Use environment variables in production
- API Secret should be kept secret!
- Cloudinary URLs are public by default (fine for this app)

## 10. Alternative: AWS S3

If you prefer AWS S3 instead:
- Cheaper for large scale ($0.023/GB/month)
- More configuration required
- Need to set up IAM policies, buckets, etc.

Let me know if you want S3 setup instead!

