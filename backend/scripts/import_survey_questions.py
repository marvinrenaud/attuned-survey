"""Import survey questions from CSV into Supabase database."""
import sys
import csv
import json
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extensions import db
from src.models.survey import SurveyQuestion
from src.main import app


def parse_maps(maps_str: str) -> Optional[Dict]:
    """Parse the maps JSON string from CSV."""
    if not maps_str or maps_str.strip() == '':
        return None
    try:
        return json.loads(maps_str)
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse maps '{maps_str}': {e}")
        return None


def import_questions_from_csv(
    csv_path: str,
    survey_version: str = '0.4',
    clear_existing: bool = False
) -> int:
    """
    Import survey questions from CSV file.
    
    Args:
        csv_path: Path to questions.csv file
        survey_version: Survey version (default '0.4')
        clear_existing: If True, delete existing questions for this version first
    
    Returns:
        Number of questions imported
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    with app.app_context():
        # Clear existing if requested
        if clear_existing:
            deleted = SurveyQuestion.query.filter_by(survey_version=survey_version).delete()
            db.session.commit()
            print(f"Deleted {deleted} existing questions for version {survey_version}")
        
        # Read CSV
        questions = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                question_id = row.get('id', '').strip()
                if not question_id:
                    print(f"Warning: Skipping row {row_num} - missing id")
                    continue
                
                chapter = row.get('chapter', '').strip()
                question_type = row.get('type', '').strip()
                prompt = row.get('prompt', '').strip()
                options = row.get('options', '').strip() or None
                maps_str = row.get('maps', '').strip()
                
                maps_json = parse_maps(maps_str)
                
                questions.append({
                    'question_id': question_id,
                    'survey_version': survey_version,
                    'chapter': chapter,
                    'question_type': question_type,
                    'prompt': prompt,
                    'options': options,
                    'maps': maps_json,
                    'display_order': row_num - 1  # Use CSV row order
                })
        
        # Insert into database with upsert logic
        inserted = 0
        updated = 0
        errors = 0
        
        for q in questions:
            try:
                # Check if question already exists
                existing = SurveyQuestion.query.filter_by(
                    survey_version=q['survey_version'],
                    question_id=q['question_id']
                ).first()
                
                if existing:
                    # Update existing question
                    existing.chapter = q['chapter']
                    existing.question_type = q['question_type']
                    existing.prompt = q['prompt']
                    existing.options = q['options']
                    existing.maps = q['maps']
                    existing.display_order = q['display_order']
                    existing.is_active = True
                    updated += 1
                else:
                    # Create new question
                    question = SurveyQuestion(**q)
                    db.session.add(question)
                    inserted += 1
                    
            except Exception as e:
                print(f"Error inserting question {q['question_id']}: {e}")
                errors += 1
                db.session.rollback()
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✓ Successfully imported {inserted} new questions")
            if updated > 0:
                print(f"✓ Updated {updated} existing questions")
            if errors > 0:
                print(f"⚠️  {errors} errors encountered")
            return inserted + updated
        except Exception as e:
            print(f"\n✗ Commit failed: {e}")
            db.session.rollback()
            raise


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Import survey questions from CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import questions (default: frontend/src/data/questions.csv, version 0.4)
  python import_survey_questions.py
  
  # Import with custom CSV path and version
  python import_survey_questions.py --csv ../frontend/src/data/questions.csv --version 0.4
  
  # Clear existing questions before importing
  python import_survey_questions.py --clear-before
        """
    )
    
    parser.add_argument(
        '--csv',
        type=str,
        default='frontend/src/data/questions.csv',
        help='Path to questions.csv file (default: frontend/src/data/questions.csv)'
    )
    parser.add_argument(
        '--version',
        type=str,
        default='0.4',
        help='Survey version (default: 0.4)'
    )
    parser.add_argument(
        '--clear-before',
        action='store_true',
        help='Clear existing questions for this version before importing'
    )
    
    args = parser.parse_args()
    
    # Resolve CSV path relative to script location
    script_dir = Path(__file__).parent
    csv_path = script_dir.parent / args.csv if not Path(args.csv).is_absolute() else Path(args.csv)
    
    try:
        count = import_questions_from_csv(
            str(csv_path),
            survey_version=args.version,
            clear_existing=args.clear_before
        )
        print(f"\nTotal questions processed: {count}")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

