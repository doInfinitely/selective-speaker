#!/bin/bash
# Quickstart script for Selective Speaker Backend

set -e

echo "🚀 Selective Speaker Backend - Quick Start"
echo "==========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
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
    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi

# Start database
echo ""
echo "🐘 Starting PostgreSQL database..."
docker compose up -d db
sleep 3
echo "✓ Database started"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo ""
    echo "🐍 Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
.venv/bin/pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Create database tables
echo ""
echo "🗄️  Creating database tables..."
.venv/bin/python -c "from app.db import Base, engine; import app.models; Base.metadata.create_all(engine)" 2>/dev/null
echo "✓ Database tables created"

# Create data directory
mkdir -p data/enrollments data/chunks
echo "✓ Storage directories created"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the API server, run:"
echo "  .venv/bin/uvicorn app.main:app --reload"
echo ""
echo "Or for external access:"
echo "  .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""

