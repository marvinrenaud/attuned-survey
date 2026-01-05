
import sys
import os
import uuid
import json

# Add backend to path
sys.path.append(os.getcwd())

from backend.src.extensions import db
from backend.src.main import create_app
from backend.src.models.session import Session
from backend.src.models.user import User

def verify_guest_anatomy():
    app = create_app()
    
    with app.app_context():
        # 1. Create a dummy user for the request
        test_user_id = str(uuid.uuid4())
        # We need a user in DB to pass token_required if we were mocking that, 
        # but we can mock the request context directly with a user_id.
        # However, start_game checks if user exists for some logic?
        # Let's create a real user to be safe.
        user = User(
            id=test_user_id,
            email=f"test_{test_user_id[:8]}@example.com",
            display_name="Test Host"
        )
        db.session.add(user)
        db.session.commit()
        
        print(f"Created test user: {test_user_id}")

        # 2. Prepare Request Data
        guest_anatomy_pref = ["vagina"] # Specific pref to test
        payload = {
            "players": [
                {"id": test_user_id, "name": "Host", "anatomy": ["penis"]},
                {
                    "id": str(uuid.uuid4()), 
                    "name": "Guest Partner", 
                    "anatomy": ["vagina"],
                    "anatomy_preference": guest_anatomy_pref
                }
            ],
            "settings": {
                "intimacy_level": 3
            }
        }

        # 3. Call start_game (simulating request)
        # We use test_client to simulate the full request cycle
        client = app.test_client()
        
        # We need to bypass @token_required or mock it. 
        # Since we have a real user, we can generate a token or mock the decorator.
        # Easier: The user.py start_game uses @token_required(current_user_id).
        # We can simulate the auth middleware or just manually invoke the function?
        # Manual invocation is tricky due to `request.get_json()`.
        # Using test_client requires a valid token which implies mocking Supabase or the middleware.
        
        # Let's look at how @token_required works. usually it decodes JWT.
        # If we want to avoid external auth dependencies, we can mock the middleware.
        # BUT, the script is running in a separate process.
        
        # ALTERNATIVE: Use `with app.test_request_context(...)` and manually call the function?
        # Yes, and we can mock the `current_user_id` argument if we call the underlying view function?
        # But `token_required` wraps it.
        
        # Let's assume we can mock the decorator behaviors if we import the module?
        # Or more robust: just insert directly into DB to test logic? 
        # No, we want to test the ENDPOINT logic (parsing request).
        
        # Let's use `app.test_request_context` and Mock the `token_required` decorator? 
        # Too late, it's already decorated.
        
        # We can use a property of the `current_user_id` passed by the decorator.
        # If we can't easily generate a token, let's try to mock `backend.src.middleware.auth.token_required`.
        # But `gameplay` imports it at top level.
        
        # Let's try this: Manually call `start_game.__wrapped__(current_user_id=test_user_id)`?
        # Does Flask decorators expose __wrapped__? Often yes.
        pass

    # Re-import to patch not possible easily.
    # Let's try to simulate the request and see if we can just pass a dummy header if we are in dev/test mode?
    # Or just rely on the fact that we can call the function if we strip the decorator.
    
    from backend.src.routes.gameplay import start_game
    
    # Check if we can unwrap
    if hasattr(start_game, '__wrapped__'):
         print("Calling unwrapped start_game function directly...")
         with app.test_request_context('/api/game/start', method='POST', json=payload):
             # start_game(current_user_id)
             response = start_game.__wrapped__(test_user_id)
             
             # Response is a tuple or response object?
             # Flask return: jsonify(...) which is a Response object
             if hasattr(response, 'get_json'):
                 data = response.get_json()
             else:
                 # verify if it's a tuple (response, status)
                 if isinstance(response, tuple):
                     data = response[0].get_json()
                 else:
                     data = response.get_json()
                     
             print(f"Response: {data}")
             
             if "session_id" not in data:
                 print("FAILED: No session_id returned")
                 return

             session_id = data["session_id"]
             
             # Verify DB State
             session = Session.query.get(session_id)
             players = session.players
             guest = players[1] # 2nd player
             
             print(f"Guest Data in DB: {guest}")
             
             saved_pref = guest.get('anatomy_preference')
             if saved_pref == guest_anatomy_pref:
                 print("SUCCESS: Anatomy preference saved correctly!")
             else:
                 print(f"FAILED: Expected {guest_anatomy_pref}, got {saved_pref}")

    else:
        print("Could not unwrap start_game. Test cannot proceed without auth mock.")

if __name__ == "__main__":
    verify_guest_anatomy()
