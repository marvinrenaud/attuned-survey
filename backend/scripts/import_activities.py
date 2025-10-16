"""Import activities from CSV spreadsheet to database."""
import sys
import os
import csv
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extensions import db
from src.models.activity import Activity
from src.main import app


# Mapping from intimacy levels to intensity and rating
INTIMACY_LEVEL_MAP = {
    'L1': {'intensity': 1, 'rating': 'G'},
    'L2': {'intensity': 1, 'rating': 'G'},
    'L3': {'intensity': 1, 'rating': 'G'},
    'L4': {'intensity': 2, 'rating': 'R'},
    'L5': {'intensity': 3, 'rating': 'R'},
    'L6': {'intensity': 3, 'rating': 'R'},
    'L7': {'intensity': 4, 'rating': 'R'},
    'L8': {'intensity': 4, 'rating': 'X'},
    'L9': {'intensity': 5, 'rating': 'X'},
}


def parse_activity_row(row):
    """Parse a single row from the CSV into activity data."""
    # Expected columns:
    # Activity Type, Activity Description, Audience Tag, Intimacy Level
    
    activity_type = row.get('Activity Type', '').strip().lower()
    description = row.get('Activity Description', '').strip()
    audience_tag = row.get('Audience Tag', '').strip().lower()
    intimacy_level = row.get('Intimacy Level', '').strip().upper()
    
    # Validate activity type
    if activity_type not in ['truth', 'dare']:
        return None, f"Invalid activity type: {activity_type}"
    
    # Validate description
    if not description:
        return None, "Missing activity description"
    
    # Map intimacy level to intensity and rating
    if intimacy_level not in INTIMACY_LEVEL_MAP:
        return None, f"Invalid intimacy level: {intimacy_level}"
    
    mapping = INTIMACY_LEVEL_MAP[intimacy_level]
    intensity = mapping['intensity']
    rating = mapping['rating']
    
    # Build tags
    tags = []
    if audience_tag:
        tags.append(audience_tag)
    
    # Build script format
    # For now, simple format with generic actors
    # TODO: Enhance with proper actor assignment based on activity type
    script = {
        "steps": [
            {
                "actor": "A",  # Will be assigned dynamically during generation
                "do": description
            }
        ]
    }
    
    activity_data = {
        'type': activity_type,
        'rating': rating,
        'intensity': intensity,
        'script': script,
        'tags': tags,
        'source': 'bank',
        'approved': True,
        'hard_limit_keys': [],  # TODO: Add if needed
    }
    
    return activity_data, None


def import_activities_from_csv(csv_path, clear_existing=False):
    """Import activities from CSV file into database."""
    
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return False
    
    with app.app_context():
        # Optionally clear existing bank activities
        if clear_existing:
            print("Clearing existing bank activities...")
            Activity.query.filter_by(source='bank').delete()
            db.session.commit()
            print("✓ Cleared existing activities")
        
        # Read CSV
        imported_count = 0
        error_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                activity_data, error = parse_activity_row(row)
                
                if error:
                    print(f"⚠️  Row {row_num}: {error}")
                    error_count += 1
                    continue
                
                # Create activity
                activity = Activity(**activity_data)
                db.session.add(activity)
                imported_count += 1
                
                # Commit in batches of 50
                if imported_count % 50 == 0:
                    db.session.commit()
                    print(f"  Imported {imported_count} activities...")
        
        # Final commit
        db.session.commit()
        
        print(f"\n✅ Import complete!")
        print(f"  Imported: {imported_count} activities")
        print(f"  Errors: {error_count}")
        
        # Show summary by type/rating/intensity
        print("\nSummary:")
        for activity_type in ['truth', 'dare']:
            count = Activity.query.filter_by(type=activity_type).count()
            print(f"  {activity_type.capitalize()}: {count}")
        
        for rating in ['G', 'R', 'X']:
            count = Activity.query.filter_by(rating=rating).count()
            print(f"  {rating}-rated: {count}")
        
        for intensity in range(1, 6):
            count = Activity.query.filter_by(intensity=intensity).count()
            print(f"  Intensity {intensity}: {count}")
        
        return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Import activities from CSV')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--clear', action='store_true', help='Clear existing bank activities before import')
    
    args = parser.parse_args()
    
    success = import_activities_from_csv(args.csv_file, clear_existing=args.clear)
    sys.exit(0 if success else 1)

