# Attuned Survey - Backend

Flask API server for the Attuned intimacy profile survey.

**Version:** v0.6 (Compatibility Algorithm)  
**Last Updated:** November 12, 2025

## Tech Stack

- **Flask 3.1** - Web framework
- **Python 3.11** - Runtime
- **SQLAlchemy** - ORM
- **PostgreSQL** (Supabase) - Database
- **Flask-CORS** - Cross-origin support
- **Groq AI** - Activity generation and enrichment

## Project Structure

```
src/
├── main.py              # Flask application entry point
├── extensions.py        # Flask extensions (db, cors)
├── config.py            # Configuration
├── models/              # Database models
│   ├── profile.py       # User profiles
│   ├── activity.py      # Activity bank
│   ├── session.py       # Game sessions
│   └── ...
├── routes/              # API endpoints
│   ├── survey.py        # Survey submissions
│   ├── user.py          # User/profile management
│   └── recommendations.py  # Activity recommendations
├── compatibility/       # Compatibility algorithm
│   └── calculator.py    # v0.6 asymmetric matching
├── recommender/         # Activity recommendation engine
│   ├── scoring.py       # Preference-based scoring
│   ├── picker.py        # Activity selection
│   └── ...
├── llm/                 # AI integration
│   ├── generator.py     # Groq activity generation
│   └── activity_analyzer.py  # Activity enrichment
└── db/                  # Database access
    └── repository.py    # Query helpers
```

## Development

### Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Development Server
```bash
python src/main.py
```
Runs on http://localhost:5000

## API Endpoints

### Submissions

**GET /api/survey/submissions**
```json
{
  "submissions": [...],
  "baseline": "submission_id"
}
```

**POST /api/survey/submissions**
```json
{
  "id": "unique_id",
  "name": "User Name",
  "answers": { ... },
  "derived": { ... },
  "createdAt": "2025-10-10T12:00:00Z"
}
```

**GET /api/survey/submissions/:id**
```json
{
  "id": "submission_id",
  "name": "User Name",
  ...
}
```

### Baseline

**GET /api/survey/baseline**
```json
{
  "baseline": "submission_id"
}
```

**POST /api/survey/baseline**
```json
{
  "id": "submission_id"
}
```

**DELETE /api/survey/baseline**
```json
{
  "baseline": null
}
```

### Export

**GET /api/survey/export**
```json
{
  "exportedAt": "2025-10-10T12:00:00Z",
  "baseline": "submission_id",
  "submissions": [...]
}
```

## Data Storage

### JSON Files

**submissions.json**
```json
[
  {
    "id": "1760111369900-k3j2h9x",
    "name": "User Name",
    "createdAt": "2025-10-10T12:00:00Z",
    "answers": {
      "A1": 5,
      "A2": 6,
      ...
    },
    "derived": {
      "traits": { ... },
      "dials": { ... },
      "archetypes": [ ... ],
      "boundaryFlags": { ... },
      "warnings": []
    }
  }
]
```

**baseline.json**
```json
"1760111369900-k3j2h9x"
```

### File Operations

**Load submissions:**
```python
def load_submissions():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)
```

**Save submissions:**
```python
def save_submissions(submissions):
    with open(DATA_FILE, 'w') as f:
        json.dump(submissions, f, indent=2)
```

## Configuration

### Admin Password

Edit `src/routes/survey.py`:
```python
ADMIN_PASSWORD = 'your_secure_password'
```

### CORS Settings

Edit `src/main.py`:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "https://your-domain.com"]
    }
})
```

### Port

Edit `src/main.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## Compatibility Calculation (v0.6)

The backend includes a sophisticated compatibility algorithm:

**Components:**
- **Power Complement** (20% weight) - Top/Bottom pairing
- **Domain Similarity** (25% weight) - Interest alignment
- **Activity Overlap** (45% weight) - Mutual activities
- **Truth Overlap** (10% weight) - Communication comfort

**Algorithm Types:**
- **Asymmetric Directional Jaccard** - For Top/Bottom pairs (recognizes complementary _give/_receive and _self/_watching pairs)
- **Same-Pole Jaccard** - For Top/Top or Bottom/Bottom pairs (penalizes incompatible role preferences)
- **Standard Jaccard** - For Switch/Switch or mixed pairs

See `src/compatibility/calculator.py` for implementation.

## Activity Recommendations

AI-powered activity recommendations using Groq:

**Scoring Components:**
- **Mutual Interest** (50%) - Matches player preferences
- **Power Alignment** (30%) - Fits power dynamics
- **Domain Fit** (20%) - Aligns with domains

**Features:**
- Anatomy-based filtering
- Boundary-aware selection
- Intensity progression (warmup → peak → afterglow)
- Bank-first with AI fallback

See `src/recommender/scoring.py` and `src/llm/generator.py`.

## Error Handling

All endpoints return proper HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

Error response format:
```json
{
  "error": "Error message"
}
```

## Testing

### Manual Testing
```bash
# Get all submissions
curl http://localhost:5000/api/survey/submissions

# Create submission
curl -X POST http://localhost:5000/api/survey/submissions \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","answers":{},"derived":{}}'

# Set baseline
curl -X POST http://localhost:5000/api/survey/baseline \
  -H "Content-Type: application/json" \
  -d '{"id":"submission_id"}'
```

### Automated Testing
```bash
python -m pytest tests/
```

## Deployment

### Production Server

Use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

### Environment Variables

Create `.env` file:
```
FLASK_ENV=production
ADMIN_PASSWORD=secure_password
DATABASE_PATH=/path/to/database
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]
```

### Heroku

```bash
# Create Procfile
echo "web: gunicorn src.main:app" > Procfile

# Deploy
heroku create
git push heroku main
```

## Database Migration

For production, migrate from JSON to a proper database:

### PostgreSQL
```python
import psycopg2
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/attuned'
db = SQLAlchemy(app)
```

### MongoDB
```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['attuned']
submissions = db['submissions']
```

## Security

### Current Limitations
- ⚠️ Admin password hardcoded
- ⚠️ No user authentication
- ⚠️ No data encryption
- ⚠️ JSON file storage (not scalable)

### Recommendations
- Use environment variables for secrets
- Implement JWT authentication
- Encrypt sensitive data
- Use proper database with transactions
- Add rate limiting
- Enable HTTPS only

## Monitoring

### Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/survey/submissions', methods=['POST'])
def create_submission():
    logger.info(f"New submission from {request.remote_addr}")
    # ...
```

### Health Check
```python
@app.route('/health')
def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

## Troubleshooting

### Port Already in Use
```bash
# Find process
lsof -ti:5000

# Kill process
kill -9 $(lsof -ti:5000)
```

### CORS Errors
Check CORS configuration in `src/main.py` includes frontend URL.

### File Permission Errors
```bash
# Fix permissions
chmod 644 src/database/*.json
```

## License

Proprietary. All rights reserved.

