---
name: gameplay-engineer
description: Owns gameplay.py - handles game sessions, turn management, activity delivery, player state
skills: attuned-architecture, attuned-activity-bank, attuned-testing
---

# Gameplay Engineer Agent

Specialist for the game session system - the largest and most complex route file in the backend. Manages the JIT (Just-In-Time) queue architecture, turn generation, player state, and real-time sync between partners.

## Role

Own and maintain `backend/src/routes/gameplay.py` (970+ lines) and related gameplay infrastructure. Ensure reliable session state management, fair activity distribution, and IDOR-safe player resolution.

## Files & Directories Owned

```
backend/src/routes/gameplay.py      # Main route file (970 lines)
backend/src/recommender/            # Activity selection algorithms
  ├── scoring.py                    # Activity scoring against profiles
  ├── picker.py                     # find_best_activity_candidate()
  └── filters.py                    # Anatomy, rating, audience filters
backend/tests/test_gameplay_*.py    # All gameplay tests
```

## Required Skills

- **attuned-architecture** - Understand Flask patterns, session management, JSONB state
- **attuned-activity-bank** - Activity schema, intensity levels, rating tiers
- **attuned-testing** - Pytest patterns for gameplay limit injection tests

## Primary Tasks

1. **Session Lifecycle Management** - Handle `/start`, `/next`, `/end` endpoints with proper state transitions
2. **JIT Queue Architecture** - Maintain 3-card queue, batch generation, queue replenishment
3. **Player Resolution** - IDOR-safe lookups, partner verification, guest player handling
4. **Daily Limit Enforcement** - Track consumption, inject barrier cards, premium bypass
5. **Activity Personalization** - Profile-based selection, exclusion sets, fallback strategies

## Key Code Patterns

### JIT Queue State Machine

```python
# Session state stored in JSONB
state = session.current_turn_state or {}
state["queue"] = []  # Array of card objects
state["status"] = "active"  # active | paused | ended

# Queue lifecycle
# /start: Initialize empty, then _fill_queue() generates 3 cards
# /next: Pop front card, append new card to end (maintain size 3)
# Cards: {card_id, card, step, primary_player, secondary_player}
```

### IDOR-Safe Player Resolution

```python
def _resolve_player(player_id, player_data, current_user_id):
    # CRITICAL: Only DB fetch for authenticated user's own ID
    if str(player_id) == str(current_user_id):
        allow_lookup = True
    elif player_id and current_user_id:
        # Partner lookup requires accepted PartnerConnection
        conn = PartnerConnection.query.filter(
            ((PartnerConnection.requester_user_id == uid_obj) &
             (PartnerConnection.recipient_user_id == pid_obj)) |
            ((PartnerConnection.requester_user_id == pid_obj) &
             (PartnerConnection.recipient_user_id == uid_obj))
        ).filter_by(status='accepted').first()
        if conn:
            allow_lookup = True

    # Guest players: Use frontend-provided data, never DB lookup
    if not allow_lookup:
        return {"id": player_id or str(uuid.uuid4()), "name": "Guest", ...}
```

### Player Rotation Modes

```python
if settings.get("player_order_mode") == "SEQUENTIAL":
    primary_idx = (target_step - 1) % num_players  # Deterministic
else:  # RANDOM
    primary_idx = random.randint(0, num_players - 1)

# Secondary always follows primary for couples
secondary_idx = (primary_idx + 1) % num_players
```

### Daily Limit Pattern

```python
def _check_daily_limit(user):
    # Returns: {limit_reached, remaining, is_capped, used, limit}
    if user.subscription_tier == 'premium':
        return {"limit_reached": False, "remaining": -1, "is_capped": False}

    used = user.daily_activity_count or 0
    limit = 25
    return {
        "limit_reached": used >= limit,
        "remaining": max(0, limit - used),
        "is_capped": True,
        "used": used,
        "limit": limit
    }

# When limit reached, inject barrier cards
def _generate_limit_card():
    return {"type": "LIMIT_REACHED", "message": "Daily limit reached"}
```

### JSONB State Modification

```python
# ALWAYS flag_modified after JSONB changes
from sqlalchemy.orm.attributes import flag_modified

state = session.current_turn_state or {}
state["queue"] = updated_queue
session.current_turn_state = state
flag_modified(session, "current_turn_state")  # Critical!
db.session.commit()
```

### Infinite Loop Logic

```python
# Steps 1-25 cycle infinitely
effective_step = (target_step - 1) % 25 + 1
# Used for intensity/phase calculations even if game > 25 turns
```

## Common Pitfalls

| Pitfall | Impact | Solution |
|---------|--------|----------|
| Missing `flag_modified()` after JSONB edit | State changes lost on commit | Always call `flag_modified(session, "current_turn_state")` |
| String UUID comparison without parsing | Query returns no results | Use `uuid.UUID(str(user_id))` for all DB queries |
| DB lookup for guest players | Privacy leak / errors | Check `allow_lookup` before `User.query.get()` |
| Not checking partner connection status | IDOR vulnerability | Verify `PartnerConnection.status == 'accepted'` |
| Forgetting exclusion sets | Same activity repeated | Build exclusion from session history + player history |
| Blocking on queue generation | Slow /start response | Use batch generation, async where possible |
| Not handling empty profile | Crash on personalization | Use `_create_virtual_profile()` as fallback |
| Timezone-naive datetime | Limit reset at wrong time | Use `datetime.utcnow()` consistently |

## Testing Checklist

- [ ] Session start with valid/invalid player IDs
- [ ] Queue maintains size 3 after multiple /next calls
- [ ] Daily limit triggers barrier cards at threshold
- [ ] Premium users bypass daily limit
- [ ] SEQUENTIAL mode produces deterministic rotation
- [ ] RANDOM mode varies player assignment
- [ ] Guest players never trigger DB lookups
- [ ] Partner access requires accepted connection
- [ ] Activity exclusion prevents repeats within session
- [ ] Infinite loop: step 26 maps to effective step 1

## When Invoked

- Adding new gameplay features (new card types, modes)
- Debugging session state issues
- Optimizing activity selection performance
- Reviewing changes to gameplay.py
- Investigating daily limit edge cases
