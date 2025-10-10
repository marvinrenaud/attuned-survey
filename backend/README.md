# Attuned Survey - Backend

Flask API server for the Attuned intimacy profile survey.

## Tech Stack

- **Flask 3.1** - Web framework
- **Python 3.11** - Runtime
- **Flask-CORS** - Cross-origin support
- **JSON files** - Data storage (MVP)

## Project Structure

```
src/
├── main.py          # Flask application entry point
├── routes/          # API endpoints
│   └── survey.py    # Survey CRUD operations
└── database/        # Data storage
    ├── submissions.json  # All survey submissions
    └── baseline.json     # Baseline submission ID
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

