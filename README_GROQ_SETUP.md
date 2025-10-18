# Groq Recommender Setup & User Guide

## Overview

This guide explains how to set up and use the new AI-powered activity recommendation system powered by Groq (Llama 3.3).

## Features

### 🤖 AI-Powered Recommendations
- Generate personalized activity sessions using Groq Llama 3.3
- **820 curated activities** with AI-extracted tags
- **Preference-based ranking** - prioritizes mutual interests
- **Power dynamic filtering** - respects Top/Bottom/Switch orientations
- Intelligent truth/dare balancing
- Rating-based intensity progression (G=gentle, R=sensual, X=explicit)
- Respect hard boundaries and preferences
- Deduplication ensures variety (no repeated activities)

### 💾 Complete Database Persistence
- All profiles stored in PostgreSQL
- Session history and activities
- Compatibility results cached
- Activity bank management

### 🎮 Interactive Gameplay
- Step-by-step activity display
- Progress tracking
- Seamless navigation
- Beautiful UI with type/intensity indicators

---

## Quick Setup (5 Minutes)

### 1. Environment Configuration

```bash
cd /Users/mr/Documents/attuned-survey

# Interactive setup (easiest)
./setup_env.sh

# OR manually create .env with:
# DATABASE_URL=your_supabase_connection_string
# GROQ_API_KEY=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
```

### 2. Install Backend Dependencies

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start Backend

```bash
# From project root
./start_backend.sh
```

Expected output:
```
✅ Environment ready!
✅ Database connection successful
✅ Verified survey_submissions columns
* Running on http://127.0.0.1:5001
```

### 4. Start Frontend

```bash
cd frontend
pnpm dev
```

Expected output:
```
VITE ready in XXX ms
➜  Local:   http://localhost:5174/
```

### 5. Test Everything

```bash
# In a new terminal
./backend/scripts/test_api_endpoints.sh
```

Expected: All endpoints pass ✅

---

## User Flow

### For End Users

1. **Complete Survey**
   - Go to http://localhost:5174/survey
   - Answer all questions
   - Submit

2. **View Results**
   - See your personality profile
   - If baseline is set, see compatibility score

3. **Start Game** (New!)
   - Click "Start Game" button
   - System generates 25 personalized activities
   - Navigate step-by-step through the session

### For Admins

1. **Test Recommendations**
   - Go to http://localhost:5174/admin
   - Click "Recommendations" tab
   - Select 2 players
   - Configure rating and activity type
   - Generate and download results

2. **Manage Baseline**
   - Go to "Responses" tab
   - Click "Set" next to any submission
   - This becomes the comparison partner for all new surveys

---

## Activity Import & AI Enrichment

### Prepare Your CSV

Required columns:
- **Activity Type**: Truth or Dare
- **Activity Description**: The activity text
- **Audience Tag**: Couple or Group
- **Intimacy Level**: L1 through L9
- **Intimacy Rating**: G, R, or X

Example row:
```
Truth,Share your favorite memory from this year,L1,G,Couple
Dare,Kiss your partner passionately for 10 seconds,L5,R,Couple
```

### Step 1: AI Enrichment (Recommended)

Use Groq to analyze activities and extract metadata for personalization:

```bash
cd backend
source venv/bin/activate

# Enrich first 100 activities (test quality)
python scripts/enrich_activities.py \
  "../docs/your-activities.csv" \
  --limit 100 \
  --show-samples

# If quality looks good, enrich all activities
python scripts/enrich_activities.py \
  "../docs/your-activities.csv" \
  --show-samples
```

**This extracts:**
- **Power roles** (top/bottom/switch/neutral) - for power dynamic filtering
- **Preference keys** (massage, oral, bondage, etc.) - for preference matching
- **Domains** (sensual, playful, power, connection) - for categorization
- **Intensity modifiers** (gentle, intense, edgy, taboo) - for fine-tuning

**Output:** `enriched_activities.json` with AI-generated tags

### Step 2: Import to Database

```bash
# Import with AI tags (auto-detects enriched_activities.json)
python scripts/import_activities.py \
  /path/to/your/activities.csv \
  --clear
```

The `--clear` flag removes existing bank activities before import.

**Import shows:**
- Total imported
- How many have AI tags
- Power role distribution (Top/Bottom/Switch/Neutral)

### Verify Import

```bash
python -c "
from src.main import app
from src.models.activity import Activity
with app.app_context():
    count = Activity.query.count()
    print(f'Total activities: {count}')
    
    # Check AI enrichment
    enriched = Activity.query.filter(Activity.power_role.isnot(None)).count()
    print(f'With AI tags: {enriched}')
    
    # Power role distribution
    for role in ['top', 'bottom', 'switch', 'neutral']:
        c = Activity.query.filter_by(power_role=role).count()
        if c > 0:
            print(f'{role.capitalize()}: {c}')
"
```

---

## Configuration Options

### Environment Variables

```env
# Required
DATABASE_URL=postgresql://...
GROQ_API_KEY=gsk_xxx...

# Optional (with defaults)
GROQ_MODEL=llama-3.3-70b-versatile
ATTUNED_DEFAULT_TARGET_ACTIVITIES=25
ATTUNED_DEFAULT_BANK_RATIO=0.5
ATTUNED_DEFAULT_RATING=R
REPAIR_USE_AI=true
GEN_TEMPERATURE=0.6
```

### Session Configuration (via API)

When generating recommendations, you can configure:

```json
{
  "rating": "G|R|X",           // Content rating
  "target_activities": 25,      // Number of activities (1-50)
  "activity_type": "random",    // random, truth, dare
  "bank_ratio": 0.5,           // 0-1: ratio of bank vs AI activities
  "rules": {
    "avoid_maybe_until": 6      // Don't suggest uncertain items before step N
  }
}
```

---

## Advanced Features

### Activity Personalization System

**How It Works:**

The system uses AI-powered preference-based ranking to select activities:

1. **AI Tagging**: Groq analyzes each activity description to extract:
   - Power role (top/bottom/switch/neutral)
   - Preference keys (massage, oral, bondage, etc.)
   - Domain tags (sensual, playful, power, connection)
   - Intensity modifiers

2. **Intelligent Ranking**: Activities are scored based on:
   - **Mutual Interest (50%)**: Both players want this activity
   - **Power Alignment (30%)**: Matches player power dynamics
   - **Domain Fit (20%)**: Matches domain preferences

3. **Smart Selection**:
   - Filters out power mismatches (Top activities for Bottom-only players)
   - Ranks candidates by composite score
   - Selects best-matching activity
   - Tracks used IDs to prevent duplicates

4. **Rating-Based Progression**:
   - **G-rated**: Intensity 1 throughout (gentle, playful)
   - **R-rated**: Intensity 2-3 (sensual, intimate)
   - **X-rated**: Intensity 4-5 (explicit, starts at L4)

### Enabling Full Groq AI Generation

Currently, the system uses curated bank activities with fallback templates. To enable full AI generation:

1. Ensure `GROQ_API_KEY` is set correctly
2. In `backend/src/routes/recommendations.py`, uncomment Groq generation logic
3. AI will generate activities when bank pool is exhausted

### Custom Activity Templates

You can add custom activities directly to the database:

```python
from src.main import app, db
from src.models.activity import Activity

with app.app_context():
    activity = Activity(
        type='truth',
        rating='R',
        intensity=3,
        script={
            'steps': [
                {'actor': 'A', 'do': 'Your custom activity description'}
            ]
        },
        tags=['custom', 'couple'],
        source='user_submitted',
        approved=True
    )
    db.session.add(activity)
    db.session.commit()
```

### Batch Generation

For testing or pre-generating sessions:

```bash
curl -X POST http://localhost:5001/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "player_a": {"submission_id": "YOUR_ID"},
    "player_b": {"submission_id": "OTHER_ID"},
    "session": {
      "rating": "R",
      "target_activities": 25,
      "activity_type": "random"
    }
  }' | jq '.session_id'
```

Save the session_id and use it later in the Gameplay page.

---

## Monitoring & Debugging

### Check Database Tables

In Supabase Studio, verify these tables exist:
- `profiles` - Player profiles from surveys
- `sessions` - Game sessions
- `activities` - Activity bank
- `session_activities` - Generated activities
- `compatibility_results` - Cached compatibility scores

### View Backend Logs

The Flask console shows structured logs:

```
[INFO] Starting recommendations generation request_id=xxx rating=R target_activities=25
[INFO] Saved 25 activities for session abc-123
[INFO] Recommendations generated successfully session_id=abc-123 elapsed_ms=1850
```

### Performance Metrics

Current performance (with fallback templates):
- **5 activities**: ~300-500ms
- **25 activities**: ~1.5-2s
- **Compatibility**: ~200-400ms

With Groq AI enabled (future):
- **5 activities**: ~1-2s
- **25 activities**: ~3-5s

---

## Files Changed

### Backend (New)
- `backend/src/config.py` - Environment configuration
- `backend/src/models/profile.py` - Profile model
- `backend/src/models/session.py` - Session model
- `backend/src/models/activity.py` - Activity bank model
- `backend/src/models/session_activity.py` - Generated activities
- `backend/src/models/compatibility.py` - Compatibility results
- `backend/src/recommender/` - Core recommendation logic (4 files)
- `backend/src/llm/` - Groq integration (3 files)
- `backend/src/db/repository.py` - Data access layer
- `backend/src/compatibility/calculator.py` - Compatibility algorithm
- `backend/src/routes/recommendations.py` - API routes

### Backend (Modified)
- `backend/requirements.txt` - Added groq, jsonschema
- `backend/src/main.py` - Register new models and routes

### Frontend (New)
- `frontend/src/pages/Gameplay.jsx` - Complete gameplay experience

### Frontend (Modified)
- `frontend/src/lib/storage/apiStore.js` - Added 4 new API methods
- `frontend/src/pages/Admin.jsx` - Added Recommendations panel
- `frontend/src/pages/Result.jsx` - Added "Start Game" button
- `frontend/src/App.jsx` - Added /gameplay route

### Documentation (New)
- `BACKEND_TESTING_GUIDE.md`
- `FRONTEND_INTEGRATION_GUIDE.md`
- `README_GROQ_SETUP.md` (this file)
- `.env.example`

### Scripts (New)
- `setup_env.sh` - Interactive environment setup
- `start_backend.sh` - Backend startup with validation
- `backend/scripts/test_api_endpoints.sh` - Automated API testing
- `backend/scripts/import_activities.py` - CSV import tool
- `backend/scripts/test_*.py` - 4 backend test suites

---

## Support

**Backend Issues**: Check `BACKEND_TESTING_GUIDE.md`
**Frontend Issues**: Check `FRONTEND_INTEGRATION_GUIDE.md`
**General Setup**: This file

Questions? Check the console logs first - they're very detailed!

---

**You're all set! Enjoy testing the new recommendation system! 🎉**

