# Attuned Survey - Deployment Guide

**Version**: v0.4 Survey | v0.5 Compatibility  
**Status**: ✅ Production Deployed  
**Last Updated**: October 15, 2025

---

## Quick Start

### Current Production Deployment

The application is **live and fully functional** with:
- ✅ v0.4 survey (54 questions)
- ✅ v0.5 compatibility algorithm (asymmetric matching)
- ✅ Supabase PostgreSQL database
- ✅ Render.com backend hosting
- ✅ All tests passing

---

## System Requirements

### Frontend
- **Node.js** 22+
- **pnpm** 10+ (package manager)
- **Modern browser** (Chrome, Firefox, Safari, Edge)

### Backend
- **Python** 3.11+
- **PostgreSQL** 13+ (via Supabase)
- **pip** package manager

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/marvinrenaud/attuned-survey.git
cd attuned-survey
```

### 2. Frontend Setup

```bash
cd frontend
pnpm install
pnpm run dev
```

Frontend runs on: `http://localhost:5173` (or auto-incremented port)

### 3. Backend Setup (Optional - Uses Remote Supabase)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run_backend.py
```

Backend runs on: `http://localhost:5001`

**Note**: By default, frontend connects to remote production backend (`attuned-backend.onrender.com`). To use local backend, create `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:5001
```

---

## Production Deployment

### Current Stack

**Frontend**: React SPA
- Build tool: Vite
- Output: Static files in `dist/`
- Hosting: Can deploy to Vercel, Netlify, or serve via Flask

**Backend**: Flask API
- Hosting: Render.com
- Database: Supabase PostgreSQL
- Auto-deploy: GitHub integration

### Frontend Deployment

#### Option 1: Vercel (Recommended for Frontend-Only)

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel deploy --prod
```

Configuration (`vercel.json`):
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
  "env": {
    "VITE_API_URL": "https://attuned-backend.onrender.com"
  }
}
```

#### Option 2: Netlify

```bash
cd frontend
pnpm run build

# Deploy via Netlify CLI or drag-drop dist/ folder
netlify deploy --prod --dir=dist
```

#### Option 3: Serve via Flask Backend

```bash
cd frontend
pnpm run build

# Copy build to backend static folder
cp -r dist/* ../backend/src/static/
```

Then deploy Flask as normal.

### Backend Deployment

#### Current: Render.com (Auto-Deploy)

**Setup**:
1. Connected to GitHub repository
2. Auto-deploys on push to `main` branch
3. Environment variables configured in Render dashboard

**Environment Variables (Render.com)**:
```bash
DATABASE_URL=postgresql://user:pass@host/db  # Supabase connection
FLASK_ENV=production
SECRET_KEY=your_secret_key
PORT=5001
```

**Build Command**: `pip install -r requirements.txt`  
**Start Command**: `gunicorn src.main:app`

#### Alternative: Heroku

```bash
cd backend

# Create Heroku app
heroku create attuned-backend

# Add PostgreSQL (or use Supabase)
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main
```

---

## Database Setup

### Supabase Configuration

**Current Setup**:
- **Project**: Attuned Survey
- **Region**: US East
- **Plan**: Free tier (sufficient for MVP)

**Tables**:
1. `survey_submissions` - All survey responses and calculated profiles
2. `survey_baseline` - Currently selected baseline for compatibility

**Migrations**: Auto-handled by SQLAlchemy in Flask

**Connection String**:
```
postgresql://[user]:[password]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

### Backup Strategy

**Automated** (Supabase):
- Daily backups (free tier: 7 days retention)
- Point-in-time recovery available on paid tiers

**Manual Export**:
```bash
# Via admin panel
# Navigate to /admin/export
# Click "Download JSON" or "Download CSV"
```

---

## Configuration

### Frontend Configuration

**API Base URL** (`frontend/src/lib/storage/apiStore.js`):
```javascript
const DEFAULT_API =
  (typeof window !== 'undefined' && window.location.hostname === 'localhost')
    ? 'http://localhost:5001'  // Local development
    : 'https://attuned-backend.onrender.com';  // Production

const API_BASE = `${(import.meta.env?.VITE_API_URL || DEFAULT_API)}/api/survey`;
```

**Timeouts**:
```javascript
// All API calls have 15-second timeout
const timeoutId = setTimeout(() => controller.abort(), 15000);
```

**Admin Password** (Frontend - Not Secure):
```javascript
// frontend/src/pages/Admin.jsx
const ADMIN_PASSWORD = '1111';  // Change for production
```

### Backend Configuration

**Flask Settings** (`backend/src/main.py`):
```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Database connection via environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
```

**CORS Configuration**:
```python
# Allows frontend on any origin (development)
# For production, specify exact origin:
CORS(app, origins=['https://your-frontend-domain.com'])
```

---

## Testing

### Automated Tests

**Frontend Tests**:
```bash
cd frontend

# Run compatibility algorithm tests
# Navigate to: http://localhost:5173/test-compatibility
# Click test buttons and check console
```

**Expected Results**:
- Top/Bottom: 89% ✅
- Top/Top: 38% ✅
- Bottom/Bottom: 41% ✅

### Manual Testing

**Complete Survey Flow**:
1. Navigate to `/survey`
2. Enter name, sex, orientation
3. Complete all 54 questions
4. Submit and view results
5. Verify all sections display correctly

**Compatibility Testing**:
1. Complete survey as Top user
2. Go to `/admin`, set as baseline
3. Complete survey as Bottom user
4. View results - should show ~89% compatibility

**Error Handling**:
1. Simulate slow backend (network throttling)
2. Verify timeout triggers after 15s
3. Verify retry buttons appear
4. Verify helpful error messages

---

## Monitoring

### Health Checks

**Backend**:
```bash
# Health check endpoint
curl https://attuned-backend.onrender.com/api/survey/submissions
# Should return 200 OK with submissions
```

**Frontend**:
```bash
# Check if site loads
curl https://your-frontend-url.com
# Should return 200 OK with HTML
```

### Logs

**Render.com Backend Logs**:
- Dashboard → Your Service → Logs
- Shows: API requests, errors, database queries

**Supabase Database Logs**:
- Dashboard → Database → Logs
- Shows: Queries, connection issues, slow queries

**Frontend Console**:
- Browser DevTools → Console
- Shows: Calculation breakdowns, API calls, errors

### Performance Metrics

**Expected**:
- Page load: <2s
- Survey submit: <1s
- Results calculation: <100ms
- Compatibility calculation: <50ms
- API timeout: 15s max

---

## Scaling Considerations

### Current Limits (Free Tier)

**Supabase**:
- Database: 500 MB
- API requests: Unlimited (with rate limits)
- Bandwidth: 5 GB/month

**Render.com**:
- Free tier: Sleeps after 15 min inactivity
- Wakes on request (~30s delay)
- 750 hours/month free

### When to Upgrade

**Supabase Pro** (Consider when):
- >500 MB database size
- >5 GB bandwidth/month
- Need point-in-time recovery

**Render.com Paid** (Consider when):
- Need always-on (no sleep)
- >750 hours usage/month
- Need faster performance

---

## Security Checklist

### Before Production (Future Improvements)

- [ ] Move admin password to backend authentication
- [ ] Implement JWT for user sessions
- [ ] Enable Supabase Row Level Security (RLS)
- [ ] Add rate limiting (prevent abuse)
- [ ] Validate all inputs on backend
- [ ] Enable HTTPS only
- [ ] Add Content Security Policy headers
- [ ] Implement backend validation of survey responses
- [ ] Encrypt sensitive data at rest
- [ ] Add audit logging

### Current Security Posture

✅ **Good**:
- HTTPS enforced
- CORS configured
- Database hosted (Supabase managed)
- No sensitive data in frontend code

⚠️ **Needs Improvement**:
- Admin password in frontend (not secure)
- No rate limiting
- No user authentication
- No data encryption beyond Supabase defaults

---

## Rollback Procedure

### If Issues Occur in Production

**Step 1: Identify Branch**
```bash
# Current production: fix-compatibility-algo branch
# Previous: feature/v0.3.1-2 or main
```

**Step 2: Rollback Frontend**
```bash
git checkout main  # or previous stable branch
cd frontend
pnpm install
pnpm run build
# Re-deploy build
```

**Step 3: Rollback Backend (Render.com)**
- Dashboard → Manual Deploy
- Select previous deployment
- Click "Redeploy"

**Step 4: Verify**
- Test survey completion
- Test results display
- Test compatibility matching

---

## Version Migration

### Upgrading from v0.3.1 to v0.4

**Database**: No migration needed
- v0.3.1 profiles remain in database
- v0.4 profiles stored alongside
- Admin panel handles both versions

**Frontend**: Deploy new code
- New profiles automatically use v0.4
- Old profiles viewable in admin (compatibility mode)
- Results page requires v0.4 (shows error for v0.3.1)

**Backward Compatibility**:
- Admin panel: ✅ Shows both v0.3.1 and v0.4
- Results page: ❌ v0.4 only (intentional)
- Compatibility: ✅ Works if both profiles same version

---

## Support & Maintenance

### Regular Maintenance

**Weekly**:
- Check Render.com logs for errors
- Monitor Supabase usage
- Review submission count growth

**Monthly**:
- Export data backup (via admin panel)
- Review performance metrics
- Check for security updates

**Quarterly**:
- Review and update dependencies
- Performance optimization review
- User feedback incorporation

### Contact & Resources

**Documentation**:
- Executive Summary: `/EXECUTIVE_SUMMARY.md`
- README: `/README.md`
- Technical Notes: `/docs/TECHNICAL_NOTES.md`
- This Guide: `/docs/DEPLOYMENT_GUIDE.md`

**Code Repository**:
- GitHub: https://github.com/marvinrenaud/attuned-survey
- Branch: `fix-compatibility-algo` (production)
- Main: `main` (stable releases)

---

## Success Checklist

After deployment, verify:

- [ ] Frontend loads correctly
- [ ] Can complete survey (all 54 questions)
- [ ] Results display with all sections
- [ ] Power visualizer shows correct position
- [ ] Admin panel loads submissions
- [ ] Can set baseline
- [ ] Compatibility displays when baseline set
- [ ] Test page works (`/test-compatibility`)
- [ ] All three pair types score correctly:
  - [ ] Top/Bottom: 85-95%
  - [ ] Top/Top: 35-45%
  - [ ] Bottom/Bottom: 35-45%
- [ ] Error handling works (retry buttons, timeouts)
- [ ] No console errors
- [ ] Mobile responsive
- [ ] Data persists in database

---

## Deployment Timeline

| Date | Version | Changes | Status |
|------|---------|---------|--------|
| Oct 10, 2025 | v1.0.0 | Initial release | ✅ Deployed |
| Oct 11, 2025 | v0.3.1 | Minor refinements | ✅ Deployed |
| Oct 14, 2025 | v0.4 | Survey refactor | ✅ Deployed |
| Oct 15, 2025 | v0.5 | Compatibility fix | ✅ Deployed |

**Current Production**: v0.4 Survey + v0.5 Compatibility

---

## Emergency Contacts

**Backend Issues (Render.com)**:
- Dashboard: https://dashboard.render.com
- Logs: Service → Logs tab
- Restart: Service → Manual Deploy

**Database Issues (Supabase)**:
- Dashboard: https://supabase.com/dashboard
- Connection: Check pooler status
- Backup: Download from admin panel

**Code Issues**:
- GitHub: https://github.com/marvinrenaud/attuned-survey
- Branch: `fix-compatibility-algo`
- Rollback: Deploy previous commit

---

**Deployment guide complete. System is production-ready and fully documented.**

*Made with ♥️ in BK*
