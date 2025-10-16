# Frontend Integration Testing Guide

## What We've Built

The frontend now has complete integration with the recommendations backend:

### New Features

1. **Admin Panel → Recommendations Tab**
   - Select two players from existing submissions
   - Configure: Rating (G/R/X), Activity Type (Random/Truth/Dare), Number of Activities
   - Generate button calls backend API
   - View results with stats, activity preview, and full JSON
   - Download recommendations as JSON file

2. **Results Page → "Start Game" Button**
   - Appears after compatibility is calculated
   - Generates 25 activity session
   - Navigates to Gameplay page

3. **Gameplay Page (New!)**
   - Step-by-step activity display
   - Progress tracker
   - Activity cards with type badges and intensity indicators
   - Previous/Next navigation
   - Complete session or end early
   - Returns to results

### New API Methods

Added to `frontend/src/lib/storage/apiStore.js`:
- `generateRecommendations(payload)` - Generate activities
- `getSessionActivities(sessionId)` - Fetch session
- `calculateCompatibility(idA, idB)` - Calculate & store
- `getCompatibility(idA, idB)` - Retrieve cached

---

## Testing the Frontend

### Prerequisites

1. **Backend must be running** on port 5001
2. **At least 2 survey submissions** in the database
3. **One submission set as baseline** (via Admin panel)

### Quick Frontend Test (3 Steps)

#### Step 1: Start Frontend Dev Server

```bash
cd /Users/mr/Documents/attuned-survey/frontend
pnpm dev
```

Expected: Frontend starts on http://localhost:5174 (or 5173)

#### Step 2: Test Admin Panel Recommendations

1. Navigate to http://localhost:5174/admin
2. Enter password: `1111`
3. Click "Recommendations" card
4. **Expected to see:**
   - Dropdown menus with existing submissions
   - Configuration options (Rating, # Activities, Type)
   - "Generate Plan" button

5. Click "Generate Plan"
6. **Expected to see:**
   - Loading state (button shows "Generating...")
   - Stats cards: Total, Truths, Dares, From Bank, Generation Time
   - Activity preview with first 10 activities
   - Each activity shows: #, Type badge, Intensity, Description
   - "Download JSON" button works

#### Step 3: Test Complete User Flow

1. **Complete a survey** (if you haven't already)
   - Go to http://localhost:5174/survey
   - Fill out survey and submit

2. **Set baseline** (if not already set)
   - Go to http://localhost:5174/admin
   - Click "Set" button next to a submission

3. **View results with compatibility**
   - Complete another survey (or use existing)
   - Go to results page
   - **Expected:** Compatibility score displayed

4. **Start game**
   - Click "Start Game" button (pink/rose gradient)
   - **Expected:** Navigate to Gameplay page
   - **See:** 
     - Progress bar showing "Step 1 of 25"
     - Activity card with Truth/Dare badge
     - Intensity dots (5 dots, filled based on level)
     - Activity description
     - Navigation buttons

5. **Navigate through activities**
   - Click "Next" to advance
   - Click "Previous" to go back
   - **Expected:** Smooth transitions, progress bar updates
   - On last step: "Complete Session" button appears

6. **Complete or end game**
   - Click "Complete Session" or "End Game Early"
   - **Expected:** Return to results page

---

## What to Look For

### ✅ Success Indicators

**Admin Recommendations Panel:**
- ✅ Dropdowns populated with submission names
- ✅ Generate button enabled when both players selected
- ✅ API call completes in < 3 seconds for 5 activities
- ✅ Stats show balanced truths/dares
- ✅ Activities have proper structure
- ✅ Download JSON works

**Results Page:**
- ✅ "Start Game" button appears when baseline match exists
- ✅ Button disabled while generating
- ✅ Navigation to gameplay works

**Gameplay Page:**
- ✅ Progress bar updates correctly
- ✅ Activity cards display with proper styling
- ✅ Type badges show correct colors (green=truth, purple=dare)
- ✅ Intensity indicators show filled/unfilled dots
- ✅ Navigation buttons work (Previous disabled on first, Next→Complete on last)
- ✅ Session info displays at bottom

### 🔍 Things to Verify

1. **Activity Quality** (once you import your CSV):
   - Activities make sense for the rating level
   - Scripts are clear and actionable
   - Intensity progression feels natural

2. **Compatibility Accuracy**:
   - Backend calculation matches frontend (should be same algorithm)
   - Scores are reasonable (0-100%)
   - Breakdown percentages add up logically

3. **Error Handling**:
   - Backend offline → Clear error messages
   - Missing data → Graceful fallbacks
   - Network errors → Retry options

---

## Console Debugging

Open browser DevTools console to see detailed logs:

```javascript
// API calls show:
Generating recommendations... {player_a: "xxx", player_b: "yyy", target: 25}
✅ Recommendations generated: {session_id: "...", activity_count: 25, stats: {...}}

// Compatibility:
Calculating compatibility... {submissionIdA: "xxx", submissionIdB: "yyy"}
✅ Compatibility calculated: {score: 87, interpretation: "..."}

// Gameplay:
Loading session: abc-123-def
✅ Session loaded: {id: "...", activities: 25}
```

---

## Known Behaviors

### Expected (Not Bugs):

1. **Fallback Activities**: If activity bank is empty, you'll see generic fallback templates
   - "Share your favorite memory from this year"
   - "Describe what attracted you to your partner"
   - These are safe defaults until you import your activity CSV

2. **All Actor "A"**: Current implementation assigns all actions to Player A
   - TODO: Implement smart actor assignment based on power dynamics
   - This will be enhanced when Groq AI generation is fully enabled

3. **Fast Generation**: With fallbacks, generation is near-instant
   - Once Groq AI is enabled, expect 2-5 seconds for 25 activities
   - Once activity bank is populated, mix of bank + AI

4. **No Session State Persistence**: 
   - If you refresh during gameplay, you lose progress
   - This is intentional for prototype
   - Can be enhanced with session resumption later

---

## Troubleshooting

### "Start Game" button not appearing
- Check: Is baseline set in Admin panel?
- Check: Does compatibility calculation succeed?
- Check: Are both profiles v0.4?

### Recommendations return errors
- Check: Backend is running on port 5001
- Check: Selected submissions have derived profile data
- Check: Network tab shows 200 response

### Gameplay page shows error
- Check: Session was created successfully
- Check: Activities were persisted to database
- Check: Network request to /api/recommendations/:id succeeds

### Activities look generic/repetitive
- Expected! Import your activity CSV:
  ```bash
  cd backend
  source venv/bin/activate
  python scripts/import_activities.py your_file.csv --clear
  ```

---

## Next Steps

Once frontend testing looks good:

1. ✅ Frontend components working
2. Import your activity spreadsheet
3. Test with real activity content
4. Enable Groq AI generation (optional - currently using fallbacks for speed)
5. Add more sophisticated actor assignment
6. Add session persistence/resumption

---

## Quick Visual Test Checklist

- [ ] Admin → Recommendations tab loads
- [ ] Can select 2 players from dropdown
- [ ] Generate Plan button works
- [ ] Stats cards show correct numbers
- [ ] Activity preview shows first 10 items
- [ ] Download JSON works
- [ ] Results page shows "Start Game" button (when baseline set)
- [ ] Clicking "Start Game" navigates to gameplay
- [ ] Gameplay shows activity #1 correctly
- [ ] Next/Previous buttons work
- [ ] Progress bar updates as you navigate
- [ ] Complete Session returns to results

All passing? You're ready to go! 🚀

