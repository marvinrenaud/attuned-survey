# Attuned - Intimacy Profile Survey

A comprehensive web application for discovering intimacy profiles through a scientifically-grounded survey. Built with React and Flask.

**Version**: v0.4 Survey | v0.6 Compatibility | v2.0 Activity Bank  
**Status**: ✅ Production Ready (compatibility fixes complete)  
**Last Updated**: November 12, 2025

![Attuned Logo](frontend/public/AttunedLogo.png)

## Overview

Attuned helps users understand their unique intimacy profile through a streamlined **54-question survey** covering:
- **Arousal Propensity** (Sexual Excitation/Inhibition - SES/SIS model)
- **Power Dynamics** (Top/Bottom/Switch/Versatile orientation)
- **Activity Preferences** (Physical, oral, anal, power exchange, verbal, display)
- **Truth Topics** (Communication and conversation comfort)
- **Boundaries** (Hard limits and safety preferences)

Results include:
- **Arousal Profile** (SE, SIS-P, SIS-C scores with interpretations)
- **Power Orientation** (Top/Bottom/Switch with confidence level)
- **Five Domain Scores** (Sensation, Connection, Power, Exploration, Verbal)
- **Advanced Compatibility Matching** (Asymmetric algorithm for all power dynamics)

## Recent Updates (v0.6 - November 2025)

**Compatibility Algorithm Improvements:**
- ✅ Fixed display activity matching (stripping, posing, dancing now recognized as complementary)
- ✅ Fixed protocols naming consistency (protocols_follow → protocols_receive)
- ✅ Split commands/begging into directional pairs (_give/_receive) for clarity
- ✅ Improved Top/Bottom matching accuracy: +6-30 percentage points
- ✅ Backend Python calculator now fully matches frontend JavaScript algorithm
- ✅ Activity recommendations properly score complementary pairs

**Validation:** Tested with real users showing score improvement from 64% to 94%.

See [COMPATIBILITY_ALGORITHM_FIX_SUMMARY.md](COMPATIBILITY_ALGORITHM_FIX_SUMMARY.md) for complete details.

## Features

- ✅ **54-question survey** (streamlined from 71) across 3 sections
- ✅ **Anatomy-based filtering** (Penis, Vagina, Breasts preferences)
- ✅ **Arousal profiling** (SES/SIS Dual Control Model)
- ✅ **Explicit power dynamics** (Top/Bottom/Switch determination with D/s vs S/M)
- ✅ **8-key boundary taxonomy** (Impact, Restraints, Breath, Degradation, Public, Recording, Anal, Watersports)
- ✅ **850 AI-enriched activities** (100% coverage with Groq)
- ✅ **Audience scope filtering** (Couples/Groups/All)
- ✅ **Directional preference matching** (Give/Receive pairs)
- ✅ **Real-time validation** and progress tracking
- ✅ **Session persistence** (resume incomplete surveys)
- ✅ **Domain-based results** (5 key dimensions + power orientation)
- ✅ **Advanced compatibility** (asymmetric matching for all power dynamics)
- ✅ **Activity versioning** (Active/archived with source tracking)
- ✅ **Admin panel** for viewing submissions and managing baselines
- ✅ **Test suite** for algorithm validation
- ✅ **Data export** (CSV and JSON formats)
- ✅ **Responsive design** (mobile, tablet, desktop)
- ✅ **Robust error handling** (15s timeouts, retry buttons)

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
- **Supabase PostgreSQL** - Database
- **Render.com** - Hosting
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

### v0.5 (October 15, 2025) - Compatibility Algorithm Fix
- ✅ **Same-pole incompatibility recognition** (Top/Top, Bottom/Bottom)
- ✅ Fixed false positive high scores for incompatible pairs
- ✅ Optimized weights (Power 20%, Activity 45%, Domain 25%, Truth 10%)
- ✅ Domain & truth penalties for same-pole pairs (0.5× multiplier)
- ✅ Updated test suite with all pair types
- **Impact**: Same-pole pairs now score 38-41% (was 75%)

### v0.4 (October 14, 2025) - Survey Refactor & Asymmetric Matching
- ✅ **Survey streamlined** (71 → 54 questions, 25% shorter)
- ✅ **Explicit power dynamics section** (A13-A16)
- ✅ **Asymmetric directional Jaccard** for Top/Bottom pairs
- ✅ **Complementary-aware domain similarity**
- ✅ **New profile structure** (arousal, power, domains, activities, truth, boundaries)
- ✅ **Results redesigned** (domain-based, removed archetypes)
- ✅ **Question clarifications** (8 questions improved)
- ✅ **Power visualizer fix** (Top displays correctly)
- ✅ **Boundary mapping fix** (begging ≠ degradation)
- **Impact**: Top/Bottom pairs now score 89% (was 60%)

### v0.3.1 (October 11, 2025)
- Removed ipsative questions (IA1–IA4)
- Domain-first matching approach

### v1.0.0 (October 10, 2025)
- ✅ Initial production release
- ✅ Full survey implementation
- ✅ API-based data persistence
- ✅ Admin panel
- ✅ Supabase integration

### Current Status
- ✅ Production deployed and stable
- ✅ All tests passing
- ✅ Real user data validated
- ✅ Error handling robust (15s timeouts, retry buttons)

### Roadmap
- [ ] Activity recommendations based on profiles
- [ ] Partner coordination features
- [ ] Profile evolution tracking
- [ ] Educational content
- [ ] Mobile app
- [ ] Multi-language support

