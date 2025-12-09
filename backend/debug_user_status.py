
import sys
import os
from datetime import datetime

# Add the backend directory to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.main import create_app
from src.extensions import db
from src.models.user import User
from src.models.profile import Profile

app = create_app()

def debug_user_status(user_id):
    with app.app_context():
        print(f"Inspecting User ID: {user_id}")
        
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            print("User not found!")
            return
            
        print("\n--- User Table ---")
        print(f"Display Name: {user.display_name}")
        print(f"Email: {user.email}")
        print(f"Onboarding Completed: {user.onboarding_completed}")
        print(f"Profile Completed: {user.profile_completed}")
        print(f"Demographics: {user.demographics}")
        print(f"Anatomy (Has): P={user.has_penis}, V={user.has_vagina}, B={user.has_breasts}")
        print(f"Anatomy (Likes): P={user.likes_penis}, V={user.likes_vagina}, B={user.likes_breasts}")
        
        print("\n--- Profile Table (Survey Results) ---")
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            print(f"Profile Exists: Yes")
            print(f"Activities Count: {len(profile.activities) if profile.activities else 0}")
            print(f"Created At: {profile.created_at}")
        else:
            print("Profile Exists: No")

if __name__ == "__main__":
    target_user_id = '90c0c048-951c-44a4-b90a-a77272362d8a'
    debug_user_status(target_user_id)
