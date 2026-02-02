# Manual Mode: Paired Cards Design

**Date:** February 1, 2026
**Status:** DRAFT - Pending Frontend Review
**Author:** Backend Team

---

## Executive Summary

This document proposes a solution for the manual mode bug where users select Truth/Dare but the displayed content doesn't match their selection. The root cause is that manual mode was **partially designed but never fully implemented** in the backend.

**Proposed Solution:** Generate paired cards (one TRUTH + one DARE) for each turn in manual mode. Frontend picks which to display based on user selection. Only the selected card is tracked and billed.

---

## Current Problem

### What Frontend Observes

1. User sees picker → selects "Truth" or "Dare"
2. Card reveals → header matches selection, but `display_text` is whatever was pre-loaded
3. Swipe → `selected_type` sent to backend for NEXT turn

**The selection only affects future cards, not the current one.**

### Root Cause Analysis

| Component | Expected | Actual | Status |
|-----------|----------|--------|--------|
| `next_turn()` reads `selected_type` | Yes | No | Missing |
| `_fill_queue()` passes `selected_type` | Yes | No | Missing |
| MANUAL mode returns `WAITING_FOR_SELECTION` | Yes | No | Never implemented |
| Test file shows intended behavior | Yes | Test at line 135 | Test exists but feature incomplete |

**Evidence:**
- `backend/test_gameplay.py:135-156` - Test expects `WAITING_FOR_SELECTION` status
- `API_DOCUMENTATION.md:297` - Documents `selected_type` as optional parameter
- `_generate_turn_data(selected_type=...)` - Function accepts parameter but never receives it

---

## Proposed Solution: Paired Cards

### Overview

When `selection_mode: "MANUAL"`, the backend generates **pairs** of activities (one TRUTH, one DARE) for each turn. Frontend receives both options and selects which to display. Only the **selected** activity is tracked/consumed.

### Why This Approach?

| Alternative | Pros | Cons |
|-------------|------|------|
| **Paired Cards (Recommended)** | Single API call, real content for both options, works offline after load | Slightly larger payload |
| **WAITING_FOR_SELECTION Flow** | Matches original test design | 2 API calls per turn, latency |
| **Dual-Text Cards** | Smaller payload | Activities are designed as TRUTH OR DARE, not both |
| **Fetch on Selection** | Clean separation | Network latency on every selection |

---

## Technical Design

### Queue Structure

**RANDOM mode (unchanged):**
```json
{
  "queue": [
    { "turn_number": 1, "card": { "type": "TRUTH", "display_text": "...", "card_id": "123" }, ... },
    { "turn_number": 2, "card": { "type": "DARE", "display_text": "...", "card_id": "456" }, ... },
    { "turn_number": 3, "card": { "type": "TRUTH", "display_text": "...", "card_id": "789" }, ... }
  ]
}
```

**MANUAL mode (new):**
```json
{
  "selection_mode": "MANUAL",
  "current_turn_number": 1,
  "queue": [
    { "turn_number": 1, "card": { "type": "TRUTH", "display_text": "What's your biggest fantasy?", "card_id": "123" }, ... },
    { "turn_number": 1, "card": { "type": "DARE", "display_text": "Give your partner a massage", "card_id": "456" }, ... },
    { "turn_number": 2, "card": { "type": "TRUTH", "display_text": "...", "card_id": "789" }, ... },
    { "turn_number": 2, "card": { "type": "DARE", "display_text": "...", "card_id": "101" }, ... },
    { "turn_number": 3, "card": { "type": "TRUTH", "display_text": "...", "card_id": "102" }, ... },
    { "turn_number": 3, "card": { "type": "DARE", "display_text": "...", "card_id": "103" }, ... }
  ]
}
```

**Key fields:**
- `turn_number`: Groups paired cards together
- `selection_mode`: Echoed back so frontend knows which mode
- `current_turn_number`: Convenience field for the active turn

---

## Frontend Contract

### Start Game

**Request:** (unchanged)
```json
POST /api/game/start
{
  "player_ids": [...],
  "settings": {
    "selection_mode": "MANUAL",
    "intimacy_level": 3,
    ...
  }
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "selection_mode": "MANUAL",
  "current_turn_number": 1,
  "queue": [
    // 3 turns worth = 6 cards (3 pairs)
    { "turn_number": 1, "card": { "type": "TRUTH", ... }, ... },
    { "turn_number": 1, "card": { "type": "DARE", ... }, ... },
    { "turn_number": 2, "card": { "type": "TRUTH", ... }, ... },
    { "turn_number": 2, "card": { "type": "DARE", ... }, ... },
    { "turn_number": 3, "card": { "type": "TRUTH", ... }, ... },
    { "turn_number": 3, "card": { "type": "DARE", ... }, ... }
  ],
  "limit_status": { ... }
}
```

### Frontend Logic (Pseudo-code)

```dart
// After receiving start/next response
List<QueueItem> queue = response.queue;
int currentTurn = response.current_turn_number;

// Filter to get the pair for current turn
List<QueueItem> currentPair = queue
    .where((item) => item.turn_number == currentTurn)
    .toList();

QueueItem truthCard = currentPair.firstWhere((c) => c.card.type == "TRUTH");
QueueItem dareCard = currentPair.firstWhere((c) => c.card.type == "DARE");

// ========================================
// STEP 1: Show picker with REAL preview (optional enhancement)
// ========================================
// You could show truncated previews:
// "Truth: What's your biggest..." vs "Dare: Give your partner a..."
String userSelection = await showTruthDarePicker();

// ========================================
// STEP 2: Display the selected card
// ========================================
QueueItem activeCard = userSelection == "TRUTH" ? truthCard : dareCard;
displayCard(activeCard);

// ========================================
// STEP 3: On swipe/complete, advance turn
// ========================================
final response = await api.post('/api/game/$sessionId/next', {
  "action": "NEXT",
  "selected_type": userSelection  // REQUIRED in MANUAL mode
});

// Update local state with new queue
setState(() {
  queue = response.queue;
  currentTurn = response.current_turn_number;
});
```

### Next Turn Request

**Request:**
```json
POST /api/game/{session_id}/next
{
  "action": "NEXT",
  "selected_type": "TRUTH"  // REQUIRED when selection_mode is MANUAL
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "current_turn_number": 2,
  "queue": [
    // Turn 1 pair consumed, turns 2-4 now in queue
    { "turn_number": 2, "card": { "type": "TRUTH", ... }, ... },
    { "turn_number": 2, "card": { "type": "DARE", ... }, ... },
    { "turn_number": 3, "card": { "type": "TRUTH", ... }, ... },
    { "turn_number": 3, "card": { "type": "DARE", ... }, ... },
    { "turn_number": 4, "card": { "type": "TRUTH", ... }, ... },
    { "turn_number": 4, "card": { "type": "DARE", ... }, ... }
  ],
  "limit_status": { ... }
}
```

---

## Activity Tracking & Billing

| Event | Activity History | Credit Charged | Notes |
|-------|-----------------|----------------|-------|
| Card pair generated | Neither card | 0 | Generation is free |
| User selects TRUTH | TRUTH card logged | 1 | Selected card only |
| User selects DARE | DARE card logged | 1 | Selected card only |
| Unused pair card | **Not logged** | 0 | Discarded, available for future use |

**Important:** The unselected card is **not** added to activity history, so it can appear in future sessions. This prevents "phantom blocking" where generating an activity prevents its future use.

---

## Error Handling

| Scenario | Backend Response | Frontend Action |
|----------|-----------------|-----------------|
| MANUAL mode, missing `selected_type` | `400: {"error": "selected_type required in MANUAL mode"}` | Show error, re-prompt for selection |
| RANDOM mode, `selected_type` provided | Ignored (works normally) | N/A |
| `include_dare: false` + MANUAL | Only TRUTH cards in queue | Show "Truth only" UI, no picker needed |

---

## Edge Cases

### What if `include_dare: false`?

When dares are disabled in manual mode, the queue will only contain TRUTH cards (no pairs). Frontend should:
1. Detect this by checking if only TRUTH exists for current `turn_number`
2. Skip the picker UI
3. Display the TRUTH card directly

### Backward Compatibility

- **Existing RANDOM sessions:** Unchanged, single-card queue continues to work
- **New MANUAL sessions:** Use paired cards
- **Old API clients:** If they don't send `selected_type` in MANUAL mode, they get a 400 error (clear contract)

---

## Questions for Frontend Team

1. **Picker UX:** Should the picker show a preview of the actual content? (e.g., "Truth: What's your biggest..." vs "Dare: Give your partner...")

2. **Loading indicator:** While user deliberates, should we show a "thinking" state or is instant reveal preferred?

3. **include_dare: false:** Should we show a simplified "Ready?" prompt instead of Truth/Dare picker when only truths are available?

4. **Error handling:** What should happen if the API call fails after selection but before swipe? Retry with same selection?

---

## Backend Implementation Summary

Changes required in `backend/src/routes/gameplay.py`:

1. **`_generate_turn_data()`**: Add `generate_pair: bool` parameter to create both TRUTH and DARE cards
2. **`_fill_queue()`**: Check `selection_mode` and generate pairs when MANUAL
3. **`next_turn()`**: Read `selected_type`, consume both cards for turn, track only selected
4. **Response format**: Add `selection_mode` and `current_turn_number` fields

Estimated backend changes: ~100 lines of code modification

---

## Next Steps

1. **Frontend review:** Please review this design and provide feedback
2. **Agree on contract:** Confirm response format and error handling
3. **Backend implementation:** 1-2 day implementation
4. **Testing:** Integration tests for manual mode
5. **Deployment:** Behind feature flag initially?

---

*Document prepared for cross-team review. Please add comments or questions below.*
