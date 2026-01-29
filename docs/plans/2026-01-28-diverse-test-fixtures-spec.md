# Diverse Test Fixtures Specification

## Purpose

Create realistic test profile pairs representing the actual user population to:
1. Validate compatibility algorithm produces intuitive scores
2. Identify edge cases where current logic fails
3. Provide regression coverage for algorithm changes

## User Archetypes

Based on realistic intimacy preferences, we define these archetypes:

### By Interest Level

| Archetype | Characteristics | Activity Pattern |
|-----------|-----------------|------------------|
| **Enthusiast** | High interest across many categories | 70%+ activities at 1.0 |
| **Explorer** | Curious about most things | 60%+ activities at 0.5 (maybe) |
| **Selective** | Strong opinions, few maybes | Clear 1.0 or 0.0, few 0.5 |
| **Focused** | Deep interest in 1-2 categories | High in favorites, low elsewhere |
| **Vanilla** | Traditional intimacy preferences | High connection/sensation, low power/exploration |
| **Conservative** | Limited comfort zone | Most activities 0.0, few at 0.5-1.0 |

### By Power Dynamic

| Orientation | Top Score | Bottom Score | Confidence |
|-------------|-----------|--------------|------------|
| **Strong Top** | 90-100 | 0-20 | 0.85+ |
| **Moderate Top** | 65-80 | 30-45 | 0.60-0.75 |
| **Switch** | 45-55 | 45-55 | 0.50-0.65 |
| **Moderate Bottom** | 30-45 | 65-80 | 0.60-0.75 |
| **Strong Bottom** | 0-20 | 90-100 | 0.85+ |
| **Versatile** | 20-30 | 20-30 | 0.30-0.40 |

### By Arousal Pattern

| Pattern | SE | SIS-P | SIS-C | Description |
|---------|-----|-------|-------|-------------|
| **Eager** | 0.75+ | 0.30- | 0.30- | Easily aroused, uninhibited |
| **Anxious** | 0.50 | 0.70+ | 0.50 | Performance concerns |
| **Cautious** | 0.50 | 0.50 | 0.70+ | Consequence concerns |
| **Balanced** | 0.45-0.55 | 0.45-0.55 | 0.45-0.55 | Middle of the road |
| **Slow burn** | 0.30- | 0.50 | 0.50 | Needs time to warm up |

---

## Test Pair Specifications

### Pair 1: Perfect Match (Top + Bottom)

**Use case**: Validate that couples who agree on everything score ~95-100%

**Profile A: "Confident Top"**
- Power: Strong Top (top=95, bottom=10)
- Arousal: Eager (SE=0.80, SIS-P=0.25, SIS-C=0.30)
- Interest pattern: Selective
- Categories:
  - physical_touch: massage=1.0, hair_pull=1.0, spanking_moderate=1.0, spanking_hard=0.5, slapping=0.0, choking=0.0
  - oral: all=1.0
  - anal: all=0.0
  - power_exchange: restraints=1.0, blindfold=1.0, orgasm_control=1.0, protocols=0.5
  - verbal_roleplay: dirty_talk=1.0, commands=1.0, roleplay=0.5
  - display_performance: stripping=0.5, watching_strip=1.0
- Truth topics: all=0.8 (very open)
- Boundaries: none

**Profile B: "Eager Bottom"**
- Power: Strong Bottom (top=10, bottom=95)
- Arousal: Eager (SE=0.85, SIS-P=0.20, SIS-C=0.25)
- Interest pattern: Selective (matches A's preferences exactly for complementary activities)
- Categories: Mirror of A with give/receive swapped appropriately
  - physical_touch: massage=1.0, hair_pull=1.0, spanking_moderate=1.0, spanking_hard=0.5, slapping=0.0, choking=0.0
  - oral: all=1.0
  - anal: all=0.0
  - power_exchange: restraints=1.0, blindfold=1.0, orgasm_control=1.0, protocols=0.5
  - verbal_roleplay: dirty_talk=1.0, commands=1.0, roleplay=0.5
  - display_performance: stripping=1.0, watching_strip=0.5
- Truth topics: all=0.8
- Boundaries: none

**Expected Scores**:
- Overall: 95-100%
- Power complement: 100% (perfect Top/Bottom)
- Domain similarity: 95%+ (nearly identical)
- Activity overlap: 95-100% (perfect agreement including mutual "no")
- Truth overlap: 95%+ (both very open)

**Current Algorithm Issue**: Activity overlap will be lower due to anal category scoring 0% instead of 100% (mutual disinterest).

---

### Pair 2: Vanilla Couple (Switch + Switch)

**Use case**: Traditional intimacy preferences, both flexible on power

**Profile A: "Romantic Partner"**
- Power: Switch (top=50, bottom=55)
- Arousal: Balanced (SE=0.55, SIS-P=0.45, SIS-C=0.50)
- Interest pattern: Vanilla
- Categories:
  - physical_touch: massage=1.0, hair_pull=0.5, spanking=0.0, slapping=0.0, choking=0.0
  - oral: all=1.0
  - anal: all=0.0
  - power_exchange: all=0.0
  - verbal_roleplay: dirty_talk=0.5, moaning=1.0, commands=0.0
  - display_performance: low across board (0.0-0.5)
- Truth topics: fantasies=0.7, turn_ons=0.8, insecurities=0.5, boundaries=0.9
- Boundaries: none

**Profile B: "Affectionate Partner"**
- Power: Switch (top=55, bottom=50)
- Arousal: Balanced (SE=0.50, SIS-P=0.50, SIS-C=0.45)
- Interest pattern: Vanilla (matches A)
- Categories: Same as A
- Truth topics: Similar to A
- Boundaries: none

**Expected Scores**:
- Overall: 90-95%
- Power complement: 90% (Switch/Switch)
- Domain similarity: 95%+ (both vanilla-focused)
- Activity overlap: 90-95% (agree on what they want AND don't want)
- Truth overlap: 85%+

---

### Pair 3: Kink-Focused Complementary

**Use case**: Both into power exchange, complementary dynamics

**Profile A: "Experienced Dom"**
- Power: Strong Top (top=90, bottom=15)
- Arousal: Eager (SE=0.75, SIS-P=0.30, SIS-C=0.35)
- Interest pattern: Focused on power
- Categories:
  - physical_touch: massage=0.5, hair_pull=1.0, spanking_moderate=1.0, spanking_hard=1.0, slapping=0.5, choking=0.5
  - oral: give=1.0, receive=1.0
  - anal: all=0.0
  - power_exchange: all=1.0
  - verbal_roleplay: dirty_talk=1.0, commands=1.0, begging=1.0, roleplay=1.0
  - display_performance: watching=1.0, performing=0.5
- Truth topics: all=0.9 (very open)
- Boundaries: none

**Profile B: "Devoted Sub"**
- Power: Strong Bottom (top=15, bottom=90)
- Arousal: Balanced (SE=0.60, SIS-P=0.55, SIS-C=0.40)
- Interest pattern: Focused on power (complements A)
- Categories: Mirror of A for complementary activities
- Truth topics: all=0.85
- Boundaries: choking (soft limit)

**Expected Scores**:
- Overall: 88-95%
- Power complement: 100%
- Domain similarity: 90%+
- Activity overlap: 85-95% (high agreement, minor boundary consideration)
- Truth overlap: 90%+

---

### Pair 4: Enthusiast + Curious Explorer

**Use case**: One very experienced, one new but open

**Profile A: "Seasoned Enthusiast"**
- Power: Moderate Top (top=75, bottom=35)
- Arousal: Eager (SE=0.80, SIS-P=0.25, SIS-C=0.30)
- Interest pattern: Enthusiast (lots of 1.0s)
- Categories: High interest (0.8-1.0) across most activities
- Truth topics: all=0.9
- Boundaries: none

**Profile B: "Curious Newcomer"**
- Power: Moderate Bottom (top=35, bottom=70)
- Arousal: Cautious (SE=0.45, SIS-P=0.60, SIS-C=0.65)
- Interest pattern: Explorer (lots of 0.5 maybes)
- Categories: Mostly 0.5 (curious), few 0.0 (hard nos), few 1.0 (definite yes)
- Truth topics: 0.5-0.7 range
- Boundaries: breath_play, watersports

**Expected Scores**:
- Overall: 70-80%
- Power complement: 90%+ (complementary)
- Domain similarity: 70-80% (different intensity levels)
- Activity overlap: 65-75% (A wants more than B is ready for)
- Truth overlap: 70-80%

**Key insight**: This is a "growth opportunity" couple - B might grow into A's interests.

---

### Pair 5: Partial Mismatch

**Use case**: Good on some things, different on others

**Profile A: "Sensation Seeker"**
- Power: Switch (top=50, bottom=50)
- Arousal: Eager (SE=0.75, SIS-P=0.35, SIS-C=0.35)
- Interest pattern: Focused on sensation
- Categories:
  - physical_touch: all high (0.8-1.0)
  - oral: all=1.0
  - anal: interested (0.7-1.0)
  - power_exchange: low (0.0-0.3)
  - verbal_roleplay: moderate (0.5)
  - display_performance: low (0.0-0.3)
- Truth topics: 0.6-0.8

**Profile B: "Power Player"**
- Power: Switch (top=55, bottom=45)
- Arousal: Balanced (SE=0.55, SIS-P=0.50, SIS-C=0.45)
- Interest pattern: Focused on power exchange
- Categories:
  - physical_touch: moderate (0.5-0.7)
  - oral: all=1.0
  - anal: not interested (0.0)
  - power_exchange: all high (0.8-1.0)
  - verbal_roleplay: high (0.8-1.0)
  - display_performance: moderate (0.5-0.7)
- Truth topics: 0.7-0.9

**Expected Scores**:
- Overall: 60-70%
- Power complement: 90% (both Switches)
- Domain similarity: 60-70% (different focus areas)
- Activity overlap: 55-65% (agree on oral, disagree on anal/power)
- Truth overlap: 75-85%

---

### Pair 6a: Power Dynamic Conflict (Top + Top)

**Use case**: Both want to lead - incompatible power dynamic

**Profile A: "Alpha Top"**
- Power: Strong Top (top=95, bottom=5)
- Arousal: Eager (SE=0.80, SIS-P=0.20, SIS-C=0.25)
- Interest pattern: Enthusiast
- Categories: High across most, all _give high, all _receive low

**Profile B: "Dominant Top"**
- Power: Strong Top (top=90, bottom=10)
- Arousal: Eager (SE=0.75, SIS-P=0.25, SIS-C=0.30)
- Interest pattern: Enthusiast (similar to A)
- Categories: Same pattern as A - high _give, low _receive

**Expected Scores**:
- Overall: 35-45%
- Power complement: 40% (same-pole penalty)
- Domain similarity: 50% (same-pole reduction)
- Activity overlap: 25-35% (both want to give, neither receives)
- Truth overlap: 40-50% (same-pole penalty)

---

### Pair 6b: Power Dynamic Conflict (Bottom + Bottom)

**Use case**: Both want to receive - incompatible power dynamic

**Profile A: "Devoted Bottom"**
- Power: Strong Bottom (top=10, bottom=92)
- Arousal: Balanced (SE=0.55, SIS-P=0.50, SIS-C=0.45)
- Interest pattern: Enthusiast
- Categories: High across most, all _receive high, all _give low

**Profile B: "Submissive Bottom"**
- Power: Strong Bottom (top=8, bottom=88)
- Arousal: Cautious (SE=0.45, SIS-P=0.60, SIS-C=0.55)
- Interest pattern: Enthusiast (similar to A)
- Categories: Same pattern as A - high _receive, low _give

**Expected Scores**:
- Overall: 35-45%
- Power complement: 40% (same-pole penalty)
- Domain similarity: 50% (same-pole reduction)
- Activity overlap: 25-35% (both want to receive, neither gives)
- Truth overlap: 40-50% (same-pole penalty)

---

### Pair 7: Conservative + Conservative

**Use case**: Both have limited interests, but they align

**Profile A: "Reserved Partner"**
- Power: Versatile (top=25, bottom=30)
- Arousal: Slow burn (SE=0.30, SIS-P=0.55, SIS-C=0.60)
- Interest pattern: Conservative
- Categories:
  - physical_touch: massage=1.0, everything else=0.0
  - oral: receive=0.5, give=0.5
  - anal: all=0.0
  - power_exchange: all=0.0
  - verbal_roleplay: moaning=0.5, everything else=0.0
  - display_performance: all=0.0
- Truth topics: 0.3-0.5 (private)
- Boundaries: many

**Profile B: "Gentle Partner"**
- Power: Versatile (top=30, bottom=25)
- Arousal: Slow burn (SE=0.35, SIS-P=0.50, SIS-C=0.55)
- Interest pattern: Conservative (matches A)
- Categories: Same as A
- Truth topics: 0.3-0.5
- Boundaries: similar to A

**Expected Scores**:
- Overall: 85-95%
- Power complement: 70-80% (both versatile/undefined)
- Domain similarity: 90%+ (both low across board)
- Activity overlap: 90-95% (agree on limited scope)
- Truth overlap: 80-90% (both private, that's alignment)

**Current Algorithm Issue**: Will score low on many categories due to mutual disinterest being penalized.

---

### Pair 8: Mismatched Arousal Patterns

**Use case**: Compatible preferences but different arousal needs

**Profile A: "Eager Beaver"**
- Power: Moderate Top (top=70, bottom=40)
- Arousal: Eager (SE=0.85, SIS-P=0.20, SIS-C=0.25)
- Interest pattern: Enthusiast
- Categories: High across most

**Profile B: "Anxious Partner"**
- Power: Moderate Bottom (top=40, bottom=70)
- Arousal: Anxious (SE=0.40, SIS-P=0.80, SIS-C=0.50)
- Interest pattern: Similar interests to A, but with anxiety
- Categories: Same preferences as A

**Expected Scores**:
- Overall: 75-85% (with arousal modifiers)
- Power complement: 95%+
- Domain similarity: 90%+
- Activity overlap: 90%+ (same preferences)
- Truth overlap: 85%+
- **Arousal impact**: SIS-P mismatch may affect pacing/performance activities

**Key insight**: Preferences align but B needs more patience/warmup.

---

### Pair 9: Boundary Conflict

**Use case**: One person's strong interest is other's hard limit

**Profile A: "Impact Enthusiast"**
- Power: Strong Top (top=85, bottom=20)
- Arousal: Eager (SE=0.75, SIS-P=0.30, SIS-C=0.35)
- Interest pattern: Focused on impact play
- Categories:
  - physical_touch: spanking_hard=1.0, slapping=1.0, all impact high
  - Everything else moderate

**Profile B: "Soft Touch"**
- Power: Moderate Bottom (top=30, bottom=75)
- Arousal: Cautious (SE=0.50, SIS-P=0.55, SIS-C=0.65)
- Interest pattern: Connection-focused
- Categories:
  - physical_touch: massage=1.0, gentle=1.0, ALL IMPACT=0.0
- Boundaries: impact_play (HARD LIMIT)

**Expected Scores**:
- Overall: 45-55% (boundary penalty applied)
- Power complement: 90%+
- Activity overlap: 50-60% before boundary
- **Boundary conflict**: A's core interest (1.0) hits B's hard limit
- After penalty: significant reduction

---

### Pair 10: Curious Vanilla Couple (Lots of Maybes)

**Use case**: Both vanilla-leaning but open to exploring, lots of uncertainty

**Profile A: "Curious Romantic"**
- Power: Switch (top=50, bottom=50)
- Arousal: Balanced (SE=0.50, SIS-P=0.50, SIS-C=0.50)
- Interest pattern: Mostly maybes with vanilla yeses
- Categories:
  - physical_touch: massage=1.0, hair_pull=0.5, spanking_moderate=0.5, spanking_hard=0.5, slapping=0.5, choking=0.0
  - oral: all=1.0
  - anal: all=0.5 (curious)
  - power_exchange: restraints=0.5, blindfold=0.5, orgasm_control=0.5, protocols=0.0
  - verbal_roleplay: dirty_talk=0.5, moaning=1.0, roleplay=0.5, commands=0.5
  - display_performance: all=0.5
- Truth topics: all=0.5-0.6 (somewhat open)
- Boundaries: breath_play

**Profile B: "Open-Minded Partner"**
- Power: Switch (top=55, bottom=50)
- Arousal: Balanced (SE=0.55, SIS-P=0.45, SIS-C=0.50)
- Interest pattern: Mostly maybes with vanilla yeses (matches A)
- Categories: Same as A - lots of 0.5s
- Truth topics: all=0.5-0.6
- Boundaries: breath_play

**Expected Scores**:
- Overall: 85-90%
- Power complement: 90% (Switch/Switch)
- Domain similarity: 90%+ (similar curiosity levels)
- Activity overlap: 85-90% (mutual maybes = alignment, mutual nos = alignment)
- Truth overlap: 80-85%

**Key insight**: Two people who are both "maybe" on most things should be highly compatible - they can explore together.

---

### Pair 11: The "Growth Journey" Couple

**Use case**: Established explorer + brand new partner

**Profile A: "Experienced Guide"**
- Power: Switch (top=60, bottom=55)
- Arousal: Balanced (SE=0.65, SIS-P=0.40, SIS-C=0.40)
- Interest pattern: Broad experience
- Categories: Varied - high in some, moderate in others, knows what they like

**Profile B: "Total Newbie"**
- Power: Versatile/Undefined (top=35, bottom=40)
- Arousal: Cautious (SE=0.40, SIS-P=0.65, SIS-C=0.70)
- Interest pattern: Mostly "maybe" (0.5)
- Categories: Almost everything at 0.5 (curious but uncertain)
- Truth topics: 0.4-0.6 (somewhat open)

**Expected Scores**:
- Overall: 65-75%
- Power complement: 70-75%
- Activity overlap: 60-70% (A's yes + B's maybe = partial match)
- Truth overlap: 65-75%

---

## Summary: Expected Score Ranges

| Pair | Type | Expected Overall |
|------|------|------------------|
| 1 | Perfect Match | 95-100% |
| 2 | Vanilla Couple | 90-95% |
| 3 | Kink Complementary | 88-95% |
| 4 | Enthusiast + Curious | 70-80% |
| 5 | Partial Mismatch | 60-70% |
| 6a | Power Conflict (Top+Top) | 35-45% |
| 6b | Power Conflict (Bottom+Bottom) | 35-45% |
| 7 | Conservative Match | 85-95% |
| 8 | Arousal Mismatch | 75-85% |
| 9 | Boundary Conflict | 45-55% |
| 10 | Curious Vanilla (Maybes) | 85-90% |
| 11 | Growth Journey | 65-75% |

---

## Future: Anatomy Iterations

For future testing, each compatible pair type should be tested across anatomy combinations to ensure activity filtering works correctly.

### Anatomy Configurations

| Config | Person A | Person B | Notes |
|--------|----------|----------|-------|
| **A1** | penis | vagina | "Traditional" heterosexual |
| **A2** | vagina | penis | Reversed A1 |
| **A3** | penis | penis | Gay male |
| **A4** | vagina | vagina | Lesbian |
| **A5** | penis + breasts | vagina | Trans woman + cis woman |
| **A6** | vagina + breasts | penis | Cis woman + cis man |
| **A7** | penis | vagina + breasts | Cis man + cis woman |
| **A8** | all | all | Both have all anatomy |
| **A9** | penis | penis + breasts | Gay male + trans woman |
| **A10** | vagina | vagina + breasts | Cis woman + trans woman |

### Activities Affected by Anatomy

| Activity | Requires |
|----------|----------|
| penetrative_vaginal | vagina (receiver) |
| penetrative_anal | any |
| oral_penis | penis (receiver) |
| oral_vagina | vagina (receiver) |
| breast_play | breasts |

### Test Matrix (Future)

For each of the 12 compatibility pairs above, test with anatomy configs A1-A10 to verify:
1. Activity filtering removes anatomically-impossible activities
2. Scores adjust appropriately when activities are filtered
3. No crashes or errors with any combination

**Note**: This anatomy testing is OUT OF SCOPE for current work but documented here for future implementation.

---

## Next Steps

1. Review this specification for completeness
2. Identify any missing user archetypes
3. Validate expected score ranges make intuitive sense
4. Proceed to Phase 2: Document current algorithm behavior against these pairs
