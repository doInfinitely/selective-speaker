#!/bin/bash
set -e

echo "🚀 Starting Selective Speaker Backend..."

# Create database tables
echo "📊 Creating database tables..."
python -c "from app.db import Base, engine; import app.models; Base.metadata.create_all(engine)"

echo "✅ Database tables created successfully!"

# Start the application
echo "🌐 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

