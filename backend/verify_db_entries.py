from src.main import app, db
from src.models.notification import PushNotificationToken
from src.models.activity_history import UserActivityHistory

def verify_db():
    with app.app_context():
        print("Checking PushNotificationToken...")
        tokens = PushNotificationToken.query.all()
        print(f"Found {len(tokens)} tokens.")
        for t in tokens:
            print(f" - User: {t.user_id}, Token: {t.device_token}, Platform: {t.platform}")

        print("\nChecking UserActivityHistory...")
        history = UserActivityHistory.query.all()
        print(f"Found {len(history)} history records.")
        for h in history:
            print(f" - Session: {h.session_id}, Activity: {h.activity_id}, Feedback: {h.feedback_type}")

if __name__ == "__main__":
    verify_db()
