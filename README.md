# Selective Speaker Backend

**FastAPI backend for diarization-only selective speaker transcription**

An always-on transcription system that captures only the primary user's speech by using enrollment-anchored speaker diarization. Built for frontline workers who need accurate, privacy-respecting conversation records.

---

## 🎯 Overview

This backend implements a sophisticated selective speaker pipeline:

1. **Enrollment**: User records a ~30-second voice sample
2. **Continuous Recording**: Android app sends audio chunks via VAD
3. **Audio Concatenation**: Backend concatenates `[enrollment] + [silence] + [chunk]`
4. **Diarization**: Upload to AssemblyAI for transcription with speaker labels
5. **Selective Filtering**: Keep only segments matching the enrolled speaker
6. **Storage**: Save transcripts with timestamps and GPS locations

### Key Features

- ✅ **Privacy-First**: Only the enrolled user's speech is transcribed
- ✅ **High Accuracy**: Combines diarization with enrollment anchoring
- ✅ **Fully Integrated**: Real AssemblyAI API integration with webhooks
- ✅ **Audio Processing**: Automatic audio concatenation and validation
- ✅ **Scalable**: Built on FastAPI with async support and background tasks
- ✅ **Production-Ready**: Database models, webhook handling, and comprehensive testing

---

## 🏗️ Architecture

```
┌─────────────┐
│   Android   │ Records audio chunks (VAD-triggered)
│     App     │
└──────┬──────┘
       │ POST /chunks/submit
       ↓
┌─────────────────┐
│   FastAPI       │ Stores chunk metadata, enqueues job
│   Backend       │
└────────┬────────┘
         │ Concatenate [enroll + silence + chunk]
         ↓
┌─────────────────┐
│   AssemblyAI    │ Transcribe with diarization
│   STT Service   │
└────────┬────────┘
         │ Webhook: transcription complete
         ↓
┌─────────────────┐
│  Diarization    │ Map speakers, keep only user segments
│    Mapper       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   PostgreSQL    │ Store segments, locations
│   Database      │
└─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for PostgreSQL)
- PostgreSQL 16 (or use Docker)

### 1. Clone and Setup

```bash
cd selective-speaker
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e .
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
cat > .env << EOF
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/selective
ENV=dev
STORAGE_ROOT=./data

# Diarization settings
PAD_MS=1000
ENROLL_DOMINANCE=0.8
SEGMENT_GAP_MS=500
SEGMENT_MIN_MS=1000
SEGMENT_MIN_CHARS=6

# AssemblyAI integration (get your API key from https://www.assemblyai.com/)
ASSEMBLYAI_API_KEY=your_api_key_here
ASSEMBLYAI_WEBHOOK_SECRET=your_webhook_secret_here
WEBHOOK_BASE_URL=http://localhost:8000

# Audio settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
EOF
```

**Note:** For development without real API calls, you can leave the default values. For production, get your API key from [AssemblyAI](https://www.assemblyai.com/).

### 3. Start Database

```bash
docker compose up -d db
```

Verify database is running:
```bash
docker compose ps
```

### 4. Create Tables

Quick setup (use Alembic for production):

```bash
python -c "from app.db import Base, engine; import app.models; Base.metadata.create_all(engine)"
```

### 5. Run API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (Swagger UI)
- **Redoc**: http://localhost:8000/redoc

---

## 📊 Database Schema

### Tables

**users**: User accounts (linked to Firebase Auth)
- `id`, `uid` (Firebase), `display_name`, `email`, `created_at`

**enrollments**: Voice enrollment records
- `id`, `user_id`, `audio_url`, `duration_ms`, `phrase_text`, `edit_distance`, `created_at`

**chunks**: Recorded audio chunks
- `id`, `user_id`, `audio_url`, `device_id`, `start_ts`, `end_ts`, `gps_lat`, `gps_lon`, `created_at`

**segments**: Transcribed speech segments (filtered for user)
- `id`, `chunk_id`, `speaker_label`, `start_ms`, `end_ms`, `text`, `confidence`, `kept`

**locations**: Reverse-geocoded addresses
- `id`, `chunk_id`, `address`, `source`

---

## 🧪 Testing

### Run Unit Tests

```bash
pip install pytest
pytest tests/
```

### Test Diarization Mapper Locally

Use the test script with sample data:

```bash
python scripts/local_map_segments.py \
  --enroll-ms 3000 \
  --stt tests/fixtures/sample_stt.json
```

Expected output:
```json
{
  "status": "ok",
  "user_label": "SPEAKER_00",
  "kept": [
    {
      "start_ms": 100,
      "end_ms": 2600,
      "text": "Hello I said hello world",
      "avg_conf": 0.89
    }
  ]
}
```

---

## 🔌 API Endpoints

### Enrollment

- **POST** `/enrollment/complete` - Complete voice enrollment
- **POST** `/enrollment/reset` - Reset enrollment (re-record)
- **GET** `/enrollment/status` - Check enrollment status

### Chunks

- **POST** `/chunks/submit` - Submit audio chunk for transcription
  - Triggers background processing: concatenation → upload → transcription
- **GET** `/chunks/{chunk_id}` - Get chunk details and segments

### Utterances (Timeline)

- **GET** `/utterances` - List utterances (paginated timeline)
  - Query params: `limit`, `before_id`
- **GET** `/utterances/search?q=query` - Search transcripts

### Webhooks

- **POST** `/webhooks/assemblyai` - AssemblyAI transcription callback
  - Automatically called by AssemblyAI when transcription completes
  - Processes diarization and stores user segments

---

## 🔧 Configuration

Configure via `.env` file or environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg://...` | PostgreSQL connection string |
| `ENV` | `dev` | Environment (dev/prod) |
| `STORAGE_ROOT` | `./data` | Local file storage path |
| `PAD_MS` | `1000` | Silence padding between enrollment and chunk (ms) |
| `ENROLL_DOMINANCE` | `0.8` | Min % of enrollment that must be user's voice |
| `SEGMENT_GAP_MS` | `500` | Max gap to merge adjacent words into segment |
| `SEGMENT_MIN_MS` | `1000` | Minimum segment duration to keep |
| `SEGMENT_MIN_CHARS` | `6` | Minimum text length to keep |
| `ASSEMBLYAI_WEBHOOK_SECRET` | `devsecret` | Webhook signature verification secret |

---

## 📝 Development Workflow

### Typical Flow

1. **Enrollment**:
   ```bash
   curl -X POST http://localhost:8000/enrollment/complete \
     -H "Content-Type: application/json" \
     -d '{
       "audio_url": "enrollments/user123.wav",
       "duration_ms": 30000,
       "phrase_text": "This is my enrollment phrase"
     }'
   ```

2. **Submit Chunk**:
   ```bash
   curl -X POST http://localhost:8000/chunks/submit \
     -H "Content-Type: application/json" \
     -d '{
       "audio_url": "chunks/chunk001.wav",
       "device_id": "android-device-1",
       "gps_lat": 37.7749,
       "gps_lon": -122.4194
     }'
   ```

3. **Webhook Callback** (simulated):
   ```bash
   curl -X POST http://localhost:8000/webhooks/assemblyai \
     -H "Content-Type: application/json" \
     -d @tests/fixtures/webhook_payload.json
   ```

4. **List Utterances**:
   ```bash
   curl http://localhost:8000/utterances?limit=20
   ```

---

## 🛠️ Production Deployment

### ✅ Ready for Production

1. **AssemblyAI Integration**: ✅ Fully implemented
   - Real API calls with upload and transcription
   - Webhook signature verification
   - Custom metadata passing
   - Background task processing

2. **Audio Processing**: ✅ Implemented
   - Audio concatenation with silence padding
   - Format validation and compatibility checking
   - WAV file handling

3. **Logging**: ✅ Configured
   - Loguru for structured logging
   - Request/response tracking
   - Error logging with stack traces

4. **Background Tasks**: ✅ Implemented
   - FastAPI BackgroundTasks for async processing
   - Audio upload and transcription queueing

### 🔄 TODO for Production Scale

1. **Authentication**:
   - Implement Firebase Auth token verification
   - Add JWT middleware for protected routes

2. **Storage**:
   - Replace local storage with S3/GCS
   - Implement presigned URL generation for uploads

3. **Job Queue** (Optional - FastAPI BackgroundTasks may be sufficient):
   - Add Celery + Redis for heavy processing
   - Or use Cloud Tasks for serverless scaling

4. **Geocoding**:
   - Integrate Google Geocoding API or Mapbox
   - Cache results to reduce API calls

5. **Monitoring**:
   - Add Sentry for error tracking
   - Set up centralized logging (CloudWatch/Stackdriver)
   - Implement health checks and metrics

6. **Database**:
   - Set up Alembic migrations properly
   - Add indexes for performance
   - Enable connection pooling

7. **Security**:
   - Enable HTTPS/TLS
   - Implement rate limiting
   - Add CORS configuration
   - Use secrets manager for credentials

8. **Cost Optimization**:
   - Monitor AssemblyAI usage
   - Implement caching strategies
   - Optimize chunk sizes

---

## 📚 Key Files

```
selective-speaker/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration settings
│   ├── db.py                      # Database session management
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── storage.py                 # File storage abstraction
│   ├── routes/
│   │   ├── enrollment.py          # Enrollment endpoints
│   │   ├── chunks.py              # Chunk submission endpoints
│   │   ├── utterances.py          # Timeline/search endpoints
│   │   └── webhooks.py            # Webhook handlers
│   ├── services/
│   │   ├── diarization_mapper.py  # Core enrollment-anchored logic
│   │   ├── assemblyai_client.py   # STT service integration
│   │   └── geocoding.py           # GPS → address conversion
│   └── utils/
│       └── audio.py               # Audio file utilities
├── tests/
│   ├── test_diarization_mapper.py
│   └── fixtures/
│       └── sample_stt.json
├── scripts/
│   └── local_map_segments.py      # Test harness for mapper
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests: `pytest tests/`
4. Check linting (if configured)
5. Submit PR

---

## 📄 License

This project is part of Frontier Audio's Always-On Selective Speaker system.

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker compose ps

# View logs
docker compose logs db

# Restart database
docker compose restart db
```

### Import Errors

Make sure you've installed the package in development mode:
```bash
pip install -e .
```

### Port Already in Use

Change the port in uvicorn command:
```bash
uvicorn app.main:app --reload --port 8001
```

---

## 🎓 Learn More

### Documentation

- **[ASSEMBLYAI_INTEGRATION.md](ASSEMBLYAI_INTEGRATION.md)** - Complete guide to AssemblyAI integration
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Architecture overview and design decisions
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - 5-minute quick start guide

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AssemblyAI API](https://www.assemblyai.com/docs)
- [AssemblyAI Speaker Diarization](https://www.assemblyai.com/docs/audio-intelligence/speaker-diarization)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)

---

**Built with ❤️ for Frontier Audio**

