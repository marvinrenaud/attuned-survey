#!/bin/bash
# Backend startup script with environment validation

set -e

cd "$(dirname "$0")/backend"

echo "========================================="
echo "Attuned Backend Startup"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Create it with:"
    echo "  cp ../.env.example ../.env"
    echo ""
    echo "Then edit .env and set:"
    echo "  DATABASE_URL=your_supabase_connection_string"
    echo "  GROQ_API_KEY=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"
    exit 1
fi

# Load environment variables
echo "Loading environment variables..."
export $(grep -v '^#' ../.env | xargs)

# Validate critical variables
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL not set in .env file!"
    echo ""
    echo "Please add to .env:"
    echo "  DATABASE_URL=postgresql://user:pass@host:5432/database"
    exit 1
fi

if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  Warning: GROQ_API_KEY not set (recommendations will fail)"
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo ""
    echo "Create it with:"
    echo "  cd backend"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
fi

echo "✅ Environment ready!"
echo ""
echo "Database: ${DATABASE_URL:0:30}..."
echo "Groq Key: ${GROQ_API_KEY:0:20}..."
echo ""
echo "Starting Flask backend on port 5001..."
echo "========================================="
echo ""

# Start Flask
python -m flask --app src.main run --port 5001 --debug

