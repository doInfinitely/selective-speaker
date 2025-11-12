# AssemblyAI Integration Guide

This document describes how the Selective Speaker backend integrates with AssemblyAI for speech-to-text with speaker diarization.

---

## 🎯 Overview

The system uses AssemblyAI's speaker diarization to identify and filter the enrolled user's speech from audio recordings.

### How It Works

```
1. User enrolls (30-second sample)
   ↓
2. Android app sends audio chunks
   ↓
3. Backend concatenates: [enrollment] + [silence] + [chunk]
   ↓
4. Upload to AssemblyAI
   ↓
5. AssemblyAI transcribes with diarization
   ↓
6. Webhook callback with speaker-labeled words
   ↓
7. Diarization mapper identifies user's segments
   ↓
8. Store only user's transcribed speech
```

---

## 🔧 Configuration

### 1. Get AssemblyAI API Key

1. Sign up at https://www.assemblyai.com/
2. Get your API key from the dashboard
3. Add to `.env` file:

```bash
ASSEMBLYAI_API_KEY=your_api_key_here
ASSEMBLYAI_WEBHOOK_SECRET=your_webhook_secret_here
WEBHOOK_BASE_URL=https://your-domain.com
```

### 2. Configure Webhook URL

In production, set `WEBHOOK_BASE_URL` to your public domain:

```bash
WEBHOOK_BASE_URL=https://api.yourdomain.com
```

The webhook will be automatically registered as:
```
https://api.yourdomain.com/webhooks/assemblyai
```

### 3. Development Mode

For local development, you can:

**Option A: Use ngrok**
```bash
ngrok http 8000
# Copy the HTTPS URL to WEBHOOK_BASE_URL
```

**Option B: Skip webhook verification**
```bash
# Leave ASSEMBLYAI_WEBHOOK_SECRET=devsecret
# The code will skip signature verification in dev mode
```

---

## 📡 API Flow

### Step 1: Enroll User

```bash
curl -X POST http://localhost:8000/enrollment/complete \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "enrollments/user123.wav",
    "duration_ms": 30000,
    "phrase_text": "This is my enrollment sample"
  }'
```

Response:
```json
{
  "status": "ok",
  "enrollment_id": 1,
  "user_id": 1
}
```

### Step 2: Submit Audio Chunk

```bash
curl -X POST http://localhost:8000/chunks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "chunks/chunk001.wav",
    "device_id": "android-123",
    "gps_lat": 37.7749,
    "gps_lon": -122.4194
  }'
```

Response:
```json
{
  "status": "queued",
  "chunk_id": 1,
  "enrollment_id": 1,
  "enrollment_ms": 30000,
  "message": "Chunk queued for transcription"
}
```

**Background Process:**
1. Concatenate enrollment + silence + chunk
2. Upload to AssemblyAI
3. Submit transcription request
4. Wait for webhook callback

### Step 3: Webhook Callback (Automatic)

AssemblyAI will POST to `/webhooks/assemblyai` when transcription completes:

```json
{
  "transcript_id": "abc123",
  "status": "completed",
  "custom_metadata": {
    "user_id": "1",
    "chunk_id": "1",
    "enrollment_ms": "30000"
  },
  "text": "Full transcript...",
  "words": [
    {
      "start": 0,
      "end": 500,
      "speaker": "A",
      "confidence": 0.92,
      "text": "Hello"
    },
    ...
  ]
}
```

**Processing:**
1. Verify webhook signature
2. Extract diarized words
3. Run enrollment-anchored mapper
4. Store user's segments
5. Geocode GPS coordinates (if present)

### Step 4: Retrieve Utterances

```bash
curl http://localhost:8000/utterances?limit=20
```

Response:
```json
{
  "items": [
    {
      "chunk_id": 1,
      "start_ms": 100,
      "end_ms": 2500,
      "text": "I need to check the blueprint",
      "device_id": "android-123",
      "timestamp": "2025-11-11T10:30:00",
      "address": "123 Main St, San Francisco, CA"
    }
  ],
  "count": 1,
  "has_more": false
}
```

---

## 🎵 Audio Requirements

### File Format

- **Format**: WAV (recommended) or MP3
- **Sample Rate**: 16kHz (recommended) or 44.1kHz
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit PCM

### Enrollment Audio

- **Duration**: 20-40 seconds
- **Content**: Clear speech, user reading provided phrase
- **Quality**: Low background noise, good microphone

### Chunk Audio

- **Duration**: 5-15 seconds (optimal for responsiveness)
- **Content**: Actual speech to transcribe
- **Quality**: Varies (real-world conditions)

### Audio Concatenation

The backend automatically handles:
- Parameter validation (matching sample rate, channels, bit depth)
- Silence padding generation (1000ms by default)
- WAV file creation

---

## 🔐 Webhook Security

### Signature Verification

AssemblyAI signs webhooks using HMAC-SHA256:

```python
expected_signature = hmac.new(
    webhook_secret.encode(),
    request_body,
    hashlib.sha256
).hexdigest()

if signature_header == expected_signature:
    # Valid webhook
```

### Configuration

1. Get webhook secret from AssemblyAI dashboard
2. Set in `.env`: `ASSEMBLYAI_WEBHOOK_SECRET=your_secret`
3. The backend automatically verifies all webhooks

### Development Mode

For testing without real webhooks:
```bash
# Keep default secret
ASSEMBLYAI_WEBHOOK_SECRET=devsecret
```

Signature verification is skipped in dev mode.

---

## 💰 Cost Estimation

AssemblyAI Pricing (as of 2025):
- **Pay-as-you-go**: $0.00025 per second (~$0.015 per minute)
- **Speaker Diarization**: Included (no extra cost)

### Example Costs

**Per User Per Day:**
- 8 hours of recording
- ~500 chunks (5-10 seconds each)
- ~30 minutes of actual speech
- Cost: ~$0.45 per user per day

**Monthly (1000 users):**
- 1000 users × 30 days × $0.45 = $13,500/month
- With VAD filtering (50% silence): ~$6,750/month

### Optimization Tips

1. **Voice Activity Detection**: Only upload chunks with speech
2. **Chunk Size**: Larger chunks (10-15s) reduce overhead
3. **Enrollment Caching**: Store enrollment audio once
4. **Batch Processing**: Group chunks if real-time not needed

---

## 📊 Monitoring

### Backend Logs

```bash
# View logs in real-time
tail -f logs/app.log

# Or use loguru's colored output
uvicorn app.main:app --log-level info
```

### Key Metrics to Track

1. **Chunk Processing Time**
   - Audio concatenation: <1s
   - Upload to AssemblyAI: 1-5s
   - Transcription: 5-30s (depends on audio length)

2. **Transcription Success Rate**
   - Target: >95% successful transcriptions
   - Monitor webhook failures

3. **Diarization Accuracy**
   - Enrollment dominance: Should be >80%
   - Kept segments per chunk: Varies by use case

4. **API Errors**
   - AssemblyAI API errors
   - Webhook signature failures
   - Audio file issues

### Database Queries

```sql
-- Chunks without segments (failed processing)
SELECT c.id, c.created_at, c.audio_url
FROM chunks c
LEFT JOIN segments s ON c.id = s.chunk_id
WHERE s.id IS NULL
  AND c.created_at < NOW() - INTERVAL '1 hour';

-- Average segments per chunk
SELECT AVG(segment_count) as avg_segments
FROM (
  SELECT chunk_id, COUNT(*) as segment_count
  FROM segments
  WHERE kept = true
  GROUP BY chunk_id
) subq;

-- Transcription success rate
SELECT 
  COUNT(*) FILTER (WHERE has_segments) * 100.0 / COUNT(*) as success_rate
FROM (
  SELECT c.id,
    EXISTS(SELECT 1 FROM segments WHERE chunk_id = c.id) as has_segments
  FROM chunks c
) subq;
```

---

## 🐛 Troubleshooting

### 1. "ASSEMBLYAI_API_KEY not configured"

**Solution:** Add your API key to `.env`:
```bash
ASSEMBLYAI_API_KEY=your_actual_key_here
```

### 2. "Invalid signature" on webhook

**Causes:**
- Webhook secret mismatch
- Request body modified in transit
- Using wrong secret

**Solutions:**
- Verify `ASSEMBLYAI_WEBHOOK_SECRET` matches AssemblyAI dashboard
- Check for proxies/middleware modifying request
- In dev mode, use `devsecret`

### 3. No segments created

**Possible causes:**
- Enrollment speaker not dominant
- No matching speaker in chunk
- Audio quality too poor
- File format issues

**Debug:**
```bash
# Check webhook logs
grep "Diarization mapping failed" logs/app.log

# Check database
SELECT * FROM chunks WHERE id = YOUR_CHUNK_ID;
SELECT * FROM segments WHERE chunk_id = YOUR_CHUNK_ID;
```

### 4. "Channel mismatch" or "Sample rate mismatch"

**Solution:** Ensure all audio files have same parameters:
```bash
# Check audio file info
ffprobe enrollment.wav
ffprobe chunk.wav

# Convert if needed
ffmpeg -i input.wav -ar 16000 -ac 1 output.wav
```

### 5. Webhook not received

**Causes:**
- Incorrect WEBHOOK_BASE_URL
- Firewall blocking AssemblyAI
- Server not publicly accessible

**Solutions:**
- Use ngrok for local development
- Check firewall rules
- Verify webhook URL is publicly accessible
- Check AssemblyAI dashboard for webhook status

---

## 🧪 Testing

### Test with Mock Data

```bash
# Test the diarization mapper directly
python scripts/local_map_segments.py \
  --enroll-ms 30000 \
  --stt tests/fixtures/sample_stt.json
```

### Test with Real Audio (requires API key)

1. Create test audio files
2. Set API key in `.env`
3. Submit through API
4. Monitor logs for processing

### Simulate Webhook

```bash
curl -X POST http://localhost:8000/webhooks/assemblyai \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/webhook_payload.json
```

---

## 📚 AssemblyAI API Documentation

- **Main Docs**: https://www.assemblyai.com/docs
- **Speaker Diarization**: https://www.assemblyai.com/docs/audio-intelligence/speaker-diarization
- **Webhooks**: https://www.assemblyai.com/docs/core-transcription/webhooks
- **Error Codes**: https://www.assemblyai.com/docs/core-transcription/error-codes

---

## 🚀 Production Checklist

- [ ] Set real ASSEMBLYAI_API_KEY
- [ ] Configure ASSEMBLYAI_WEBHOOK_SECRET
- [ ] Set public WEBHOOK_BASE_URL
- [ ] Enable HTTPS for webhooks
- [ ] Set up monitoring and alerts
- [ ] Configure log aggregation
- [ ] Test webhook signature verification
- [ ] Set up error tracking (Sentry)
- [ ] Configure retry logic for failed uploads
- [ ] Optimize chunk sizes based on usage
- [ ] Set up cost monitoring
- [ ] Test with production audio quality
- [ ] Load test with concurrent uploads

---

**Status:** ✅ Fully Integrated and Ready for Testing

Last Updated: November 11, 2025

