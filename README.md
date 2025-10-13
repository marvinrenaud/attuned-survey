# Attuned - Intimacy Profile Survey

A comprehensive web application for discovering intimacy profiles through a scientifically-grounded survey. Built with React and Flask.

![Attuned Logo](frontend/public/AttunedLogo.png)

## Overview

Attuned helps users understand their unique intimacy profile through a 92-question survey covering:
- **Arousal patterns** (Sexual Excitation/Inhibition)
- **Preferences** (Activities and dynamics)
- **Boundaries** (Limits and rules)
- **Role & Logistics** (Communication and planning)
 

Results include:
- **Intimacy Archetypes** (e.g., The Romantic, The Director, The Explorer)
- **Four Dimensions** (Adventure, Connection, Intensity, Confidence)
- **Compatibility Matching** (Compare with baseline profile)

## Features

- ✅ **92-question survey** across 5 chapters
- ✅ **Real-time validation** and progress tracking
- ✅ **Session persistence** (resume incomplete surveys)
- ✅ **Results visualization** with archetypes and dimension scores
- ✅ **Compatibility matching** with category-by-category breakdown
- ✅ **Admin panel** for viewing submissions and managing baselines
- ✅ **Data export** (CSV and JSON formats)
- ✅ **Responsive design** (mobile, tablet, desktop)
- ✅ **Accessibility** (WCAG 2.1 AA compliant)

## Tech Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **React Router v6** - Client-side routing
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Lucide React** - Icons

### Backend
- **Flask 3.1** - API server
- **Python 3.11** - Runtime
- **JSON files** - Data storage (for MVP)
- **Flask-CORS** - Cross-origin support

## Project Structure

```
attuned-survey/
├── frontend/              # React application
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Page components
│   │   ├── lib/          # Business logic
│   │   │   ├── scoring/  # Trait, dial, archetype calculators
│   │   │   ├── matching/ # Compatibility algorithm
│   │   │   └── storage/  # API client
│   │   └── data/         # Survey schema and questions
│   └── public/           # Static assets
├── backend/              # Flask API
│   ├── src/
│   │   ├── routes/       # API endpoints
│   │   └── database/     # JSON data files
│   └── requirements.txt  # Python dependencies
└── docs/                 # Documentation
```

## Getting Started

### Prerequisites

- **Node.js** 22+ and pnpm
- **Python** 3.11+
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/attuned-survey.git
   cd attuned-survey
   ```

2. **Install frontend dependencies**
   ```bash
   cd frontend
   pnpm install
   ```

3. **Install backend dependencies**
   ```bash
   cd ../backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Development

1. **Start the backend server**
   ```bash
   cd backend
   source venv/bin/activate
   python src/main.py
   ```
   Backend runs on http://localhost:5000

2. **Start the frontend dev server**
   ```bash
   cd frontend
   pnpm run dev
   ```
   Frontend runs on http://localhost:5173

3. **Open your browser**
   Navigate to http://localhost:5173

### Production Build

1. **Build the frontend**
   ```bash
   cd frontend
   pnpm run build
   ```
   Output: `frontend/dist/`

2. **Deploy with Flask**
   ```bash
   # Copy frontend build to Flask static directory
   cp -r frontend/dist/* backend/src/static/
   
   # Run Flask in production mode
   cd backend
   source venv/bin/activate
   python src/main.py
   ```

## Configuration

### Admin Password

Default admin password: `1111`

To change, edit `backend/src/routes/survey.py`:
```python
ADMIN_PASSWORD = 'your_secure_password'
```

### API Base URL

Frontend API calls default to `/api/survey` (same origin).

For different backend URL, edit `frontend/src/lib/storage/apiStore.js`:
```javascript
const API_BASE = 'https://your-backend-url.com/api/survey';
```

## Usage

### Taking the Survey

1. Visit the homepage
2. Click "Start Your Survey"
3. Enter your name
4. Answer questions across 5 chapters
5. View your results

### Admin Panel

1. Visit `/admin`
2. Enter password (default: `1111`)
3. View all submissions
4. Set baseline for compatibility matching
5. Export data as CSV or JSON

## API Documentation

### Endpoints

**GET /api/survey/submissions**
- Get all submissions and baseline ID
- Response: `{ submissions: [...], baseline: "id" }`

**POST /api/survey/submissions**
- Create new submission
- Body: Submission object
- Response: Saved submission with ID

**GET /api/survey/submissions/:id**
- Get specific submission
- Response: Submission object

**GET /api/survey/baseline**
- Get baseline submission ID
- Response: `{ baseline: "id" }`

**POST /api/survey/baseline**
- Set baseline submission
- Body: `{ id: "submission_id" }`
- Response: `{ baseline: "id" }`

**DELETE /api/survey/baseline**
- Clear baseline
- Response: `{ baseline: null }`

**GET /api/survey/export**
- Export all data
- Response: All submissions and baseline

## Testing

### Frontend Tests
```bash
cd frontend
pnpm run test
```

### Backend Tests
```bash
cd backend
python -m pytest
```

### Component Validation
```bash
node tests/test_components.js
```

### API Tests
```bash
python tests/test_backend_api.py
```

## Deployment

### Manus Platform (Current)

The application is deployed on Manus:
- **URL:** https://e5h6i7cvqlyx.manus.space
- **Deployment:** Automatic via Manus CLI

### Other Platforms

**Vercel (Frontend):**
```bash
cd frontend
vercel deploy
```

**Heroku (Backend):**
```bash
cd backend
heroku create
git push heroku main
```

**Docker:**
```bash
docker-compose up
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary. All rights reserved.

## Acknowledgments

- **IntimacAI** - Survey methodology and scoring system (v0.2.3)
- **shadcn/ui** - Beautiful component library
- **Tailwind CSS** - Utility-first CSS framework

## Support

For issues, questions, or feedback:
- Open an issue on GitHub
- Contact: [your-email@example.com]

## Changelog

### v0.3.1
- Ipsative (IA1–IA4) removed; domain scores + direction-aware matching make them unnecessary.

### v1.0.0 (October 10, 2025)
- ✅ Initial release
- ✅ Full survey implementation (92 questions)
- ✅ Scoring engine (traits, dials, archetypes)
- ✅ Compatibility matching algorithm
- ✅ Admin panel with data export
- ✅ Responsive design
- ✅ Data persistence fixes

### Known Issues
- JSON file storage (not scalable for production)
- No user authentication
- No data encryption
- Admin password hardcoded

### Roadmap
- [ ] Database migration (PostgreSQL)
- [ ] User authentication
- [ ] Data encryption
- [ ] Real-time updates
- [ ] Mobile app
- [ ] Multi-language support

