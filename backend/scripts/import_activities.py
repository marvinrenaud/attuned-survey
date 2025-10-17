"""Import activities from CSV spreadsheet to database with AI-enriched metadata."""
import sys
import os
import csv
import json
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


def load_enriched_data(enriched_json_path):
    """Load AI-enriched activity metadata from JSON file."""
    if not os.path.exists(enriched_json_path):
        print(f"⚠️  No enriched data found at {enriched_json_path}")
        print("   Activities will be imported without AI tags")
        return {}
    
    with open(enriched_json_path, 'r') as f:
        enriched = json.load(f)
    
    print(f"✓ Loaded enriched data for {len(enriched)} activities")
    return enriched


def parse_activity_row(row, row_num, enriched_data=None):
    """Parse a single row from the CSV into activity data with optional AI enrichment."""
    # Expected columns:
    # Activity Type, Activity Description, Intimacy Level, Intimacy Rating, Audience Tag
    
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
    script = {
        "steps": [
            {
                "actor": "A",  # Will be assigned dynamically during generation
                "do": description
            }
        ]
    }
    
    # Base activity data
    activity_data = {
        'type': activity_type,
        'rating': rating,
        'intensity': intensity,
        'script': script,
        'tags': tags,
        'source': 'bank',
        'approved': True,
        'hard_limit_keys': [],
    }
    
    # Add AI-enriched metadata if available
    if enriched_data:
        row_id = str(row_num - 1)  # Enrichment uses 1-indexed row_id
        if row_id in enriched_data:
            enrichment = enriched_data[row_id]
            activity_data['power_role'] = enrichment.get('power_role')
            activity_data['preference_keys'] = enrichment.get('preference_keys', [])
            activity_data['domains'] = enrichment.get('domains', [])
            activity_data['intensity_modifiers'] = enrichment.get('intensity_modifiers', [])
            activity_data['requires_consent_negotiation'] = enrichment.get('requires_consent_negotiation', False)
    
    return activity_data, None


def import_activities_from_csv(csv_path, clear_existing=False, enriched_json_path=None):
    """
    Import activities from CSV file into database with AI-enriched metadata.
    
    Args:
        csv_path: Path to activities CSV
        clear_existing: Clear existing bank activities first
        enriched_json_path: Path to enriched_activities.json (optional)
    """
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return False
    
    # Load enriched data if provided
    enriched_data = {}
    if enriched_json_path:
        enriched_data = load_enriched_data(enriched_json_path)
    else:
        # Auto-detect enriched_activities.json in same directory
        auto_path = Path(__file__).parent / 'enriched_activities.json'
        if auto_path.exists():
            enriched_data = load_enriched_data(str(auto_path))
    
    with app.app_context():
        # Optionally clear existing bank activities
        if clear_existing:
            print("Clearing existing bank activities...")
            Activity.query.filter_by(source='bank').delete()
            db.session.commit()
            print("✓ Cleared existing activities")
        
        # Read CSV
        imported_count = 0
        enriched_count = 0
        error_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                activity_data, error = parse_activity_row(row, row_num, enriched_data)
                
                if error:
                    print(f"⚠️  Row {row_num}: {error}")
                    error_count += 1
                    continue
                
                # Track if enriched
                if activity_data.get('power_role'):
                    enriched_count += 1
                
                # Create activity
                activity = Activity(**activity_data)
                db.session.add(activity)
                imported_count += 1
                
                # Commit in batches of 50
                if imported_count % 50 == 0:
                    db.session.commit()
                    print(f"  Imported {imported_count} activities ({enriched_count} with AI tags)...")
        
        # Final commit
        db.session.commit()
        
        print(f"\n✅ Import complete!")
        print(f"  Imported: {imported_count} activities")
        print(f"  With AI tags: {enriched_count} activities")
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
        
        # Show power role distribution if enriched
        if enriched_count > 0:
            print("\nPower Roles:")
            for role in ['top', 'bottom', 'switch', 'neutral']:
                count = Activity.query.filter_by(power_role=role).count()
                if count > 0:
                    print(f"  {role.capitalize()}: {count}")
        
        return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Import activities from CSV with AI-enriched metadata')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--clear', action='store_true', help='Clear existing bank activities before import')
    parser.add_argument('--enriched', '-e', help='Path to enriched_activities.json (auto-detects if not specified)')
    
    args = parser.parse_args()
    
    success = import_activities_from_csv(
        args.csv_file, 
        clear_existing=args.clear,
        enriched_json_path=args.enriched
    )
    sys.exit(0 if success else 1)

