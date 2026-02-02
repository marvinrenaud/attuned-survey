---
name: attuned-activity-bank
description: Managing the activity bank - creating, editing, importing, validating activities. Use when working with activity data, the enriched_activities JSON files, import scripts, or activity validation. Covers activity schema and taxonomy.
---

# Attuned Activity Bank Skill

## Activity Data Files

```
backend/
├── enriched_activities_v2.json      # Current production bank (474KB)
├── enriched_activities_v2.json.backup
└── scripts/
    ├── import_activities.py         # XLSX → DB import (23KB)
    ├── enrich_activities.py         # Add AI metadata (14KB)
    ├── validate_activities.py       # Schema validation
    └── enriched_activities.json     # Script output
```

Source spreadsheet: `Consolidated_ToD_Activities (20).xlsx`

## Activity Schema

```python
{
    "id": "spanking_give_001",           # Unique ID
    "activity_key": "spanking_give",      # Taxonomy key
    "type": "dare",                       # "truth" or "dare"
    "title": "Light Spanking",            # Display title
    "description": "Give your partner...", # 2-3 sentences
    "intensity_level": 3,                 # 1-5 scale
    "rating": "R",                        # PG-13, R, NC-17
    "requires_anatomy": [""],             # or ["penis"], ["vagina"], etc.
    "tags": ["sensation", "power"],       # Domain tags
    "give_receive": "give",               # "give", "receive", "mutual", null
    "truth_topics": [],                   # Sensitive topic tags (truth only)
    "created_at": "2025-01-01T00:00:00Z"
}
```

### Truth Topics (truth activities only)

Truth activities can be tagged with 0-3 sensitive topic categories from survey questions B29-B36:

```python
ALLOWED_TRUTH_TOPICS = [
    'past_experiences',    # Sexual history, "Have you ever..."
    'fantasies',           # Fantasy description, "What's your fantasy..."
    'turn_ons',            # What arouses, "What turns you on?"
    'turn_offs',           # What doesn't work, "What turns you off?"
    'insecurities',        # Vulnerabilities
    'boundaries',          # Limits and consent
    'future_fantasies',    # Future desires
    'feeling_desired',     # Being wanted
]
```

- **Empty array:** Activity bypasses truth topic filtering (normal scoring)
- **Tagged:** Filtered/ranked based on user survey responses (NO=block, MAYBE=lower rank, YES=higher rank)

## Activity Key Taxonomy

```
{activity}_give      # Active/performing role (spanking_give)
{activity}_receive   # Passive/receiving role (spanking_receive)
{activity}_self      # Self-display (dancing_self, stripping_self)
{activity}_watching  # Watching partner (watching_strip)
{activity}_mutual    # Both participate equally
```

## Import Workflow

```bash
# 1. Prepare XLSX with columns: id, type, title, description, intensity, rating, anatomy, tags

# 2. Run import script
cd backend
python scripts/import_activities.py --input ../Consolidated_ToD_Activities.xlsx --output enriched_activities_v2.json

# 3. Validate
python scripts/validate_activities.py enriched_activities_v2.json

# 4. Backup existing
cp enriched_activities_v2.json enriched_activities_v2.json.backup

# 5. Deploy (activities loaded at app startup)
```

## Validation Rules

```python
REQUIRED_FIELDS = ['id', 'activity_key', 'type', 'title', 'description', 'intensity_level', 'rating']
VALID_TYPES = ['truth', 'dare']
VALID_RATINGS = ['PG-13', 'R', 'NC-17']
VALID_ANATOMY = ['penis', 'vagina', 'breasts', '']
INTENSITY_RANGE = (1, 5)

def validate_activity(activity):
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in activity:
            errors.append(f"Missing {field}")
    if activity.get('type') not in VALID_TYPES:
        errors.append(f"Invalid type: {activity.get('type')}")
    # ... more validations
    return errors
```

## Editing Activities

### Single Activity Edit
```python
# Load bank
with open('enriched_activities_v2.json') as f:
    activities = json.load(f)

# Find and modify
for act in activities:
    if act['id'] == 'target_id':
        act['description'] = 'New description'
        break

# Save
with open('enriched_activities_v2.json', 'w') as f:
    json.dump(activities, f, indent=2)
```

### Bulk Updates
Use `scripts/fix_activity_typos.py` pattern:
```python
FIXES = {
    'old_typo': 'correct_word',
    'another_typo': 'fixed',
}

for activity in activities:
    for old, new in FIXES.items():
        activity['description'] = activity['description'].replace(old, new)
```

## Database Integration

Activities are loaded into the `activities` table at startup:
```sql
CREATE TABLE activities (
    id UUID PRIMARY KEY,
    activity_key VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    intensity_level INTEGER,
    rating VARCHAR,
    requires_anatomy JSONB,
    tags JSONB,
    truth_topics JSONB DEFAULT '[]'::jsonb,  -- Migration 029
    created_at TIMESTAMP DEFAULT NOW()
);

-- GIN index for truth_topics array queries
CREATE INDEX idx_activities_truth_topics ON activities USING GIN (truth_topics);
```

## Common Tasks

### Add New Activity Category
1. Define activity_key naming (e.g., `newactivity_give`, `newactivity_receive`)
2. Add entries to XLSX or JSON
3. Update `HARD_LIMIT_MAP` in compatibility/calculator.py if needed
4. Run validation and import

### Fix Typos
1. Identify affected activities by ID
2. Create fix script or edit JSON directly
3. Backup, validate, deploy

### Rebalance Intensity Levels
1. Export current distribution: `SELECT intensity_level, COUNT(*) FROM activities GROUP BY 1`
2. Adjust levels to ensure good distribution across 1-5
3. Re-import

### Batch Tag Truth Topics
Use AI-powered tagging to classify truth activities:
```bash
cd backend

# Preview tagging (no database changes)
python scripts/tag_truth_topics.py --dry-run

# Apply tags to database
python scripts/tag_truth_topics.py --apply

# Re-tag all activities (overwrite existing)
python scripts/tag_truth_topics.py --apply --retag

# Limit processing (for testing)
python scripts/tag_truth_topics.py --apply --limit 10
```

The script uses `src/llm/activity_analyzer.py` to classify each truth activity into 0-3 topic categories.
