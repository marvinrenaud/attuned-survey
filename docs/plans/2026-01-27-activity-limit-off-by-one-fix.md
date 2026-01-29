# Activity Limit Off-By-One Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the off-by-one bug where free users get 11 activities instead of 10 by refactoring the limit-check-and-scrub logic into a shared helper function.

**Architecture:** Extract `_enforce_activity_limit()` helper that performs fresh limit checks and applies consistent scrubbing logic. Both `start_game` and `next_turn` will use this helper after incrementing activity counts, ensuring the response always contains accurate limit status and properly scrubbed queues.

**Tech Stack:** Python 3.11, Flask, SQLAlchemy, pytest

**Branch:** `fix/activity-count-off-by-one`

---

## Problem Summary

Two issues cause free users to receive one extra activity:

1. **Stale `limit_status` in `start_game`**: The limit is checked at line 757 (before increment) but used for the scrub decision at line 811 (after increment). This causes scrubbing to be skipped when it should occur.

2. **Inconsistent `keep_first` logic**: `start_game` uses `keep_first=True` unconditionally (line 812), while `next_turn` conditionally sets `keep_first=False` when `used > limit` (lines 953-955).

## Solution Overview

Create `_enforce_activity_limit(queue, owner_id, anon_id)` that:
- Performs a **fresh** limit check (after increment)
- Applies scrubbing with **consistent** `keep_first` logic
- Returns both the scrubbed queue and fresh `limit_status`

---

## Task 1: Write Failing Tests for the Bug

**Files:**
- Create: `backend/tests/test_activity_limit_enforcement.py`

**Step 1.1: Create test file with imports and fixtures**

```python
"""
Tests for activity limit enforcement - specifically the off-by-one bug fix.

These tests verify that:
1. Users at limit-1 get exactly 1 more activity, then blocked
2. Users at limit get blocked immediately
3. limit_status in response is always fresh (post-increment)
4. Scrubbing is applied consistently in both start_game and next_turn
"""
import pytest
import uuid
import os
import jwt
from unittest.mock import patch
from datetime import datetime, timezone

from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity


@pytest.fixture
def test_activity(db_session):
    """Create a test activity for queue generation."""
    act = Activity(
        activity_id=1,
        type="truth",
        rating="G",
        intensity=1,
        script={'steps': [{'actor': 'A', 'do': 'Test activity'}]},
        is_active=True,
        approved=True
    )
    db_session.add(act)
    db_session.commit()
    return act


def create_user_at_count(db_session, count: int, tier: str = 'free') -> tuple:
    """Helper to create a user with specific lifetime_activity_count."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"test_{count}_{uuid.uuid4().hex[:6]}@test.com",
        lifetime_activity_count=count,
        subscription_tier=tier,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    token = jwt.encode(
        {"sub": str(user_id), "aud": "authenticated"},
        "test-secret-key",
        algorithm="HS256"
    )
    return user, token
```

**Step 1.2: Add test for fresh limit_status in start_game response**

```python
@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
class TestLimitStatusFreshness:
    """Tests that limit_status in response reflects post-increment state."""

    def test_start_game_returns_fresh_limit_status(self, client, db_session, app, test_activity):
        """
        BUG: start_game returns stale limit_status (pre-increment).

        User at count=9 starts game:
        - EXPECTED: limit_status shows used=10, remaining=0, limit_reached=True
        - ACTUAL (bug): limit_status shows used=9, remaining=1, limit_reached=False
        """
        user, token = create_user_at_count(db_session, count=9)

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert resp.status_code == 200
        data = resp.get_json()

        # Verify DB was incremented
        db_session.refresh(user)
        assert user.lifetime_activity_count == 10

        # BUG CHECK: limit_status should reflect POST-increment state
        assert data['limit_status']['used'] == 10, \
            f"Expected used=10 (post-increment), got {data['limit_status']['used']}"
        assert data['limit_status']['remaining'] == 0, \
            f"Expected remaining=0, got {data['limit_status']['remaining']}"
        assert data['limit_status']['limit_reached'] is True, \
            "Expected limit_reached=True after hitting limit"
```

**Step 1.3: Add test for consistent scrubbing at boundary**

```python
    def test_start_game_scrubs_queue_at_limit(self, client, db_session, app, test_activity):
        """
        BUG: start_game doesn't scrub queue when user hits limit.

        User at count=9 starts game (hits limit=10 after charge):
        - EXPECTED: queue[1] and queue[2] are LIMIT_REACHED cards
        - ACTUAL (bug): queue has 3 real cards because scrub was skipped
        """
        user, token = create_user_at_count(db_session, count=9)

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert resp.status_code == 200
        data = resp.get_json()
        queue = data['queue']

        # First card is allowed (the one just paid for)
        assert queue[0]['card']['type'] != 'LIMIT_REACHED', \
            "First card should be real (just paid for)"

        # Remaining cards should be LIMIT_REACHED barriers
        assert queue[1]['card']['type'] == 'LIMIT_REACHED', \
            f"queue[1] should be LIMIT_REACHED, got {queue[1]['card']['type']}"
        assert queue[2]['card']['type'] == 'LIMIT_REACHED', \
            f"queue[2] should be LIMIT_REACHED, got {queue[2]['card']['type']}"
```

**Step 1.4: Add test for user exactly at limit**

```python
    def test_start_game_at_exact_limit_blocked(self, client, db_session, app, test_activity):
        """
        User already at limit (count=10) starts game:
        - EXPECTED: All cards are LIMIT_REACHED, no increment
        """
        user, token = create_user_at_count(db_session, count=10)

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert resp.status_code == 200
        data = resp.get_json()
        queue = data['queue']

        # Should NOT increment (already at limit)
        db_session.refresh(user)
        assert user.lifetime_activity_count == 10, \
            "Should not increment when already at limit"

        # All cards should be barriers
        assert data['limit_status']['limit_reached'] is True
        for i, card in enumerate(queue):
            assert card['card']['type'] == 'LIMIT_REACHED', \
                f"queue[{i}] should be LIMIT_REACHED when at limit"
```

**Step 1.5: Add test for total activity count across full session**

```python
@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
class TestTotalActivityCount:
    """Tests that users get exactly 10 activities, not 11."""

    def test_fresh_user_gets_exactly_10_activities(self, client, db_session, app, test_activity):
        """
        Fresh user (count=0) should see exactly 10 real activities.

        This is the core off-by-one test:
        - Start game: see card 1, count becomes 1
        - next_turn x9: see cards 2-10, count becomes 10
        - next_turn: should see LIMIT_REACHED, not card 11
        """
        user, token = create_user_at_count(db_session, count=0)

        # Start game
        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert resp.status_code == 200
        session_id = resp.get_json()['session_id']

        activities_seen = 1  # First one from start

        # Call next_turn until we hit limit
        for i in range(15):  # More than enough iterations
            resp = client.post(
                f'/api/game/{session_id}/next',
                json={},
                headers={'Authorization': f'Bearer {token}'}
            )
            assert resp.status_code == 200
            data = resp.get_json()

            current_card = data['queue'][0] if data['queue'] else None
            if current_card and current_card['card']['type'] == 'LIMIT_REACHED':
                break
            activities_seen += 1

        # Should have seen exactly 10 activities
        assert activities_seen == 10, \
            f"Expected exactly 10 activities, got {activities_seen}"

        # Verify final count in DB
        db_session.refresh(user)
        # Note: count may be 11 because the 10th card charge happens,
        # but we should only SEE 10 real cards
        assert user.lifetime_activity_count >= 10
```

**Step 1.6: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_activity_limit_enforcement.py -v`

Expected: Tests should FAIL, demonstrating the bugs:
- `test_start_game_returns_fresh_limit_status` - fails on used=9 vs expected 10
- `test_start_game_scrubs_queue_at_limit` - fails on queue[1] being real card
- `test_fresh_user_gets_exactly_10_activities` - may show 11 activities

**Step 1.7: Commit failing tests**

```bash
git add backend/tests/test_activity_limit_enforcement.py
git commit -m "test: add failing tests for activity limit off-by-one bug

Tests verify:
- limit_status freshness (post-increment values)
- Queue scrubbing at limit boundary
- Exact activity count (10, not 11)

All tests expected to FAIL until fix is implemented."
```

---

## Task 2: Create the `_enforce_activity_limit` Helper

**Files:**
- Modify: `backend/src/routes/gameplay.py:308` (after `_check_activity_limit`)

**Step 2.1: Add the helper function**

Add after `_increment_daily_count` function (around line 333):

```python
def _enforce_activity_limit(queue: List[Dict[str, Any]], owner_id: str = None,
                            anonymous_session_id: str = None) -> tuple:
    """
    Enforce activity limit on queue with fresh status check.

    This is the single source of truth for limit enforcement, used by both
    start_game and next_turn to ensure consistent behavior.

    Args:
        queue: The current turn queue
        owner_id: Authenticated user ID (optional)
        anonymous_session_id: Anonymous session ID (optional)

    Returns:
        tuple: (scrubbed_queue, fresh_limit_status)

    Logic:
        1. Perform fresh limit check (captures post-increment state)
        2. If limit reached:
           - keep_first=True if used == limit (allow the card just paid for)
           - keep_first=False if used > limit (block everything)
        3. Apply scrubbing to replace future cards with barriers
        4. Return both queue and fresh status for response
    """
    # Fresh limit check - this captures the post-increment state
    limit_status = _check_activity_limit(user_id=owner_id, anonymous_session_id=anonymous_session_id)

    if limit_status.get("limit_reached"):
        used = limit_status.get("used", 0)
        limit = limit_status.get("limit", 10)

        # Consistent keep_first logic:
        # - If used == limit: keep first card (the one just paid for)
        # - If used > limit: block everything (overage state)
        keep_first = used <= limit

        queue = _scrub_queue_for_limit(queue, keep_first=keep_first)

    return queue, limit_status
```

**Step 2.2: Run existing tests to ensure no breakage**

Run: `cd backend && python -m pytest tests/test_gameplay_limits.py tests/test_gameplay_limit_boundary.py -v`

Expected: Existing tests should still pass (we only added a function, didn't change existing code yet)

**Step 2.3: Commit helper function**

```bash
git add backend/src/routes/gameplay.py
git commit -m "feat: add _enforce_activity_limit helper function

Single source of truth for limit enforcement with:
- Fresh limit check (post-increment state)
- Consistent keep_first logic
- Returns both queue and limit_status

No behavior change yet - existing code paths unchanged."
```

---

## Task 3: Refactor `start_game` to Use Helper

**Files:**
- Modify: `backend/src/routes/gameplay.py` (start_game function, lines 757-826)

**Step 3.1: Update start_game to use the helper**

Replace the limit check and scrub logic in `start_game`.

Find and replace this section (approximately lines 807-826):

**BEFORE (remove this):**
```python
        # Re-check and Scrub
        # For Anonymous, the count relies on history. If we didn't insert history, limit doesn't change.
        # Let's trust the initial check result for this turn.

        if limit_status.get("limit_reached"):
             queue = _scrub_queue_for_limit(queue, keep_first=True) # Keep the one we (maybe) paid for

             # If strictly capped (e.g. 25/25), keep_first should be FALSE if we want to block new starts?
             # If limit is 25. Used is 25. User calls Start. Limit Reached = True.
             # Queue has 3 cards.
             # If we keep_first, they get Card 1. Then Next blocks.
             # This essentially gives them 26 cards.
             # Acceptable for MVP.

             state = session.current_turn_state
             state["queue"] = queue
             session.current_turn_state = state
             flag_modified(session, "current_turn_state")

        db.session.commit()
```

**AFTER (replace with):**
```python
        # Enforce limit with fresh check (captures post-increment state)
        queue, limit_status = _enforce_activity_limit(
            queue,
            owner_id=owner_id,
            anonymous_session_id=owner_anon_id
        )

        # Update session state with potentially scrubbed queue
        state = session.current_turn_state
        state["queue"] = queue
        session.current_turn_state = state
        flag_modified(session, "current_turn_state")

        db.session.commit()
```

**Important:** Also remove the initial `limit_status` variable assignment at line 757 since we now get fresh status from the helper. Find:

```python
        # INITIAL LIMIT CHECK
        limit_status = _check_daily_limit(user_id=owner_id, anonymous_session_id=owner_anon_id)
```

Keep it but note it's only used for the initial fill_queue decision. The response will use the fresh status from `_enforce_activity_limit`.

**Step 3.2: Run the new tests**

Run: `cd backend && python -m pytest tests/test_activity_limit_enforcement.py -v`

Expected:
- `test_start_game_returns_fresh_limit_status` - should now PASS
- `test_start_game_scrubs_queue_at_limit` - should now PASS
- Other tests may still need next_turn fix

**Step 3.3: Run full gameplay test suite**

Run: `cd backend && python -m pytest tests/test_gameplay*.py -v`

Expected: All tests should pass

**Step 3.4: Commit start_game refactor**

```bash
git add backend/src/routes/gameplay.py
git commit -m "fix: refactor start_game to use _enforce_activity_limit

- Uses fresh limit check after increment
- Applies consistent keep_first logic
- Response now contains accurate limit_status

Fixes half of the off-by-one bug."
```

---

## Task 4: Refactor `next_turn` to Use Helper

**Files:**
- Modify: `backend/src/routes/gameplay.py` (next_turn function, lines 938-961)

**Step 4.1: Update next_turn to use the helper**

Find and replace this section (approximately lines 938-961):

**BEFORE (remove this):**
```python
        # SCRUBBER: Check limit and scrub buffer if needed
        limit_status = {}
        if owner_id or anonymous_session_id:
            limit_status = _check_daily_limit(user_id=owner_id, anonymous_session_id=anonymous_session_id)
            if limit_status.get("limit_reached"):
                # If we strictly exceeded the limit (e.g. 26 > 25), block everything immediately.
                # If we strictly HIT the limit (25 == 25), allow the current card (which is the 25th).
                # Note: valid range is 0..25. 25 is the last allowed card.
                # If used=25. We allow queue[0] (C25). We scrub queue[1:] (C26+).
                # If used=26. We block queue[0].

                # Check usage
                used = limit_status.get("used", 0)
                limit = limit_status.get("limit", 25)

                keep_first = True
                if used > limit:
                     keep_first = False

                queue = _scrub_queue_for_limit(queue, keep_first=keep_first)

                state["queue"] = queue
                session.current_turn_state = state
                flag_modified(session, "current_turn_state")
```

**AFTER (replace with):**
```python
        # Enforce limit with fresh check
        limit_status = {}
        if owner_id or anonymous_session_id:
            queue, limit_status = _enforce_activity_limit(
                queue,
                owner_id=owner_id,
                anonymous_session_id=anonymous_session_id
            )

            state["queue"] = queue
            session.current_turn_state = state
            flag_modified(session, "current_turn_state")
```

**Step 4.2: Run all new tests**

Run: `cd backend && python -m pytest tests/test_activity_limit_enforcement.py -v`

Expected: All tests should now PASS

**Step 4.3: Run full test suite**

Run: `cd backend && python -m pytest tests/ -v --ignore=tests/test_recommendations.py`

Expected: All tests pass (ignore recommendations tests if they have external dependencies)

**Step 4.4: Commit next_turn refactor**

```bash
git add backend/src/routes/gameplay.py
git commit -m "fix: refactor next_turn to use _enforce_activity_limit

- Consistent limit enforcement with start_game
- Single source of truth for scrubbing logic

Completes the off-by-one bug fix."
```

---

## Task 5: Add Unit Tests for the Helper

**Files:**
- Modify: `backend/tests/test_activity_limit_enforcement.py`

**Step 5.1: Add unit tests for _enforce_activity_limit**

Append to the test file:

```python
@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
class TestEnforceActivityLimitHelper:
    """Unit tests for the _enforce_activity_limit helper function."""

    def test_helper_returns_fresh_status(self, client, db_session, app, test_activity):
        """Helper returns current limit status, not stale."""
        from src.routes.gameplay import _enforce_activity_limit, _generate_limit_card

        user, _ = create_user_at_count(db_session, count=10)

        # Create a mock queue
        mock_queue = [
            {'card': {'type': 'TRUTH', 'card_id': '1'}},
            {'card': {'type': 'DARE', 'card_id': '2'}},
            {'card': {'type': 'TRUTH', 'card_id': '3'}},
        ]

        queue, status = _enforce_activity_limit(mock_queue, owner_id=str(user.id))

        assert status['used'] == 10
        assert status['limit_reached'] is True

    def test_helper_keep_first_at_exact_limit(self, client, db_session, app, test_activity):
        """At exact limit (used==limit), keep_first should be True."""
        from src.routes.gameplay import _enforce_activity_limit

        user, _ = create_user_at_count(db_session, count=10)  # At limit

        mock_queue = [
            {'card': {'type': 'TRUTH', 'card_id': '1'}},
            {'card': {'type': 'DARE', 'card_id': '2'}},
            {'card': {'type': 'TRUTH', 'card_id': '3'}},
        ]

        queue, status = _enforce_activity_limit(mock_queue, owner_id=str(user.id))

        # First card kept (keep_first=True when used==limit)
        assert queue[0]['card']['type'] == 'TRUTH'
        # Rest scrubbed
        assert queue[1]['card']['type'] == 'LIMIT_REACHED'
        assert queue[2]['card']['type'] == 'LIMIT_REACHED'

    def test_helper_scrub_all_when_over_limit(self, client, db_session, app, test_activity):
        """When over limit (used>limit), keep_first should be False."""
        from src.routes.gameplay import _enforce_activity_limit

        user, _ = create_user_at_count(db_session, count=11)  # Over limit

        mock_queue = [
            {'card': {'type': 'TRUTH', 'card_id': '1'}},
            {'card': {'type': 'DARE', 'card_id': '2'}},
            {'card': {'type': 'TRUTH', 'card_id': '3'}},
        ]

        queue, status = _enforce_activity_limit(mock_queue, owner_id=str(user.id))

        # All scrubbed (keep_first=False when used>limit)
        assert queue[0]['card']['type'] == 'LIMIT_REACHED'
        assert queue[1]['card']['type'] == 'LIMIT_REACHED'
        assert queue[2]['card']['type'] == 'LIMIT_REACHED'

    def test_helper_no_scrub_under_limit(self, client, db_session, app, test_activity):
        """Under limit, no scrubbing should occur."""
        from src.routes.gameplay import _enforce_activity_limit

        user, _ = create_user_at_count(db_session, count=5)  # Under limit

        mock_queue = [
            {'card': {'type': 'TRUTH', 'card_id': '1'}},
            {'card': {'type': 'DARE', 'card_id': '2'}},
            {'card': {'type': 'TRUTH', 'card_id': '3'}},
        ]

        queue, status = _enforce_activity_limit(mock_queue, owner_id=str(user.id))

        # No scrubbing
        assert queue[0]['card']['type'] == 'TRUTH'
        assert queue[1]['card']['type'] == 'DARE'
        assert queue[2]['card']['type'] == 'TRUTH'
        assert status['limit_reached'] is False

    def test_helper_premium_user_no_limit(self, client, db_session, app, test_activity):
        """Premium users should never have limit_reached=True."""
        from src.routes.gameplay import _enforce_activity_limit

        user, _ = create_user_at_count(db_session, count=100, tier='premium')

        mock_queue = [
            {'card': {'type': 'TRUTH', 'card_id': '1'}},
            {'card': {'type': 'DARE', 'card_id': '2'}},
        ]

        queue, status = _enforce_activity_limit(mock_queue, owner_id=str(user.id))

        # No scrubbing for premium
        assert queue[0]['card']['type'] == 'TRUTH'
        assert queue[1]['card']['type'] == 'DARE'
        assert status['limit_reached'] is False
```

**Step 5.2: Run all tests**

Run: `cd backend && python -m pytest tests/test_activity_limit_enforcement.py -v`

Expected: All tests pass

**Step 5.3: Commit unit tests**

```bash
git add backend/tests/test_activity_limit_enforcement.py
git commit -m "test: add unit tests for _enforce_activity_limit helper

Tests cover:
- Fresh status return
- keep_first=True at exact limit
- keep_first=False when over limit
- No scrubbing under limit
- Premium user bypass"
```

---

## Task 6: Add Regression Tests

**Files:**
- Modify: `backend/tests/test_activity_limit_enforcement.py`

**Step 6.1: Add regression tests for edge cases**

Append to the test file:

```python
@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
class TestActivityLimitRegression:
    """Regression tests to prevent the off-by-one bug from returning."""

    def test_user_at_9_gets_exactly_1_more_activity(self, client, db_session, app, test_activity):
        """
        REGRESSION: User at count=9 should get exactly 1 more activity.

        This was the original bug - users were getting 2 more instead of 1.
        """
        user, token = create_user_at_count(db_session, count=9)

        # Start game - this is activity #10 (the last one)
        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        session_id = data['session_id']

        # First card should be real
        assert data['queue'][0]['card']['type'] != 'LIMIT_REACHED'

        # But limit should be reached
        assert data['limit_status']['limit_reached'] is True
        assert data['limit_status']['used'] == 10

        # Next turn should show LIMIT_REACHED
        resp = client.post(
            f'/api/game/{session_id}/next',
            json={},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # Current card should be LIMIT_REACHED
        assert data['queue'][0]['card']['type'] == 'LIMIT_REACHED', \
            "After using last activity, next card must be LIMIT_REACHED"

    def test_multiple_game_sessions_share_count(self, client, db_session, app, test_activity):
        """
        Count persists across game sessions.
        User with count=8 starts game (count->9), ends game, starts new game (count->10).
        """
        user, token = create_user_at_count(db_session, count=8)

        # First game session
        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert resp.status_code == 200

        db_session.refresh(user)
        assert user.lifetime_activity_count == 9

        # Second game session
        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()

        db_session.refresh(user)
        assert user.lifetime_activity_count == 10

        # Should show limit reached
        assert data['limit_status']['limit_reached'] is True

    def test_limit_status_accurate_after_next_turn(self, client, db_session, app, test_activity):
        """limit_status in next_turn response must be accurate."""
        user, token = create_user_at_count(db_session, count=8)

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )
        session_id = resp.get_json()['session_id']

        # First next_turn: count 9 -> 10
        resp = client.post(
            f'/api/game/{session_id}/next',
            json={},
            headers={'Authorization': f'Bearer {token}'}
        )
        data = resp.get_json()

        assert data['limit_status']['used'] == 10
        assert data['limit_status']['limit_reached'] is True
        assert data['limit_status']['remaining'] == 0

    def test_no_charge_for_limit_card(self, client, db_session, app, test_activity):
        """Viewing a LIMIT_REACHED card should not increment count."""
        user, token = create_user_at_count(db_session, count=10)  # At limit

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )
        session_id = resp.get_json()['session_id']

        db_session.refresh(user)
        count_after_start = user.lifetime_activity_count

        # Call next on limit card
        resp = client.post(
            f'/api/game/{session_id}/next',
            json={},
            headers={'Authorization': f'Bearer {token}'}
        )

        db_session.refresh(user)
        assert user.lifetime_activity_count == count_after_start, \
            "Count should not increment when viewing LIMIT_REACHED card"
```

**Step 6.2: Run full test suite**

Run: `cd backend && python -m pytest tests/test_activity_limit_enforcement.py tests/test_gameplay_limits.py tests/test_gameplay_limit_boundary.py -v`

Expected: All tests pass

**Step 6.3: Commit regression tests**

```bash
git add backend/tests/test_activity_limit_enforcement.py
git commit -m "test: add regression tests for activity limit

Prevents off-by-one bug from returning:
- User at 9 gets exactly 1 more
- Count persists across sessions
- Accurate limit_status after next_turn
- No charge for LIMIT_REACHED cards"
```

---

## Task 7: Clean Up Deprecated Aliases

**Files:**
- Modify: `backend/src/routes/gameplay.py`

**Step 7.1: Update callers to use new function names**

Search and replace in gameplay.py:
- `_check_daily_limit` → `_check_activity_limit` (except the alias definition)
- `_increment_daily_count` → `_increment_activity_count` (except the alias definition)

**Step 7.2: Add deprecation warnings to aliases**

Update the alias functions (lines 311-313 and 330-332):

```python
# Alias for backwards compatibility
def _check_daily_limit(user_id: Optional[str] = None, anonymous_session_id: Optional[str] = None) -> dict:
    """Deprecated: Use _check_activity_limit instead."""
    import warnings
    warnings.warn("_check_daily_limit is deprecated, use _check_activity_limit", DeprecationWarning, stacklevel=2)
    return _check_activity_limit(user_id, anonymous_session_id)


# Alias for backwards compatibility
def _increment_daily_count(user_id: str):
    """Deprecated: Use _increment_activity_count instead."""
    import warnings
    warnings.warn("_increment_daily_count is deprecated, use _increment_activity_count", DeprecationWarning, stacklevel=2)
    _increment_activity_count(user_id)
```

**Step 7.3: Run tests**

Run: `cd backend && python -m pytest tests/test_gameplay*.py tests/test_activity_limit_enforcement.py -v`

Expected: All tests pass

**Step 7.4: Commit cleanup**

```bash
git add backend/src/routes/gameplay.py
git commit -m "refactor: update to use non-deprecated function names

- Replace _check_daily_limit with _check_activity_limit
- Replace _increment_daily_count with _increment_activity_count
- Add deprecation warnings to old aliases"
```

---

## Task 8: Final Verification

**Step 8.1: Run complete test suite**

```bash
cd backend && python -m pytest tests/ -v --ignore=tests/test_recommendations.py -x
```

Expected: All tests pass

**Step 8.2: Manual verification checklist**

Verify these scenarios work correctly:
- [ ] Fresh user (count=0) can play exactly 10 activities
- [ ] User at count=9 sees limit_reached=True after starting game
- [ ] User at count=9 gets exactly 1 more activity, then blocked
- [ ] User at count=10 sees all LIMIT_REACHED cards
- [ ] Premium user has no limits
- [ ] Response limit_status always shows accurate (post-increment) values

**Step 8.3: Create final commit with summary**

```bash
git add -A
git status  # Verify no unintended changes
```

If any uncommitted changes, commit them:

```bash
git commit -m "chore: final cleanup for activity limit fix"
```

**Step 8.4: Push branch for review**

```bash
git push -u origin fix/activity-count-off-by-one
```

---

## Summary

This plan implements Option B (Refactor for Consistency) by:

1. **Creating a shared helper** `_enforce_activity_limit()` that encapsulates:
   - Fresh limit status check
   - Consistent `keep_first` logic
   - Queue scrubbing

2. **Updating both endpoints** (`start_game` and `next_turn`) to use the helper

3. **Comprehensive testing**:
   - Failing tests first (TDD)
   - Unit tests for the helper
   - Integration tests via endpoints
   - Regression tests for edge cases

4. **Cleanup** of deprecated function aliases

**Files Modified:**
- `backend/src/routes/gameplay.py` - Add helper, refactor endpoints
- `backend/tests/test_activity_limit_enforcement.py` - New test file

**Estimated Changes:** ~50 lines added, ~40 lines removed/refactored
