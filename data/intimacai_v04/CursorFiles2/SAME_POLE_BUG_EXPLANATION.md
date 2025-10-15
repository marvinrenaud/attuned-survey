# The Same-Pole Bug: Why Top/Top Scores High (When It Shouldn't)

## 🐛 The Bug

Two Tops (or two Bottoms) are scoring **HIGH compatibility** (70-80%) when they should score **LOW** (35-45%).

## 🔍 Why This Happens

### The Algorithm's Thinking (WRONG):

**Top #1 (Big Black Haiti):**
- hair_pull_give: 1 ✓
- hair_pull_receive: 0 ✓
- spanking_give: 1 ✓
- spanking_receive: 0 ✓

**Top #2 (Male Test 2):**
- hair_pull_give: 1 ✓
- hair_pull_receive: 0 ✓
- spanking_give: 1 ✓
- spanking_receive: 0 ✓

**Standard Jaccard says:** 
"They both answered the same on all questions! They're a perfect match!" → High score ❌

### The Reality (CORRECT):

**Top #1 wants to:**
- GIVE hair pulling → needs someone to RECEIVE it
- GIVE spanking → needs someone to RECEIVE it

**Top #2 wants to:**
- GIVE hair pulling → needs someone to RECEIVE it
- GIVE spanking → needs someone to RECEIVE it

**Reality says:**
"They both want to GIVE but neither wants to RECEIVE. They're incompatible!" → Low score ✅

## 📊 The Math

### Current (Broken) Calculation:

```
hair_pull_give:    Both = 1 → Match ✓
hair_pull_receive: Both = 0 → Match ✓
spanking_give:     Both = 1 → Match ✓
spanking_receive:  Both = 0 → Match ✓

Jaccard Score: 4/4 = 100% ❌ WRONG!
```

### Correct Calculation:

```
hair_pull_give:    Both = 1, but no one to receive → No match ✗
hair_pull_receive: Both = 0, no one gets what they need → No match ✗
spanking_give:     Both = 1, but no one to receive → No match ✗
spanking_receive:  Both = 0, no one gets what they need → No match ✗

Same-Pole Score: 0/4 = 0% ✓ CORRECT!
(With non-directional activities partial credit: ~20-30%)
```

## ✅ The Fix

Add `calculateSamePoleJaccard()` function that recognizes:

1. **If both want to GIVE but not RECEIVE → Incompatible** (0 points)
2. **If one is versatile (can give AND receive) → Partial credit** (0.3 points)
3. **If both are versatile → Better** (0.5 points)
4. **Non-directional activities work normally** (mutual interest counts)

## 🎯 Expected Results

### Before Fix:
```
Top #1 + Top #2
─────────────────────────────
Power:    40% (incompatible)
Domain:   85% (similar)
Activity: 75% ❌ WRONG! (standard Jaccard sees "matches")
Truth:   100% (both open)
─────────────────────────────
TOTAL:    70% ❌ FALSE POSITIVE
```

### After Fix:
```
Top #1 + Top #2
─────────────────────────────
Power:    40% (incompatible)
Domain:   85% (similar)
Activity: 25% ✓ FIXED! (same-pole Jaccard sees incompatibility)
Truth:   100% (both open)
─────────────────────────────
TOTAL:    42% ✓ CORRECT - LOW COMPATIBILITY
```

## 🔧 Implementation

The fix requires:

1. **Add** `calculateSamePoleJaccard()` function (lines 215-267 in v0.5)
2. **Update** `calculateActivityOverlap()` to detect same-pole pairs
3. **Use** same-pole Jaccard when both are Tops or both are Bottoms

## 📝 Real-World Example

**Scenario:** Two dominant partners meet

**Person A:** "I want to tie you up, spank you, and take control"  
**Person B:** "I want to tie you up, spank you, and take control"

**Current algorithm:** "You both want the same things! 75% compatible!" ❌  
**Fixed algorithm:** "You both want to dominate, no one wants to submit. 40% compatible." ✅

## 🎯 Bottom Line

Standard Jaccard treats activities as isolated preferences:
- "Do you both like chocolate?" YES → Match ✓

But BDSM activities require complementary roles:
- "Do you both want to be the one giving pain?" YES → Incompatible ✗
- Someone needs to RECEIVE what the other GIVES

**The fix recognizes that same-pole pairs (Top/Top, Bottom/Bottom) need opposite preferences to be compatible, which they rarely have.**
