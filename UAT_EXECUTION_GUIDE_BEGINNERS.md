# UAT Execution Guide for Non-Developers

This guide explains **exactly where and how** to run each test, with detailed step-by-step instructions.

---

## 🖥️ Two Places You'll Work

### 1. **Terminal / Command Line** 
- This is the black window where you type commands
- On Mac: Open "Terminal" app (Applications → Utilities → Terminal)
- You'll see something like: `(venv) mr@MacBook-Pro backend %`

### 2. **Supabase Dashboard**
- This is your web browser
- Go to: https://supabase.com/dashboard
- Click on your project
- Click "SQL Editor" in the left sidebar

---

## 🧪 UAT-002: User Registration API Test

### What This Tests
Tests that your backend API can create new users in the database.

---

### Step 1: Start the Flask Backend

**WHERE:** Terminal (command line)

**COMMANDS TO TYPE:**
```bash
cd /Users/mr/Documents/attuned-survey/backend
source venv/bin/activate
python run_backend.py
```

**Note:** Your `.env` file should already have DATABASE_URL and GROQ_API_KEY set.

**WHAT TO EXPECT:**
You'll see output like:
```
🚀 Starting Attuned Survey Backend...
📍 Server will be available at: http://localhost:5001
```

**IMPORTANT:** Leave this terminal window open! The backend needs to keep running.

---

### Step 2: Open a Second Terminal Window

**WHERE:** Open a NEW terminal window (keep the first one running)

On Mac: 
- Command + N (new window)
- Or: Terminal menu → New Window

---

### Step 3: Send a Test Request

**WHERE:** The second terminal window

**COMMAND TO TYPE (all one line, or copy/paste):**
```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-111111111111",
    "email": "uat-test@example.com",
    "auth_provider": "email",
    "display_name": "UAT Test User",
    "demographics": {
      "gender": "woman",
      "sexual_orientation": "bisexual",
      "relationship_structure": "open"
    }
  }'
```

**NOTE:** Port is 5001 (not 5000) when using run_backend.py

**WHAT TO EXPECT:**
You should see a response like:
```json
{
  "success": true,
  "user": {
    "id": "550e8400-e29b-41d4-a716-111111111111",
    "email": "uat-test@example.com",
    "display_name": "UAT Test User",
    "subscription_tier": "free",
    ...
  }
}
```

**IF YOU SEE THIS:** ✅ Test PASSED!

**IF YOU SEE ERROR:** ❌ Copy the error message and we'll debug

---

### Step 4: Verify in Database

**WHERE:** Supabase Dashboard in your web browser

**STEPS:**
1. Open browser → https://supabase.com/dashboard
2. Click your project
3. Click "SQL Editor" in left sidebar
4. In the editor, type:
```sql
SELECT * FROM users WHERE email = 'uat-test@example.com';
```
5. Click "Run" button (or press Cmd+Enter)

**WHAT TO EXPECT:**
You should see 1 row with:
- id: 550e8400-e29b-41d4-a716-111111111111
- email: uat-test@example.com
- display_name: UAT Test User

**IF YOU SEE THIS:** ✅ Test PASSED!

---

### ✅ UAT-002 Pass Criteria

Mark as PASS if:
- [ ] Backend started without errors
- [ ] curl command returned success response
- [ ] User appears in database
- [ ] User has default values (subscription_tier='free', daily_activity_count=0)

---

## 🧪 UAT-007: Row Level Security Test

### What This Tests
Tests that users can ONLY see their own data (critical for security!)

---

### Step 1: Test User Can See Own Data

**WHERE:** Supabase Dashboard → SQL Editor

**WHAT TO TYPE:**
```sql
-- Simulate being logged in as Alice
SET ROLE authenticated;
SET request.jwt.claim.sub = '550e8400-e29b-41d4-a716-446655440001';

-- Try to read Alice's own user record
SELECT * FROM users WHERE id = '550e8400-e29b-41d4-a716-446655440001'::uuid;
```

**Click "Run"**

**WHAT TO EXPECT:**
You should see **1 row** (Alice's data)

**IF YOU SEE THIS:** ✅ Part 1 PASSED

---

### Step 2: Test User CANNOT See Other Users' Data

**WHERE:** Same SQL Editor (Supabase Dashboard)

**WHAT TO TYPE:**
```sql
-- Still logged in as Alice, try to see Bob's data
SELECT * FROM users WHERE id = '550e8400-e29b-41d4-a716-446655440002'::uuid;
```

**Click "Run"**

**WHAT TO EXPECT:**
You should see **0 rows** (Alice can't see Bob)

**IF YOU SEE THIS:** ✅ Part 2 PASSED

---

### Step 3: Reset (Clean Up)

**WHERE:** Same SQL Editor

**WHAT TO TYPE:**
```sql
-- Reset the session (back to admin mode)
RESET ROLE;
```

**Click "Run"**

Now you're back to admin mode and can see all data again.

---

### ✅ UAT-007 Pass Criteria

Mark as PASS if:
- [ ] Alice could see her own user record (Step 1 returned 1 row)
- [ ] Alice could NOT see Bob's record (Step 2 returned 0 rows)
- [ ] No error messages

---

## 🧪 UAT-005: Daily Activity Limits

### What This Tests
Tests that free users are limited to 25 activities per day, and premium users have no limit.

---

### Step 1: Check Bob's Limit (Free Tier, Near Limit)

**WHERE:** Supabase Dashboard → SQL Editor

**WHAT TO TYPE:**
```sql
SELECT email, subscription_tier, daily_activity_count 
FROM users 
WHERE email = 'bob@test.com';
```

**Click "Run"**

**WHAT TO EXPECT:**
- subscription_tier: free
- daily_activity_count: 20 (near the 25 limit)

---

### Step 2: Test Limit Check (Should Be Under Limit)

**WHERE:** Same SQL Editor

**WHAT TO TYPE:**
```sql
-- Bob has 20/25, should return TRUE (can still get activities)
SELECT 
    email,
    daily_activity_count,
    25 - daily_activity_count AS remaining,
    CASE WHEN daily_activity_count < 25 THEN 'CAN GET MORE' ELSE 'LIMIT REACHED' END AS status
FROM users
WHERE email = 'bob@test.com';
```

**Click "Run"**

**WHAT TO EXPECT:**
- remaining: 5
- status: CAN GET MORE

---

### Step 3: Test Diana (At Limit)

**WHERE:** Same SQL Editor

**WHAT TO TYPE:**
```sql
SELECT 
    email,
    daily_activity_count,
    25 - daily_activity_count AS remaining,
    CASE WHEN daily_activity_count < 25 THEN 'CAN GET MORE' ELSE 'LIMIT REACHED' END AS status
FROM users
WHERE email = 'diana@test.com';
```

**Click "Run"**

**WHAT TO EXPECT:**
- daily_activity_count: 25
- remaining: 0
- status: LIMIT REACHED

---

### Step 4: Test Alice (Premium, No Limit)

**WHERE:** Same SQL Editor

**WHAT TO TYPE:**
```sql
SELECT 
    email,
    subscription_tier,
    daily_activity_count,
    CASE WHEN subscription_tier = 'premium' THEN 'UNLIMITED' ELSE 'LIMITED' END AS limit_status
FROM users
WHERE email = 'alice@test.com';
```

**Click "Run"**

**WHAT TO EXPECT:**
- subscription_tier: premium
- limit_status: UNLIMITED

---

### ✅ UAT-005 Pass Criteria

Mark as PASS if:
- [ ] Bob shows 20/25 (under limit)
- [ ] Diana shows 25/25 (at limit)
- [ ] Alice shows premium/unlimited
- [ ] All queries returned expected results

---

## 🧪 UAT-003: Survey Auto-Save

### What This Tests
Tests that survey progress can be saved and resumed.

---

### Step 1: Create In-Progress Survey

**WHERE:** Supabase Dashboard → SQL Editor

**WHAT TO TYPE:**
```sql
-- Create an in-progress survey for Alice
INSERT INTO survey_progress (
  user_id, 
  survey_version, 
  status, 
  current_question, 
  completion_percentage, 
  answers
) VALUES (
  '550e8400-e29b-41d4-a716-446655440001'::uuid,
  '0.4',
  'in_progress',
  'A12',
  45,
  '{"A1": 7, "A2": 6, "A3": 5, "A4": 7, "A5": 4}'::jsonb
);
```

**Click "Run"**

**WHAT TO EXPECT:**
Success message: "Successfully run. 1 rows affected."

---

### Step 2: Retrieve Survey Progress

**WHERE:** Same SQL Editor

**WHAT TO TYPE:**
```sql
SELECT 
  user_id,
  survey_version,
  status,
  current_question,
  completion_percentage,
  answers
FROM survey_progress 
WHERE user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid;
```

**Click "Run"**

**WHAT TO EXPECT:**
1 row showing:
- status: in_progress
- current_question: A12
- completion_percentage: 45
- answers: {...5 answers...}

---

### Step 3: Update Progress (Simulate Auto-Save)

**WHERE:** Same SQL Editor

**WHAT TO TYPE:**
```sql
-- Add more answers (simulating user continuing survey)
UPDATE survey_progress 
SET 
  current_question = 'B3',
  completion_percentage = 65,
  answers = answers || '{"A13": 6, "A14": 5, "B1a": 1.0}'::jsonb,
  last_saved_at = NOW()
WHERE user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid
AND status = 'in_progress';
```

**Click "Run"**

**WHAT TO EXPECT:**
Success: "1 rows affected"

---

### Step 4: Verify Update Worked

**WHERE:** Same SQL Editor

**WHAT TO TYPE:**
```sql
SELECT 
  current_question,
  completion_percentage,
  jsonb_object_keys(answers) AS question_ids
FROM survey_progress 
WHERE user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid;
```

**Click "Run"**

**WHAT TO EXPECT:**
- current_question: B3 (updated!)
- completion_percentage: 65 (updated!)
- Shows 8 question IDs (A1-A5, A13-A14, B1a)

---

### ✅ UAT-003 Pass Criteria

Mark as PASS if:
- [ ] Survey progress saved successfully
- [ ] Could retrieve progress
- [ ] Could update progress (answers merged)
- [ ] All fields updated correctly

---

## 📝 How to Track Your Results

### Option 1: Use a Checklist

Create a simple text file called `my_uat_results.txt`:

```
UAT-001: Migration Execution - ✅ PASS (16 tables confirmed)
UAT-002: User Registration - ☐ (testing now...)
  Step 1 (Start backend): ☐
  Step 2 (curl test): ☐
  Step 3 (verify in DB): ☐
  Result: ☐ PASS / ☐ FAIL
  Notes: _______________

UAT-003: Survey Auto-Save - ☐
...
```

### Option 2: Use the Template in UAT_TEST_CASES.md

Scroll to the bottom of `UAT_TEST_CASES.md` (around line 580) and fill in the table.

---

## 🆘 Common Issues & Solutions

### Issue: "curl: command not found"

**Solution:** curl should be on Mac by default. If missing, use an alternative:

**Alternative 1 - Use Postman:**
1. Download Postman (free): https://www.postman.com/downloads/
2. Create new request:
   - Method: POST
   - URL: http://localhost:5001/api/auth/register
   - Headers: Content-Type = application/json
   - Body → raw → JSON:
   ```json
   {
     "id": "550e8400-e29b-41d4-a716-111111111111",
     "email": "uat-test@example.com",
     "display_name": "UAT Test User"
   }
   ```
3. Click "Send"

**Alternative 2 - Skip API test, use SQL directly:**
```sql
-- In Supabase SQL Editor
INSERT INTO users (id, email, display_name, subscription_tier)
VALUES (
  gen_random_uuid(),
  'uat-test-sql@example.com',
  'UAT Test User',
  'free'
);
```

---

### Issue: Backend won't start

**Error:** "DATABASE_URL env var is required"

**Solution:**
```bash
# Get your connection string from Supabase Dashboard:
# Settings → Database → Connection string → URI

# Then export it:
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"

# Try starting again:
python src/main.py
```

---

### Issue: "Can't connect to database"

**Check these:**
1. Is your Supabase project running?
2. Is the DATABASE_URL correct?
3. Is your internet working?

---

## 🎯 Simplified UAT Test Order

Instead of all 10 tests, **start with these 3 critical ones:**

### Test 1: Verify Migration Worked ✅ (Already Done!)
You confirmed 16 tables exist. **PASS**

### Test 2: Test Row Level Security (Most Important!)

**WHERE:** Supabase Dashboard → SQL Editor

**COPY/PASTE THIS ENTIRE BLOCK:**
```sql
-- Test 1: Alice can see her own data
SET ROLE authenticated;
SET request.jwt.claim.sub = '550e8400-e29b-41d4-a716-446655440001';
SELECT email FROM users WHERE id = '550e8400-e29b-41d4-a716-446655440001'::uuid;
-- Should return: alice@test.com

-- Test 2: Alice CANNOT see Bob's data
SELECT email FROM users WHERE id = '550e8400-e29b-41d4-a716-446655440002'::uuid;
-- Should return: NO ROWS (empty result)

-- Clean up
RESET ROLE;
```

**Click "Run"**

**EXPECTED:**
- First query: Shows `alice@test.com`
- Second query: Shows nothing (empty)

**IF THIS WORKS:** ✅ Your security is working! Users can't access each other's data.

---

### Test 3: Test Daily Activity Limits

**WHERE:** Supabase Dashboard → SQL Editor

**COPY/PASTE THIS:**
```sql
-- Check all test users' activity counts
SELECT 
    email,
    subscription_tier,
    daily_activity_count,
    CASE 
        WHEN subscription_tier = 'premium' THEN '∞ Unlimited'
        ELSE (25 - daily_activity_count)::text || ' remaining'
    END AS limit_status
FROM users
WHERE email LIKE '%@test.com'
ORDER BY email;
```

**Click "Run"**

**EXPECTED:**
```
alice@test.com    | premium | 0  | ∞ Unlimited
bob@test.com      | free    | 20 | 5 remaining
charlie@test.com  | free    | 0  | 25 remaining
diana@test.com    | free    | 25 | 0 remaining
eve@test.com      | free    | 0  | 25 remaining
```

**IF YOU SEE THIS:** ✅ Subscription limits are working!

---

## 📊 Quick UAT Results Template

After running the 3 tests above, you can fill this out:

```
UAT TESTING RESULTS
Date: ___________

CRITICAL TESTS:
✅ UAT-001: Migration Execution - PASS (16 tables confirmed)
☐ UAT-007: Row Level Security - PASS / FAIL
  - Alice sees own data: ☐ Yes ☐ No
  - Alice blocked from Bob's data: ☐ Yes ☐ No
  
☐ UAT-005: Daily Activity Limits - PASS / FAIL
  - Free users have limits: ☐ Yes ☐ No
  - Premium users unlimited: ☐ Yes ☐ No
  - Counts correct: ☐ Yes ☐ No

OVERALL: ☐ READY FOR PRODUCTION  ☐ NEEDS FIXES

Issues Found:
_______________________________________
_______________________________________
```

---

## 🎓 Glossary of Terms

**Terminal:** The black window where you type commands  
**Backend:** Your Python Flask server that handles API requests  
**API:** The endpoints like `/api/auth/register` that respond to requests  
**curl:** A command to send web requests from terminal  
**SQL:** The language to query your database  
**Supabase SQL Editor:** Web interface to run SQL commands  
**UUID:** A long unique ID like `550e8400-e29b-41d4-a716-446655440001`  
**RLS:** Row Level Security - makes sure users can only see their own data  

---

## ✅ You're Ready!

**Start with these 3 tests:**
1. ✅ UAT-001 (Done - 16 tables)
2. UAT-007 (Security - **do this first**, most important)
3. UAT-005 (Limits - quick and easy)

**Total time:** ~15 minutes for all 3 tests

If those pass, you're in great shape! The rest of the UAT tests can wait.

---

## 📞 Getting Help

**If you get stuck:**
1. Copy the error message
2. Note which test and step you're on
3. Share with me and I'll help debug

**If a test fails:**
1. That's okay! Document what happened
2. We can fix it together
3. Re-run the test after fixing

Good luck! 🚀

