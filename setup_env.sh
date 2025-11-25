#!/bin/bash
# Helper script to set up .env file

echo "========================================="
echo "Environment Setup Helper"
echo "========================================="
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists!"
    echo ""
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
        exit 0
    fi
fi

# Get DATABASE_URL
echo "Step 1: Database URL"
echo "─────────────────────"
echo "Get your Supabase connection string:"
echo "  1. Go to https://supabase.com/dashboard"
echo "  2. Select project: attuned-survey (ihbscdgkgeewnhdprhfx)"
echo "  3. Go to Settings → Database"
echo "  4. Find 'Connection String' → 'URI'"
echo "  5. Copy the full connection string"
echo ""
echo "It should look like:"
echo "  postgresql://postgres.[project]:[password]@aws-0-us-east-2.pooler.supabase.co:5432/postgres"
echo ""
read -p "Paste your DATABASE_URL: " DATABASE_URL

if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL cannot be empty"
    exit 1
fi

# GROQ_API_KEY - Set this to your actual Groq API key
GROQ_API_KEY="your_groq_api_key_here"

# Create .env file
cat > .env << EOF
# Database (Supabase PostgreSQL)
DATABASE_URL=$DATABASE_URL

# Groq AI Configuration
GROQ_API_KEY=$GROQ_API_KEY
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1

# Recommender Engine Configuration
ATTUNED_PROFILE_VERSION=0.4
ATTUNED_DEFAULT_TARGET_ACTIVITIES=25
ATTUNED_DEFAULT_BANK_RATIO=0.5
ATTUNED_DEFAULT_RATING=R

# Feature Flags
REPAIR_USE_AI=true
GEN_TEMPERATURE=0.6

# Flask Configuration
FLASK_ENV=development
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""
echo "Configuration:"
echo "  DATABASE_URL: ${DATABASE_URL:0:50}..."
echo "  GROQ_API_KEY: ${GROQ_API_KEY:0:20}..."
echo ""
echo "Next steps:"
echo "  ./start_backend.sh"
echo ""

