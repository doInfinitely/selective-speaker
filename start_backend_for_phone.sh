#!/bin/bash
echo "🚀 Starting backend on all network interfaces..."
echo "📱 Your Android phone can connect to: http://10.10.0.202:8000"
echo ""
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
