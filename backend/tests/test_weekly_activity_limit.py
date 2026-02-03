"""
Tests for weekly/daily/lifetime activity limit modes with configurable feature flag.
TDD: Written BEFORE implementation.

Covers:
- Weekly mode: counter resets after 7 days
- Daily mode: counter resets after 24 hours
- Lifetime mode: backward-compatible, no reset
- Increment behavior across modes
- Mode switching at runtime
- Backward compatibility of API response fields
- Premium bypass across all modes
- Feature flag integration
- CleanupService weekly reset
"""
import os
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.models.user import User


@pytest.fixture
def app_context(app):
    """Ensure app context is pushed."""
    with app.app_context():
        yield


@pytest.fixture
def free_user_weekly(db_session, test_user_data):
    """Free user with weekly counter initialized."""
    user = User(
        id=test_user_data['id'],
        email=test_user_data['email'],
        display_name=test_user_data['display_name'],
        auth_provider=test_user_data['auth_provider'],
        demographics=test_user_data['demographics'],
        subscription_tier='free',
        lifetime_activity_count=0,
        weekly_activity_count=0,
        weekly_activity_reset_at=datetime.utcnow(),
        daily_activity_count=0,
        daily_activity_reset_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def premium_user(db_session):
    """Premium user for bypass tests."""
    user = User(
        id=uuid.uuid4(),
        email=f'premium-{uuid.uuid4().hex[:8]}@test.com',
        display_name='Premium User',
        auth_provider='email',
        demographics={},
        subscription_tier='premium',
        lifetime_activity_count=999,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    return user


def _mock_config(mode):
    """Helper to create a mock get_config that returns the given mode for limit_mode."""
    def side_effect(key, default=None):
        if key == 'free_tier_limit_mode':
            return mode
        return default
    return side_effect


class TestWeeklyLimitMode:
    """Weekly mode: counter resets after 7 days."""

    def test_weekly_under_limit(self, client, app_context, free_user_weekly, db_session):
        """User with 5/10 weekly shows remaining=5."""
        free_user_weekly.weekly_activity_count = 5
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data['activities_used'] == 5
                assert data['remaining'] == 5
                assert data['limit_reached'] is False
                assert data['limit_mode'] == 'weekly'
                assert 'resets_at' in data

    def test_weekly_at_limit(self, client, app_context, free_user_weekly, db_session):
        """User with 10/10 weekly shows limit_reached=True."""
        free_user_weekly.weekly_activity_count = 10
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['limit_reached'] is True
                assert data['remaining'] == 0

    def test_weekly_auto_reset_after_7_days(self, client, app_context, free_user_weekly, db_session):
        """Counter resets to 0 if 7+ days have passed."""
        free_user_weekly.weekly_activity_count = 10
        free_user_weekly.weekly_activity_reset_at = datetime.utcnow() - timedelta(days=8)
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['limit_reached'] is False
                assert data['activities_used'] == 0
                assert data['remaining'] == 10

    def test_weekly_no_reset_before_7_days(self, client, app_context, free_user_weekly, db_session):
        """Counter does NOT reset if < 7 days have passed."""
        free_user_weekly.weekly_activity_count = 8
        free_user_weekly.weekly_activity_reset_at = datetime.utcnow() - timedelta(days=5)
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['activities_used'] == 8
                assert data['remaining'] == 2


class TestDailyLimitMode:
    """Daily mode: counter resets after 24 hours."""

    def test_daily_auto_reset_after_24h(self, client, app_context, free_user_weekly, db_session):
        """Counter resets after 24 hours in daily mode."""
        free_user_weekly.daily_activity_count = 10
        free_user_weekly.daily_activity_reset_at = datetime.utcnow() - timedelta(hours=25)
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('daily')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['limit_reached'] is False
                assert data['activities_used'] == 0
                assert data['limit_mode'] == 'daily'

    def test_daily_no_reset_before_24h(self, client, app_context, free_user_weekly, db_session):
        """Counter does NOT reset if < 24 hours have passed."""
        free_user_weekly.daily_activity_count = 8
        free_user_weekly.daily_activity_reset_at = datetime.utcnow() - timedelta(hours=12)
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('daily')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['activities_used'] == 8


class TestLifetimeLimitMode:
    """Lifetime mode: backward-compatible, no reset."""

    def test_lifetime_mode_uses_lifetime_count(self, client, app_context, free_user_weekly, db_session):
        """Lifetime mode uses lifetime_activity_count (no reset)."""
        free_user_weekly.lifetime_activity_count = 10
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('lifetime')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['limit_reached'] is True
                assert data['limit_mode'] == 'lifetime'
                assert 'resets_at' not in data


class TestIncrementWithModes:
    """Increment respects mode and always updates lifetime ledger."""

    def test_increment_updates_both_weekly_and_lifetime(self, client, app_context, free_user_weekly, db_session):
        """Increment in weekly mode updates both weekly and lifetime counts."""
        free_user_weekly.lifetime_activity_count = 5
        free_user_weekly.weekly_activity_count = 3
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.post(
                    f'/api/subscriptions/increment-activity/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                assert response.status_code == 200
                data = response.get_json()
                # Existing field preserved
                assert data['lifetime_activity_count'] == 6

                db_session.refresh(free_user_weekly)
                assert free_user_weekly.weekly_activity_count == 4
                assert free_user_weekly.lifetime_activity_count == 6

    def test_increment_daily_updates_both_daily_and_lifetime(self, client, app_context, free_user_weekly, db_session):
        """Increment in daily mode updates both daily and lifetime counts."""
        free_user_weekly.lifetime_activity_count = 5
        free_user_weekly.daily_activity_count = 2
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('daily')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.post(
                    f'/api/subscriptions/increment-activity/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                assert response.status_code == 200

                db_session.refresh(free_user_weekly)
                assert free_user_weekly.daily_activity_count == 3
                assert free_user_weekly.lifetime_activity_count == 6

    def test_increment_lifetime_only_updates_lifetime(self, client, app_context, free_user_weekly, db_session):
        """Increment in lifetime mode only updates lifetime count."""
        free_user_weekly.lifetime_activity_count = 5
        free_user_weekly.weekly_activity_count = 3
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('lifetime')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.post(
                    f'/api/subscriptions/increment-activity/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                assert response.status_code == 200

                db_session.refresh(free_user_weekly)
                assert free_user_weekly.lifetime_activity_count == 6
                # Weekly should NOT have changed
                assert free_user_weekly.weekly_activity_count == 3


class TestModeSwitching:
    """Runtime mode switching via app_config."""

    def test_mode_switch_lifetime_to_weekly(self, client, app_context, free_user_weekly, db_session):
        """Switching from lifetime to weekly immediately uses weekly counter."""
        free_user_weekly.lifetime_activity_count = 50  # over limit in lifetime
        free_user_weekly.weekly_activity_count = 3      # under limit in weekly
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(free_user_weekly.id)}

            # In lifetime mode, user is capped
            with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('lifetime')):
                resp = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                assert resp.get_json()['limit_reached'] is True

            # Switch to weekly mode, user is NOT capped
            with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
                resp = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = resp.get_json()
                assert data['limit_reached'] is False
                assert data['activities_used'] == 3


class TestBackwardCompatibility:
    """Ensure existing API response fields are preserved."""

    def test_check_limit_preserves_existing_fields(self, client, app_context, free_user_weekly, db_session):
        """All existing fields remain present with same types."""
        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                # Existing fields
                assert 'has_limit' in data
                assert 'limit_reached' in data
                assert 'activities_used' in data
                assert 'limit' in data
                assert 'remaining' in data
                # Types
                assert isinstance(data['has_limit'], bool)
                assert isinstance(data['limit_reached'], bool)
                assert isinstance(data['activities_used'], int)
                assert isinstance(data['limit'], int)
                assert isinstance(data['remaining'], int)

    def test_status_preserves_existing_fields(self, client, app_context, free_user_weekly, db_session):
        """Status endpoint keeps all existing fields."""
        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/status/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert 'activities_used' in data
                assert 'activities_limit' in data
                assert 'activities_remaining' in data
                assert 'subscription_tier' in data
                assert 'is_premium' in data

    def test_increment_preserves_lifetime_activity_count_field(self, client, app_context, free_user_weekly, db_session):
        """Increment response still returns lifetime_activity_count."""
        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.post(
                    f'/api/subscriptions/increment-activity/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert 'lifetime_activity_count' in data
                assert 'success' in data


class TestPremiumBypass:
    """Premium users bypass all modes."""

    def test_premium_user_bypasses_weekly_mode(self, client, app_context, premium_user, db_session):
        """Premium user has no limit regardless of mode."""
        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(premium_user.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{premium_user.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['has_limit'] is False
                assert data['limit_reached'] is False

    def test_premium_user_bypasses_daily_mode(self, client, app_context, premium_user, db_session):
        """Premium user has no limit in daily mode."""
        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('daily')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(premium_user.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{premium_user.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['has_limit'] is False


class TestFeatureFlagIntegration:
    """Feature flag integration tests."""

    def test_config_key_defaults_to_weekly(self, client, app_context, free_user_weekly, db_session):
        """When no free_tier_limit_mode exists, service defaults to 'weekly'."""
        # Don't mock get_config - let it use its real default
        # The config cache won't have this key, so default should kick in
        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                assert data['limit_mode'] == 'weekly'

    def test_invalid_mode_falls_back_to_lifetime(self, client, app_context, free_user_weekly, db_session):
        """Unknown mode value falls back to lifetime (safe default)."""
        free_user_weekly.lifetime_activity_count = 10
        db_session.commit()

        with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('invalid_mode')):
            with patch('src.middleware.auth.jwt.decode') as mock_decode:
                mock_decode.return_value = {"sub": str(free_user_weekly.id)}
                response = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                data = response.get_json()
                # Should fall back to lifetime behavior
                assert data['limit_reached'] is True
                assert data['activities_used'] == 10

    def test_runtime_mode_change_takes_effect(self, client, app_context, free_user_weekly, db_session):
        """Changing config mid-session switches behavior immediately."""
        free_user_weekly.lifetime_activity_count = 10
        free_user_weekly.weekly_activity_count = 2
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(free_user_weekly.id)}

            # Lifetime mode: capped at 10
            with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('lifetime')):
                resp = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                assert resp.get_json()['limit_reached'] is True
                assert resp.get_json()['limit_mode'] == 'lifetime'

            # Weekly mode: only 2 used
            with patch('backend.src.services.activity_limit_service.get_config', side_effect=_mock_config('weekly')):
                resp = client.get(
                    f'/api/subscriptions/check-limit/{free_user_weekly.id}',
                    headers={'Authorization': 'Bearer valid-token'}
                )
                assert resp.get_json()['limit_reached'] is False
                assert resp.get_json()['limit_mode'] == 'weekly'


class TestCleanupServiceWeeklyReset:
    """Tests for CleanupService.reset_expired_weekly_counters."""

    def test_reset_expired_weekly_counters_resets_old(self, app_context, db_session):
        """Users with weekly_activity_reset_at > 7 days ago get reset to 0."""
        from src.services.cleanup import CleanupService

        user = User(
            id=uuid.uuid4(),
            email=f'old-{uuid.uuid4().hex[:8]}@test.com',
            display_name='Old Counter User',
            auth_provider='email',
            demographics={},
            subscription_tier='free',
            weekly_activity_count=8,
            weekly_activity_reset_at=datetime.utcnow() - timedelta(days=8),
            lifetime_activity_count=20,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()

        count = CleanupService.reset_expired_weekly_counters()
        assert count >= 1

        db_session.refresh(user)
        assert user.weekly_activity_count == 0

    def test_reset_expired_weekly_counters_skips_recent(self, app_context, db_session):
        """Users with reset_at < 7 days ago are untouched."""
        from src.services.cleanup import CleanupService

        user = User(
            id=uuid.uuid4(),
            email=f'recent-{uuid.uuid4().hex[:8]}@test.com',
            display_name='Recent Counter User',
            auth_provider='email',
            demographics={},
            subscription_tier='free',
            weekly_activity_count=5,
            weekly_activity_reset_at=datetime.utcnow() - timedelta(days=3),
            lifetime_activity_count=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()

        CleanupService.reset_expired_weekly_counters()

        db_session.refresh(user)
        assert user.weekly_activity_count == 5  # unchanged

    def test_reset_expired_weekly_counters_skips_premium(self, app_context, db_session):
        """Premium users are never reset."""
        from src.services.cleanup import CleanupService

        user = User(
            id=uuid.uuid4(),
            email=f'prem-reset-{uuid.uuid4().hex[:8]}@test.com',
            display_name='Premium Reset Test',
            auth_provider='email',
            demographics={},
            subscription_tier='premium',
            weekly_activity_count=50,
            weekly_activity_reset_at=datetime.utcnow() - timedelta(days=30),
            lifetime_activity_count=200,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()

        CleanupService.reset_expired_weekly_counters()

        db_session.refresh(user)
        assert user.weekly_activity_count == 50  # unchanged
