
import sys
import os

# Ensure backend src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main import create_app, db
from src.models.user import User
from src.models.profile import Profile
from src.models.compatibility import Compatibility
from src.routes.partners import PartnerConnection
from src.compatibility.calculator import calculate_compatibility
from datetime import datetime
from sqlalchemy import or_

def backfill_compatibility():
    """
    Backfill compatibility scores for all existing accepted connections
    that don't have a corresponding compatibility_results record.
    """
    app = create_app()
    
    with app.app_context():
        print("Starting compatibility backfill...")
        
        # 1. Get all accepted connections
        connections = PartnerConnection.query.filter_by(status='accepted').all()
        print(f"Found {len(connections)} accepted connections.")
        
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for conn in connections:
            try:
                # Resolve User IDs (Conn stores strings, we need UUIDs or Profiles via User)
                requester_id = conn.requester_user_id
                recipient_id = conn.recipient_user_id
                
                if not requester_id or not recipient_id:
                    print(f"Skipping connection {conn.id}: Missing user IDs")
                    skipped_count += 1
                    continue
                    
                # Get Profiles
                # Note: UUID conversion happens implicitly or we cast if needed. 
                # Profile.user_id is UUID type usually.
                req_profile = Profile.query.filter_by(user_id=requester_id).order_by(Profile.created_at.desc()).first()
                rec_profile = Profile.query.filter_by(user_id=recipient_id).order_by(Profile.created_at.desc()).first()
                
                if not req_profile or not rec_profile:
                    print(f"Skipping connection {conn.id}: One or both profiles missing")
                    skipped_count += 1
                    continue
                
                # Determine IDs for compatibility table (ordered)
                if req_profile.id < rec_profile.id:
                    p1_id, p2_id = req_profile.id, rec_profile.id
                else:
                    p1_id, p2_id = rec_profile.id, req_profile.id
                    
                # Check existance
                exists = Compatibility.query.filter_by(player_a_id=p1_id, player_b_id=p2_id).first()
                if exists:
                    # Optional: Force update? For now, skip if exists to be safe/fast.
                    skipped_count += 1
                    continue
                
                # Calculate
                print(f"Calculating for connection {conn.id} (Profiles {p1_id}, {p2_id})...")
                result = calculate_compatibility(req_profile.to_dict(), rec_profile.to_dict())
                
                # Store
                compat_record = Compatibility(
                    player_a_id=p1_id,
                    player_b_id=p2_id,
                    overall_score=float(result['overall_compatibility']['score']) / 100.0,
                    overall_percentage=int(result['overall_compatibility']['score']),
                    interpretation=result['overall_compatibility']['interpretation'],
                    breakdown=result['breakdown'],
                    mutual_activities=result['mutual_activities'],
                    growth_opportunities=result['growth_opportunities'],
                    mutual_truth_topics=result['mutual_truth_topics'],
                    blocked_activities=result['blocked_activities'],
                    boundary_conflicts=result['boundary_conflicts'],
                    calculation_version=result['compatibility_version'],
                    created_at=datetime.utcnow()
                )
                
                db.session.add(compat_record)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing connection {conn.id}: {str(e)}")
                error_count += 1
                
        # Commit all changes
        try:
            db.session.commit()
            print("Backfill complete!")
            print(f"Processed (New): {processed_count}")
            print(f"Skipped (Exists/Invalid): {skipped_count}")
            print(f"Errors: {error_count}")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to commit changes: {str(e)}")

if __name__ == "__main__":
    backfill_compatibility()
