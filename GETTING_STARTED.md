# 🚀 Getting Started - Selective Speaker Backend

**5-Minute Setup Guide**

---

## Prerequisites

- Python 3.11+ (will work with 3.8+ but 3.11+ recommended)
- Docker & Docker Compose
- Terminal/Command Line

---

## Setup in 5 Steps

### 1️⃣ Start the Database

```bash
docker compose up -d db
```

Wait ~5 seconds for PostgreSQL to initialize.

### 2️⃣ Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment

Create a `.env` file:

```bash
cat > .env << 'EOF'
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/selective
ENV=dev
STORAGE_ROOT=./data
PAD_MS=1000
ENROLL_DOMINANCE=0.8
SEGMENT_GAP_MS=500
SEGMENT_MIN_MS=1000
SEGMENT_MIN_CHARS=6
ASSEMBLYAI_WEBHOOK_SECRET=devsecret
EOF
```

### 5️⃣ Initialize Database

```bash
python -c "from app.db import Base, engine; import app.models; Base.metadata.create_all(engine)"
```

---

## 🎉 You're Ready!

### Start the Server

```bash
uvicorn app.main:app --reload
```

### Test It's Working

Open your browser:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see:
```json
{"status": "healthy"}
```

---

## ✅ Verify Everything Works

### Run Tests

```bash
pytest tests/ -v
```

Expected: **4 passed** ✅

### Test the Mapper

```bash
python scripts/local_map_segments.py \
  --enroll-ms 3000 \
  --stt tests/fixtures/sample_stt.json
```

Expected output:
```
✓ Successfully mapped 1 segment(s)
```

---

## 🎯 Try the API

### 1. Create Enrollment

```bash
curl -X POST http://localhost:8000/enrollment/complete \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "test/enroll.wav",
    "duration_ms": 30000
  }'
```

### 2. Check Enrollment Status

```bash
curl http://localhost:8000/enrollment/status
```

### 3. Submit a Chunk

```bash
curl -X POST http://localhost:8000/chunks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "test/chunk.wav",
    "gps_lat": 37.7749,
    "gps_lon": -122.4194
  }'
```

### 4. View Timeline

```bash
curl http://localhost:8000/utterances
```

---

## 🐛 Troubleshooting

### Database Connection Error

```bash
# Check if database is running
docker compose ps

# Restart database
docker compose restart db
```

### Import Errors

```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

---

## 📖 Next Steps

1. **Read the [README.md](README.md)** for detailed documentation
2. **Check [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** for architecture overview
3. **Explore the [API docs](http://localhost:8000/docs)** interactively
4. **Review the tests** in `tests/` to understand behavior
5. **Modify configuration** in `.env` to tune the mapper

---

## 🔑 Key Concepts

### Enrollment-Anchored Diarization

The system concatenates audio like this:

```
[User's Enrollment Sample] + [Silence Pad] + [New Speech Chunk]
        30 seconds              1 second          5-15 seconds
```

Then:
1. Send to AssemblyAI for diarization
2. Identify which speaker dominated the enrollment section
3. Keep only that speaker's words from the chunk section
4. Store transcribed segments

### Why This Works

- ✅ No ML models to train or manage
- ✅ Works in noisy environments
- ✅ Single API call per chunk
- ✅ Only user's speech is stored

---

## 📁 Project Structure

```
selective-speaker/
├── app/                    # Main application
│   ├── main.py            # FastAPI entry point
│   ├── models.py          # Database models
│   ├── routes/            # API endpoints
│   └── services/          # Business logic
├── tests/                 # Unit tests
├── scripts/               # Helper scripts
├── docker-compose.yml     # PostgreSQL setup
└── .env                   # Configuration
```

---

## 🎓 Learn More

- **[FastAPI Docs](https://fastapi.tiangolo.com/)** - Learn about the framework
- **[AssemblyAI Docs](https://www.assemblyai.com/docs)** - Understand STT & diarization
- **[SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)** - Database ORM

---

## 💬 Common Questions

**Q: Do I need an AssemblyAI API key?**  
A: Not yet. The skeleton is ready, but actual STT calls are stubbed out. You'll need an API key for production.

**Q: Can I use SQLite instead of PostgreSQL?**  
A: Yes, but change `DATABASE_URL` to `sqlite:///./selective.db`. PostgreSQL is recommended for production.

**Q: How do I add authentication?**  
A: Implement Firebase Auth JWT verification in routes. See `TODO` comments in `enrollment.py`.

**Q: Can I deploy this?**  
A: Yes! It's ready for deployment. See README.md for production checklist.

---

**Happy Coding! 🎉**

