# Production Deployment Checklist

## 🚀 Ready to Deploy the Groq Recommender!

This guide will walk you through deploying the new features to production safely.

---

## Pre-Deployment Verification ✅

Before deploying, verify these are complete:

- [x] All commits pushed to `feat/groq-recommender` branch
- [x] Backend tests passing locally
- [x] Frontend tests passing locally
- [x] E2E testing completed successfully
- [x] Bug fixes applied and tested
- [x] Documentation complete

**Current Status: ALL VERIFIED ✅**

---

## Deployment Steps

### Step 1: Merge to Main

```bash
cd /Users/mr/Documents/attuned-survey

# Make sure everything is committed
git status

# Switch to main and pull latest
git checkout main
git pull origin main

# Merge feature branch
git merge feat/groq-recommender

# Push to main
git push origin main
```

### Step 2: Deploy Backend to Render

Your backend is hosted on Render (attuned-backend.onrender.com).

**Option A: Auto-Deploy (if configured)**
- Render watches the `main` branch
- Should auto-deploy after pushing to main
- Check Render dashboard for deployment progress

**Option B: Manual Deploy**
1. Go to https://dashboard.render.com
2. Find your `attuned-backend` service
3. Click "Manual Deploy" → "Deploy latest commit"
4. Wait for deployment to complete (~3-5 minutes)

**Required Environment Variables on Render:**
Make sure these are set in Render dashboard:
```
DATABASE_URL = [Your Supabase connection string]
GROQ_API_KEY = your_groq_api_key_here
GROQ_MODEL = llama-3.3-70b-versatile
```

**What will happen:**
- Render will install new dependencies (groq, jsonschema)
- Flask app will start and create new database tables automatically
- New API endpoints will become available

### Step 3: Verify Backend Deployment

Once Render deployment completes:

```bash
# Test production backend
curl https://attuned-backend.onrender.com/api/survey/submissions | jq

# Test new recommendations endpoint (should now work!)
curl -X POST https://attuned-backend.onrender.com/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "player_a": {"submission_id": "YOUR_SUBMISSION_ID"},
    "player_b": {"submission_id": "OTHER_SUBMISSION_ID"},
    "session": {"rating": "R", "target_activities": 5}
  }' | jq
```

Expected: 200 response with activities ✅

### Step 4: Deploy Frontend to Vercel

Your frontend is on Vercel.

**Vercel will auto-deploy when main branch is pushed!**

1. Push triggered → Vercel builds frontend
2. `pnpm build` runs → Vite builds with `NODE_ENV=production`
3. `vite.config.js` sets VITE_API_URL to production backend ✅
4. Deployment completes in ~2 minutes

**Check deployment:**
- Go to https://vercel.com/dashboard
- Find your `attuned-survey` project
- Watch deployment progress
- Click "Visit" when complete

### Step 5: Import Activities (Production Database)

Once backend is deployed, import your activities to production:

```bash
# Connect to production backend
cd backend
source venv/bin/activate

# Set DATABASE_URL to production Supabase
export DATABASE_URL="your_production_supabase_url"
export GROQ_API_KEY="your_groq_api_key_here"

# Import activities
python scripts/import_activities.py /path/to/your/activities.csv --clear
```

### Step 6: Production Testing

**Test the full flow on production:**

1. **Visit your Vercel URL** (e.g., attuned-survey.vercel.app)
2. **Complete survey** as Player A
3. **Go to Admin** → Set baseline
4. **Complete another survey** as Player B
5. **View results** → See compatibility
6. **Click "Start Game"** → Should work! 🎮
7. **Navigate through activities**
8. **Complete session**

**Admin Panel:**
- Visit `/admin/recommendations`
- Generate activities
- Verify it works with production backend

---

## Verification Checklist

After deployment, verify:

- [ ] Production backend has new endpoints
  - `POST /api/recommendations` returns 200
  - `POST /api/compatibility` returns 200
- [ ] Frontend connects to production backend (no localhost errors)
- [ ] New database tables exist in Supabase
  - Check Supabase Studio for: profiles, sessions, activities, session_activities, compatibility_results
- [ ] Admin recommendations panel works
- [ ] "Start Game" button appears on results
- [ ] Gameplay page displays correctly
- [ ] Activities alternate between players
- [ ] Session config shows player names

---

## Rollback Plan (If Issues Arise)

### Quick Rollback

If something breaks:

```bash
# Revert main branch
git checkout main
git revert HEAD
git push origin main
```

This will revert to the previous version while keeping your feature branch safe.

### Database Safety

**New tables don't affect existing functionality!**
- Survey submissions still work
- Compatibility calculations still work (frontend fallback)
- Only new features will be disabled

If needed, you can drop new tables in Supabase:
```sql
DROP TABLE IF EXISTS session_activities CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS compatibility_results CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS activities CASCADE;
```

---

## Post-Deployment Monitoring

### Check These

1. **Render Logs**
   - Go to Render dashboard
   - View logs for any errors
   - Look for: "Database connection successful", "New tables created"

2. **Supabase Metrics**
   - Monitor query performance
   - Check table sizes
   - Verify data is being written

3. **Vercel Analytics**
   - Check for 500 errors
   - Monitor page load times
   - Verify no console errors

4. **User Feedback**
   - Test the complete flow yourself
   - Share with beta testers
   - Monitor for issues

---

## Expected Production Behavior

### Performance
- **Recommendations**: 1.5-2s for 25 activities (with fallbacks)
- **Compatibility**: 200-400ms (cached after first calculation)
- **Page loads**: No noticeable slowdown

### Data Flow
1. User completes survey → Profile created in database
2. View results → Compatibility calculated → Cached in database
3. Start game → 25 activities generated → Session persisted
4. Navigate gameplay → Activities loaded from database

---

## Success Criteria

Deployment is successful when:

✅ No errors in Render logs
✅ Frontend loads without console errors  
✅ Can generate recommendations via Admin panel
✅ Can start game from results page
✅ Gameplay displays 25 activities correctly
✅ Both players get activities (alternating)
✅ Session completes successfully

---

## Need Help?

If anything goes wrong:
1. Check Render logs first
2. Check browser console
3. Review BACKEND_TESTING_GUIDE.md
4. Ping me with error messages!

---

**Ready to deploy? Follow the steps above and let me know at each stage!** 🚀

