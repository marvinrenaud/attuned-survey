"""
Upgrade a user's subscription tier.

Usage:
    python backend/scripts/upgrade_user_subscription.py --display-name "D" --tier premium
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.extensions import db
from backend.src.main import create_app
from backend.src.models.user import User


def upgrade_subscription(display_name: str, tier: str):
    """Upgrade a user's subscription tier by display name."""
    app = create_app()

    with app.app_context():
        # Find user by display name
        user = User.query.filter(User.display_name == display_name).first()

        if not user:
            print(f"Error: User with display_name '{display_name}' not found")
            # List all users for debugging
            all_users = User.query.all()
            print(f"\nAvailable users ({len(all_users)}):")
            for u in all_users:
                print(f"  - {u.display_name} ({u.email}) - tier: {u.subscription_tier}")
            return False

        old_tier = user.subscription_tier
        user.subscription_tier = tier
        db.session.commit()

        print(f"Successfully upgraded user:")
        print(f"  Display Name: {user.display_name}")
        print(f"  Email: {user.email}")
        print(f"  Subscription: {old_tier} -> {tier}")
        return True


def main():
    parser = argparse.ArgumentParser(description='Upgrade user subscription')
    parser.add_argument('--display-name', '-n', required=True, help='User display name')
    parser.add_argument('--tier', '-t', default='premium', choices=['free', 'premium'], help='Subscription tier')

    args = parser.parse_args()

    success = upgrade_subscription(args.display_name, args.tier)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
