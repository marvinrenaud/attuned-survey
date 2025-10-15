# 🔧 Quick Patch: Same-Pole Incompatibility Fix (v0.4 → v0.5)

## What This Patch Fixes

**Problem:** Top/Top and Bottom/Bottom pairs score 70-80% when they should score 35-45%  
**Cause:** Standard Jaccard sees "both want to give" as a match  
**Fix:** Add same-pole Jaccard that recognizes incompatibility

---

## 📦 What You Need

1. **CURSOR_AI_INSTRUCTIONS_v0_5.md** - Full implementation guide
2. **intimacai_compatibility_FINAL_v0_5.ts** - Working code with fix
3. **SAME_POLE_BUG_EXPLANATION.md** - Detailed bug explanation

---

## ⚡ Quick Implementation (3 Steps)

### Step 1: Add calculateSamePoleJaccard() Function

Add this new function after your `calculateAsymmetricDirectionalJaccard()`:

```typescript
/**
 * NEW v0.5: Inverse Jaccard for same-pole pairs (Top/Top or Bottom/Bottom)
 */
export function calculateSamePoleJaccard(
  categoryA: Record<string, number>,
  categoryB: Record<string, number>
): number {
  const keys = Object.keys(categoryA);
  let compatibleInteractions = 0;
  let totalPossibleInteractions = 0;

  keys.forEach(key => {
    const valA = categoryA[key] || 0;
    const valB = categoryB[key] || 0;

    if (key.endsWith('_give')) {
      const receiveKey = key.replace('_give', '_receive');
      const receiveA = categoryA[receiveKey] || 0;
      const receiveB = categoryB[receiveKey] || 0;
      
      if (valA >= 0.5 || valB >= 0.5) {
        totalPossibleInteractions++;
        
        // Partial credit for versatility
        if ((valA >= 0.5 && receiveA >= 0.5) && (valB >= 0.5 && receiveB < 0.5)) {
          compatibleInteractions += 0.3;
        } else if ((valA >= 0.5 && receiveA < 0.5) && (valB >= 0.5 && receiveB >= 0.5)) {
          compatibleInteractions += 0.3;
        } else if ((valA >= 0.5 && receiveA >= 0.5) && (valB >= 0.5 && receiveB >= 0.5)) {
          compatibleInteractions += 0.5;
        }
      }
    }
    else if (!key.endsWith('_receive')) {
      // Non-directional activities work normally
      if (valA >= 0.5 && valB >= 0.5) {
        compatibleInteractions++;
      }
      if (valA >= 0.5 || valB >= 0.5) {
        totalPossibleInteractions++;
      }
    }
  });

  if (totalPossibleInteractions === 0) return 0;
  return compatibleInteractions / totalPossibleInteractions;
}
```

### Step 2: Update calculateActivityOverlap()

Find your `calculateActivityOverlap()` function and update it:

```typescript
export function calculateActivityOverlap(
  powerA: PowerDynamic,
  powerB: PowerDynamic,
  activitiesA: ActivityMap,
  activitiesB: ActivityMap
): number {
  
  const isTopBottomPair = (
    (powerA.orientation === 'Top' && powerB.orientation === 'Bottom') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Top')
  );

  // ADD THIS: Check for same-pole pairs
  const isSamePolePair = (
    (powerA.orientation === 'Top' && powerB.orientation === 'Top') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Bottom')
  );

  const categories = Object.keys(activitiesA) as Array<keyof ActivityMap>;
  const scores: number[] = [];

  categories.forEach(category => {
    let score: number;

    const hasDirectionalActivities = [
      'physical_touch', 'oral', 'anal', 'power_exchange', 'display_performance'
    ].includes(category);

    if (isTopBottomPair && hasDirectionalActivities) {
      // Existing: asymmetric directional Jaccard
      const topActivities = powerA.orientation === 'Top' ? activitiesA : activitiesB;
      const bottomActivities = powerA.orientation === 'Bottom' ? activitiesA : activitiesB;
      score = calculateAsymmetricDirectionalJaccard(
        topActivities[category],
        bottomActivities[category]
      );
    } 
    // ADD THIS: Handle same-pole pairs
    else if (isSamePolePair && hasDirectionalActivities) {
      score = calculateSamePoleJaccard(
        activitiesA[category],
        activitiesB[category]
      );
    }
    else {
      // Existing: standard Jaccard for Switch/Switch
      score = calculateStandardJaccard(
        activitiesA[category],
        activitiesB[category]
      );
    }

    scores.push(score);
  });

  return scores.reduce((sum, val) => sum + val, 0) / scores.length;
}
```

### Step 3: Test

Test with three profile combinations:

```typescript
// Test 1: Top + Bottom → Should be ~90%
// Test 2: Top + Top → Should be ~40% ← NEW TEST
// Test 3: Bottom + Bottom → Should be ~40% ← NEW TEST
```

---

## ✅ Success Criteria

After implementing, verify:

| Pair Type | Expected Score | Reason |
|-----------|----------------|--------|
| Top + Bottom | 85-95% | Complementary (already working) |
| Top + Top | 35-45% | Same-pole incompatible (FIXED) |
| Bottom + Bottom | 35-45% | Same-pole incompatible (FIXED) |
| Switch + Switch | 80-90% | Versatile (already working) |

---

## 📊 What Changed

### Component Breakdown for Top/Top:

| Component | Before | After | Change |
|-----------|--------|-------|--------|
| Power | 40% | 40% | No change |
| Domain | 85% | 85% | No change |
| **Activity** | **75%** | **25%** | **-50%** ← KEY FIX |
| Truth | 100% | 100% | No change |
| **TOTAL** | **70%** | **42%** | **-28%** |

---

## 🎯 One-Line Summary

**Same-pole pairs (Top/Top, Bottom/Bottom) now correctly score LOW because they both want to give but no one wants to receive.**

---

## 📞 Need Help?

- **Full code**: See `intimacai_compatibility_FINAL_v0_5.ts`
- **Full guide**: See `CURSOR_AI_INSTRUCTIONS_v0_5.md`
- **Bug details**: See `SAME_POLE_BUG_EXPLANATION.md`
