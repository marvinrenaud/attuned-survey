# Backend Testing Guide

## Quick Start - Test the Backend in 5 Minutes

### Step 1: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cd /Users/mr/Documents/attuned-survey
cp .env.example .env
```

Edit `.env` and set these critical values:

```env
# Your existing Supabase database URL
DATABASE_URL=postgresql://postgres.[your-project]:[password]@aws-0-us-east-2.pooler.supabase.co:5432/postgres

# Groq API key (already provided)
GROQ_API_KEY=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
```

### Step 2: Activate Virtual Environment & Install Dependencies

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Start the Flask Backend

```bash
# From the backend directory with venv activated
export $(grep -v '^#' ../.env | xargs)
python -m flask --app src.main run --port 5001 --debug
```

The backend should start and automatically create all new database tables!

### Step 4: Test API Endpoints

Open a NEW terminal window and run these tests:

#### Test 1: Health Check (Existing Endpoint)
```bash
curl http://localhost:5001/api/survey/submissions | jq
```
Expected: List of existing survey submissions

#### Test 2: Generate Recommendations (New!)

First, you need two submission IDs. Get them from test 1, or use these test commands:

```bash
# Get first two submission IDs
SUBMISSION_A=$(curl -s http://localhost:5001/api/survey/submissions | jq -r '.submissions[0].id')
SUBMISSION_B=$(curl -s http://localhost:5001/api/survey/submissions | jq -r '.submissions[1].id')

echo "Testing with: $SUBMISSION_A and $SUBMISSION_B"

# Generate recommendations
curl -X POST http://localhost:5001/api/recommendations \
  -H "Content-Type: application/json" \
  -d "{
    \"player_a\": {\"submission_id\": \"$SUBMISSION_A\"},
    \"player_b\": {\"submission_id\": \"$SUBMISSION_B\"},
    \"session\": {
      \"rating\": \"R\",
      \"target_activities\": 5,
      \"activity_type\": \"random\"
    }
  }" | jq
```

Note: I set `target_activities: 5` for quick testing. You can change to 25 for full sessions.

#### Test 3: Calculate Compatibility (New!)

```bash
curl -X POST http://localhost:5001/api/compatibility \
  -H "Content-Type: application/json" \
  -d "{
    \"submission_id_a\": \"$SUBMISSION_A\",
    \"submission_id_b\": \"$SUBMISSION_B\"
  }" | jq
```

Expected: Compatibility score with breakdown (power, domain, activity, truth)

#### Test 4: Get Cached Compatibility

```bash
curl "http://localhost:5001/api/compatibility/$SUBMISSION_A/$SUBMISSION_B" | jq
```

Expected: Same result as Test 3 (now cached in database)

---

## What to Look For

### ✅ Success Indicators:

1. **Backend starts without errors**
   - You should see: "✅ Database connection successful"
   - New tables created: profiles, sessions, activities, session_activities, compatibility_results

2. **Recommendations endpoint works**
   - Returns JSON with `session_id` and `activities` array
   - Each activity has: type, rating, intensity, script, tags
   - Stats show: total, truths, dares, bank_count, ai_count

3. **Compatibility endpoint works**
   - Returns overall_compatibility score (0-100)
   - Breakdown with power, domain, activity, truth percentages
   - Lists mutual_activities and blocked_activities

### ⚠️ Expected Behaviors:

- **Empty activity bank**: Since you haven't imported activities yet, recommendations will use fallback templates
- **First run slow**: Creating new profiles from submissions takes a moment
- **Groq not called yet**: We're using fallback activities for now (faster testing)

---

## Advanced Testing

### Import Your Activities

When you're ready to import your activity spreadsheet:

```bash
cd backend
source venv/bin/activate
python scripts/import_activities.py /path/to/your/activities.csv --clear
```

The import script expects CSV with columns:
- Activity Type (Truth/Dare)
- Activity Description
- Audience Tag (Couple/Group)
- Intimacy Level (L1-L9)

### Check Database Tables

You can verify tables were created in Supabase Studio or via psql:

```sql
-- Connect to your Supabase database
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('profiles', 'sessions', 'activities', 'session_activities', 'compatibility_results');
```

### Run Backend Tests

```bash
cd backend
source venv/bin/activate

# Test picker logic
python scripts/test_picker.py

# Test validator
python scripts/test_validator.py

# Test compatibility calculator
python scripts/test_compatibility.py

# Test app can start
python scripts/test_app_startup.py
```

All tests should pass with ✅

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'groq'"
- Solution: `pip install -r backend/requirements.txt`

### "DATABASE_URL env var is required"
- Solution: Make sure you're exporting the .env file: `export $(grep -v '^#' .env | xargs)`

### "sslmode is an invalid keyword argument"
- Issue: Using SQLite instead of PostgreSQL
- Solution: Update DATABASE_URL to point to your Supabase PostgreSQL database

### Backend starts but API returns 500 errors
- Check the Flask console for error messages
- Common issue: Survey submissions missing `derived` profile data
- Solution: Make sure your submissions have v0.4 profile data

### Recommendations return empty arrays
- Expected if activity bank is empty
- Solution: Import activities using the import script
- Fallback: System will use safe fallback templates

---

## Quick Command Reference

```bash
# Start backend (from project root)
cd backend && source venv/bin/activate && export $(grep -v '^#' ../.env | xargs) && python -m flask --app src.main run --port 5001

# Test health
curl http://localhost:5001/api/survey/submissions | jq

# Test recommendations (5 activities for speed)
curl -X POST http://localhost:5001/api/recommendations -H "Content-Type: application/json" -d '{"player_a":{"submission_id":"YOUR_ID"},"player_b":{"submission_id":"OTHER_ID"},"session":{"rating":"R","target_activities":5}}' | jq

# Test compatibility
curl -X POST http://localhost:5001/api/compatibility -H "Content-Type: application/json" -d '{"submission_id_a":"YOUR_ID","submission_id_b":"OTHER_ID"}' | jq

# Run all backend tests
python scripts/test_picker.py && python scripts/test_validator.py && python scripts/test_compatibility.py
```

---

## Next Steps

Once backend testing looks good:
1. ✅ Backend is working
2. Import your activity spreadsheet
3. Test with real data
4. I'll have the frontend ready to wire up!

Let me know if you hit any issues or if the tests work smoothly! 🚀

