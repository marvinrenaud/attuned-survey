# Quick Start Guide

Get the Attuned Survey running in 5 minutes.

## Prerequisites

- **Node.js 22+** and pnpm
- **Python 3.11+**
- **Git**

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/attuned-survey.git
cd attuned-survey
```

### 2. Setup Frontend

```bash
cd frontend
pnpm install
```

### 3. Setup Backend

```bash
cd ../backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running Locally

### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate
python src/main.py
```

Backend runs on http://localhost:5000

### Terminal 2: Frontend

```bash
cd frontend
pnpm run dev
```

Frontend runs on http://localhost:5173

### Open Browser

Navigate to http://localhost:5173

## Testing the App

1. **Take Survey**
   - Click "Start Your Survey"
   - Enter your name
   - Answer questions across 5 chapters
   - View your results

2. **Admin Panel**
   - Visit http://localhost:5173/admin
   - Password: `1111`
   - View submissions
   - Set baseline
   - Export data

## Production Deployment

### Build Frontend

```bash
cd frontend
pnpm run build
```

### Copy to Backend

```bash
cp -r dist/* ../backend/src/static/
```

### Run Production Server

```bash
cd ../backend
source venv/bin/activate
python src/main.py
```

Visit http://localhost:5000

## Common Issues

### Port Already in Use

```bash
# Kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9

# Kill process on port 5000 (backend)
lsof -ti:5000 | xargs kill -9
```

### Module Not Found

```bash
# Frontend
cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### CORS Errors

Check backend `src/main.py` includes frontend URL in CORS config:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"]
    }
})
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [GITHUB_SETUP.md](GITHUB_SETUP.md) for GitHub instructions
- Review [docs/](docs/) for technical details

## Support

For issues or questions:
- Check documentation in `docs/`
- Open an issue on GitHub
- Contact: [your-email@example.com]

