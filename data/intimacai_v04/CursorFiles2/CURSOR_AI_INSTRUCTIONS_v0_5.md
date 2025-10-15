# Cursor AI Implementation Instructions v0.5: Compatibility Scoring Fix

## 🎯 OBJECTIVE

Fix the compatibility scoring algorithm to properly handle ALL power dynamics:
1. **Top/Bottom pairs** (should score 85-95% when compatible)
2. **Top/Top pairs** (should score 35-45% - incompatible power dynamic)
3. **Bottom/Bottom pairs** (should score 35-45% - incompatible power dynamic)
4. **Switch/Switch pairs** (should score appropriately based on activities)

## 📊 THE PROBLEMS

Current compatibility calculation has **FOUR critical flaws**:

1. **Implementation Bug**: Code shows 60% when methodology itself should give ~80%
2. **Symmetric Jaccard for Asymmetric Dynamics**: Algorithm treats Top giving (1) + Bottom receiving (1) as "no match" instead of "perfect match"
3. **Penalizing Complementary Differences**: Methodology punishes role-appropriate behaviors (e.g., Bottom being more adventurous than Top is actually ideal)
4. **🆕 Same-Pole False Positives**: Top/Top and Bottom/Bottom pairs score HIGH when they should score LOW (both want to give, no one wants to receive)

**Result**: 
- Top/Bottom pairs underscored by 20-30 points
- Top/Top pairs OVERSCORED by 40-50 points ← NEW BUG FOUND!

---

## 📁 DOCUMENTS TO REFERENCE

Share these files with Cursor AI in this order:

1. **CURSOR_AI_INSTRUCTIONS_v0_5.md** (this file) - Complete implementation guide
2. **intimacai_compatibility_FINAL_v0_5.ts** - Working corrected implementation
3. **SAME_POLE_BUG_EXPLANATION.md** - Details on the Top/Top bug
4. **Your current compatibility calculation code** - The file that needs fixing

---

## 🔧 IMPLEMENTATION CHANGES NEEDED (5 CHANGES)

### Change #1: Fix calculateDomainSimilarity()

**Location**: Domain similarity calculation function

**Problem**: For Top/Bottom pairs, differences in exploration/verbal domains are penalized when they're actually beneficial.

**Fix**: Add power-aware logic

```typescript
export function calculateDomainSimilarity(
  domainsA: DomainScores,
  domainsB: DomainScores,
  powerA: PowerDynamic,
  powerB: PowerDynamic
): number {
  
  const isComplementaryPair = (
    (powerA.orientation === 'Top' && powerB.orientation === 'Bottom') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Top')
  );

  if (isComplementaryPair) {
    // For complementary pairs, use minimum threshold approach for exploration/verbal
    // An eager Bottom (95) + measured Top (60) is ideal, not a problem!
    
    const sensationDist = 1 - Math.abs(domainsA.sensation - domainsB.sensation) / 100;
    const connectionDist = 1 - Math.abs(domainsA.connection - domainsB.connection) / 100;
    const powerDist = 1 - Math.abs(domainsA.power - domainsB.power) / 100;
    
    // For exploration and verbal: as long as minimum is adequate (>50), don't penalize
    const minExploration = Math.min(domainsA.exploration, domainsB.exploration);
    const minVerbal = Math.min(domainsA.verbal, domainsB.verbal);
    
    // If minimum is 50+, score is 1.0 (no penalty)
    // If minimum is below 50, scale proportionally
    const explorationScore = minExploration >= 50 ? 1.0 : minExploration / 50;
    const verbalScore = minVerbal >= 50 ? 1.0 : minVerbal / 50;
    
    return (sensationDist + connectionDist + powerDist + explorationScore + verbalScore) / 5;
  } else {
    // For Switch/Switch or same-pole pairs, use standard distance
    const sensationDist = 1 - Math.abs(domainsA.sensation - domainsB.sensation) / 100;
    const connectionDist = 1 - Math.abs(domainsA.connection - domainsB.connection) / 100;
    const powerDist = 1 - Math.abs(domainsA.power - domainsB.power) / 100;
    const explorationDist = 1 - Math.abs(domainsA.exploration - domainsB.exploration) / 100;
    const verbalDist = 1 - Math.abs(domainsA.verbal - domainsB.verbal) / 100;
    
    return (sensationDist + connectionDist + powerDist + explorationDist + verbalDist) / 5;
  }
}
```

---

### Change #2: Add calculateAsymmetricDirectionalJaccard()

**Location**: New function to add alongside your existing Jaccard calculation

**Problem**: Current Jaccard treats giving/receiving as independent. Top wants to give hair pulling (1) + Bottom wants to receive (1) = perfect match, but current algorithm sees them as mismatched.

**Fix**: Add this new function

```typescript
/**
 * Asymmetric directional Jaccard for Top/Bottom pairs
 * Recognizes that Top/Bottom dynamics are inherently asymmetric
 */
export function calculateAsymmetricDirectionalJaccard(
  topCategory: Record<string, number>,
  bottomCategory: Record<string, number>
): number {
  const keys = Object.keys(topCategory);
  
  let primaryMatches = 0;      // Top gives what Bottom wants to receive
  let primaryPotential = 0;     // Total opportunities for Top to give
  let secondaryMatches = 0;     // Bottom gives what Top wants to receive  
  let secondaryPotential = 0;   // Total opportunities for Bottom to give
  let nonDirectionalMatches = 0;
  let nonDirectionalPotential = 0;

  keys.forEach(key => {
    const topVal = topCategory[key] || 0;
    const bottomVal = bottomCategory[key] || 0;

    if (key.endsWith('_give')) {
      const receiveKey = key.replace('_give', '_receive');
      const bottomReceiveVal = bottomCategory[receiveKey] || 0;
      
      // PRIMARY: Top wants to GIVE → Bottom wants to RECEIVE
      if (topVal >= 0.5 || bottomReceiveVal >= 0.5) {
        primaryPotential++;
        if (topVal >= 0.5 && bottomReceiveVal >= 0.5) {
          primaryMatches++;
        }
      }
      
      // SECONDARY: Bottom wants to GIVE → Top wants to RECEIVE
      // (Less critical - Tops often don't want to receive)
      const topReceiveVal = topCategory[receiveKey] || 0;
      if (bottomVal >= 0.5 || topReceiveVal >= 0.5) {
        secondaryPotential++;
        if (bottomVal >= 0.5 && topReceiveVal >= 0.5) {
          secondaryMatches++;
        }
        // If Bottom wants to give but Top doesn't want to receive, give partial credit
        // (This is okay in Top/Bottom dynamics)
        else if (bottomVal >= 0.5 && topReceiveVal < 0.5) {
          secondaryMatches += 0.5; // 50% credit for "willing but not needed"
        }
      }
    } 
    else if (!key.endsWith('_receive')) {
      // Non-directional activities
      if (topVal >= 0.5 && bottomVal >= 0.5) {
        nonDirectionalMatches++;
      }
      if (topVal >= 0.5 || bottomVal >= 0.5) {
        nonDirectionalPotential++;
      }
    }
  });

  // Weight primary axis more heavily (80%) than secondary (20%)
  const totalMatches = (primaryMatches * 0.8) + (secondaryMatches * 0.2) + nonDirectionalMatches;
  const totalPotential = (primaryPotential * 0.8) + (secondaryPotential * 0.2) + nonDirectionalPotential;

  if (totalPotential === 0) return 0;
  return totalMatches / totalPotential;
}
```

---

### Change #3: 🆕 Add calculateSamePoleJaccard()

**Location**: New function for same-pole pairs (Top/Top or Bottom/Bottom)

**Problem**: Standard Jaccard sees "both want to give" as a match. Reality: no one wants to receive = incompatible.

**Fix**: Add this new function

```typescript
/**
 * NEW v0.5: Inverse Jaccard for same-pole pairs (Top/Top or Bottom/Bottom)
 * For these pairs, matching on giving/receiving is actually INCOMPATIBLE
 * They both want to give, but no one wants to receive
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
      
      // For same-pole pairs, we need OPPOSITE preferences on give/receive
      // But since they're both the same pole, this rarely happens
      
      if (valA >= 0.5 || valB >= 0.5) {
        totalPossibleInteractions++;
        
        // The only way this works is if one is versatile (wants to give AND receive)
        // Give partial credit for this flexibility
        if ((valA >= 0.5 && receiveA >= 0.5) && (valB >= 0.5 && receiveB < 0.5)) {
          compatibleInteractions += 0.3; // A is versatile, B only gives
        } else if ((valA >= 0.5 && receiveA < 0.5) && (valB >= 0.5 && receiveB >= 0.5)) {
          compatibleInteractions += 0.3; // B is versatile, A only gives
        } else if ((valA >= 0.5 && receiveA >= 0.5) && (valB >= 0.5 && receiveB >= 0.5)) {
          compatibleInteractions += 0.5; // Both are versatile - better!
        }
        // If both only want to give and not receive = 0 compatibility (default)
      }
    }
    else if (!key.endsWith('_receive')) {
      // Non-directional activities can still work for same-pole pairs
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

**Why This Works**:
- If both want to give but not receive → 0 points (incompatible)
- If one is versatile (can give AND receive) → 0.3 points (partial credit)
- If both are versatile → 0.5 points (they can switch)
- Non-directional activities still count normally

---

### Change #4: Update calculateActivityOverlap()

**Location**: Activity overlap calculation function

**Problem**: Currently uses symmetric Jaccard for all non-Top/Bottom pairs, missing same-pole incompatibility.

**Fix**: Add same-pole logic

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

  // NEW v0.5: Check for same-pole pairs
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
      // Use asymmetric directional Jaccard for complementary pairs
      const topActivities = powerA.orientation === 'Top' ? activitiesA : activitiesB;
      const bottomActivities = powerA.orientation === 'Bottom' ? activitiesA : activitiesB;

      score = calculateAsymmetricDirectionalJaccard(
        topActivities[category],
        bottomActivities[category]
      );
    } 
    else if (isSamePolePair && hasDirectionalActivities) {
      // NEW v0.5: Use inverse Jaccard for same-pole pairs
      score = calculateSamePoleJaccard(
        activitiesA[category],
        activitiesB[category]
      );
    }
    else {
      // Use standard Jaccard for Switch/Switch or non-directional categories
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

---

### Change #5: Update Main calculateCompatibility()

**Location**: Main compatibility calculation function

**Problem**: Domain similarity function not receiving power dynamics context.

**Fix**: Pass power dynamics to domain similarity (NO CHANGE from v0.4)

```typescript
export function calculateCompatibility(
  powerA: PowerDynamic,
  powerB: PowerDynamic,
  domainsA: DomainScores,
  domainsB: DomainScores,
  activitiesA: ActivityMap,
  activitiesB: ActivityMap,
  truthOverlap: number = 1.0,
  boundaryConflicts: number = 0,
  weights = { power: 0.15, domain: 0.25, activity: 0.40, truth: 0.20 }
): { score: number; breakdown: any } {
  
  const powerComp = calculatePowerComplement(powerA, powerB);
  
  // IMPORTANT: Pass power dynamics to domain similarity
  const domainSim = calculateDomainSimilarity(domainsA, domainsB, powerA, powerB);
  
  const activityOverlap = calculateActivityOverlap(powerA, powerB, activitiesA, activitiesB);

  let score = (
    weights.power * powerComp +
    weights.domain * domainSim +
    weights.activity * activityOverlap +
    weights.truth * truthOverlap
  );

  const boundaryPenalty = boundaryConflicts * 0.2;
  score = Math.max(0, score - boundaryPenalty);

  return {
    score: Math.round(score * 100),
    breakdown: {
      power_complement: Math.round(powerComp * 100),
      domain_similarity: Math.round(domainSim * 100),
      activity_overlap: Math.round(activityOverlap * 100),
      truth_overlap: Math.round(truthOverlap * 100),
      boundary_conflicts: boundaryConflicts
    }
  };
}
```

---

## 🧪 TESTING EXPECTATIONS

After implementing these changes, test with THREE profile combinations:

### Test 1: Top/Bottom (Big Black Haiti + Quick Check)
**Expected Results:**

| Component | Score | What It Means |
|-----------|-------|---------------|
| Power Complement | 100% | Perfect complementary dynamic |
| Domain Similarity | 94% | Complementary differences recognized |
| Activity Overlap | 79% | Asymmetric directional matching |
| Truth Overlap | 100% | Fully open communication |
| **TOTAL** | **90%** | **EXCEPTIONAL MATCH** |

### Test 2: Top/Top (Big Black Haiti + Male Test 2) 🆕
**Expected Results:**

| Component | Score | What It Means |
|-----------|-------|---------------|
| Power Complement | 40% | Incompatible power dynamic |
| Domain Similarity | ~85% | Similar interests but can't fulfill each other |
| Activity Overlap | **20-30%** | **Same-pole incompatibility** ← KEY FIX |
| Truth Overlap | 100% | Good communication doesn't fix power issue |
| **TOTAL** | **35-45%** | **LOW COMPATIBILITY** |

### Test 3: Bottom/Bottom (Two Bottom profiles) 🆕
**Expected Results:**

Similar to Top/Top: 35-45% overall, with low activity overlap (20-30%)

---

## 🚨 DEBUGGING THE 60% BUG

If after implementing the above changes you still see unexpected scores, check:

### Common Issues:

1. **Activity Mapping Error**
   - Verify survey responses are correctly mapped to give/receive keys
   - Check that key naming is consistent: `activity_give` / `activity_receive`

2. **Weight Miscalculation**
   - Confirm weights sum to 1.0: power(0.15) + domain(0.25) + activity(0.40) + truth(0.20) = 1.0
   - Check that weights are applied correctly in the final calculation

3. **Jaccard Selection Logic**
   - Verify Top/Bottom pairs use asymmetric Jaccard
   - Verify Top/Top pairs use same-pole Jaccard
   - Verify Bottom/Bottom pairs use same-pole Jaccard
   - Verify Switch/Switch pairs use standard Jaccard

4. **Category Inclusion**
   - Ensure all activity categories are included in the calculation
   - Verify no categories are being skipped or double-counted

---

## 📝 IMPLEMENTATION CHECKLIST

Use this checklist as you implement:

- [ ] Review intimacai_compatibility_FINAL_v0_5.ts for working implementation
- [ ] Backup current compatibility calculation code
- [ ] Update `calculateDomainSimilarity()` with power-aware logic
- [ ] Add new `calculateAsymmetricDirectionalJaccard()` function
- [ ] 🆕 Add new `calculateSamePoleJaccard()` function
- [ ] Update `calculateActivityOverlap()` to handle all three cases:
  - [ ] Top/Bottom → asymmetric Jaccard
  - [ ] Top/Top or Bottom/Bottom → same-pole Jaccard
  - [ ] Switch/Switch → standard Jaccard
- [ ] Update `calculateCompatibility()` to pass power dynamics to domain similarity
- [ ] Test #1: Top/Bottom profiles (should show 90% compatibility)
- [ ] Test #2: Top/Top profiles (should show 35-45% compatibility) ← NEW TEST
- [ ] Test #3: Bottom/Bottom profiles (should show 35-45% compatibility) ← NEW TEST
- [ ] Verify breakdown shows correct individual scores
- [ ] Verify Switch/Switch pairs still work correctly

---

## 💡 KEY INSIGHTS FOR CURSOR

**Tell Cursor AI these critical points:**

1. **Top/Bottom dynamics are inherently asymmetric** - What matters most is if the Top can give what the Bottom wants to receive

2. **Complementary differences are good** - An eager Bottom (exploration 95) paired with a measured Top (exploration 60) is IDEAL

3. **Same-pole pairs are inherently incompatible** 🆕 - Two Tops both wanting to give but not receive = no one gets what they want

4. **The primary axis matters more** - For Top/Bottom: Top giving → Bottom receiving (80% weight) is more important than the reverse (20% weight)

5. **Maintain three-way logic** 🆕:
   - Top/Bottom → Asymmetric directional Jaccard
   - Top/Top or Bottom/Bottom → Same-pole Jaccard (low scores)
   - Switch/Switch → Standard Jaccard

---

## 🎯 SUCCESS CRITERIA

You'll know the implementation is correct when:

✅ Top/Bottom profiles (Test 1) score 90% compatibility  
✅ Top/Top profiles (Test 2) score 35-45% compatibility 🆕  
✅ Bottom/Bottom profiles (Test 3) score 35-45% compatibility 🆕  
✅ Power complement remains correct for all pair types  
✅ Domain similarity adapts based on power dynamic  
✅ Activity overlap correctly identifies incompatible same-pole pairs 🆕  
✅ Switch/Switch pairs still calculate correctly  

---

## 🎉 EXPECTED OUTCOMES

### Before Fix:
```
Top/Bottom: 60% ❌ (should be 90%)
Top/Top:    75% ❌ (should be 35-45%)
```

### After Fix:
```
Top/Bottom: 90% ✅ (complementary pair)
Top/Top:    40% ✅ (same-pole incompatible)
```

---

## 📞 IF YOU NEED HELP

If Cursor AI encounters issues:

1. **First**: Review the complete working implementation in `intimacai_compatibility_FINAL_v0_5.ts`
2. **Second**: Check lines 215-267 for the same-pole Jaccard function
3. **Third**: Use the test data in intimacai_compatibility_FINAL_v0_5.ts to verify calculations step-by-step

---

**Your instinct was correct on both issues. The methodology was flawed for Top/Bottom pairs AND for same-pole pairs. Now we're fixing both.**
