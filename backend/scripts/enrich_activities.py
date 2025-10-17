"""
Batch enrichment script to analyze activities with Groq and extract tags.
Processes activities from CSV, calls AI analyzer, saves results with resume capability.
"""
import sys
import os
import csv
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.activity_analyzer import analyze_activity, batch_analyze_activities, get_fallback_tags


def load_activities_from_csv(csv_path):
    """Load activities from CSV file."""
    activities = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            activity = {
                'row_id': row_num - 1,  # 1-indexed
                'type': row.get('Activity Type', '').strip().lower(),
                'description': row.get('Activity Description', '').strip(),
                'intimacy_level': row.get('Intimacy Level', '').strip(),
                'intimacy_rating': row.get('Intimacy Rating', '').strip(),
                'audience_tag': row.get('Audience Tag', '').strip().lower()
            }
            
            if activity['type'] and activity['description']:
                activities.append(activity)
    
    return activities


def save_enrichment_results(results, output_path):
    """Save enrichment results to JSON file."""
    # Ensure directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"✓ Saved results to {output_path}")


def load_enrichment_results(output_path):
    """Load existing enrichment results (for resume)."""
    if not os.path.exists(output_path):
        return {}
    
    with open(output_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def enrich_activities_batch(
    csv_path,
    output_path=None,
    limit=None,
    resume_from=None,
    use_ai=True,
    dry_run=False,
    batch_size=10,
    save_every=50
):
    """
    Enrich activities from CSV with AI-generated tags.
    
    Args:
        csv_path: Path to consolidated activities CSV
        output_path: Where to save enrichment results (default: enriched_activities.json)
        limit: Optional limit on number to process (for testing)
        resume_from: Resume from this row number (for interrupted runs)
        use_ai: Use Groq AI (if False, use keyword fallback only)
        dry_run: Preview only, don't call AI or save results
        batch_size: Activities per Groq batch
        save_every: Save progress every N activities
    
    Returns:
        Dict of enrichment results keyed by row_id
    """
    if output_path is None:
        # Save in scripts directory
        output_path = Path(__file__).parent / 'enriched_activities.json'
    
    output_path = Path(output_path).resolve()
    
    print("=" * 70)
    print("Activity Enrichment Script")
    print("=" * 70)
    print()
    print(f"CSV: {csv_path}")
    print(f"Output: {output_path}")
    print(f"AI Mode: {'Groq' if use_ai else 'Keyword fallback only'}")
    print(f"Dry run: {dry_run}")
    print()
    
    # Load activities
    print("Loading activities from CSV...")
    activities = load_activities_from_csv(csv_path)
    print(f"✓ Loaded {len(activities)} activities")
    print()
    
    # Load existing results (for resume)
    existing_results = load_enrichment_results(output_path) if not dry_run else {}
    
    if existing_results:
        print(f"Found {len(existing_results)} existing enrichments")
        print("Will skip already-processed activities")
        print()
    
    # Filter activities to process
    to_process = []
    for activity in activities:
        row_id = str(activity['row_id'])
        
        # Skip if already enriched
        if row_id in existing_results:
            continue
        
        # Skip if before resume point
        if resume_from and activity['row_id'] < resume_from:
            continue
        
        # Stop if limit reached
        if limit and len(to_process) >= limit:
            break
        
        to_process.append(activity)
    
    if not to_process:
        print("✓ All activities already enriched!")
        return existing_results
    
    print(f"Will process {len(to_process)} activities")
    
    if dry_run:
        print("\n[DRY RUN] Showing first 5 activities that would be processed:")
        for activity in to_process[:5]:
            print(f"  Row {activity['row_id']}: {activity['type']} - {activity['description'][:60]}...")
        print()
        print(f"[DRY RUN] Would process {len(to_process)} total activities")
        return {}
    
    print()
    print("Starting enrichment...")
    print("─" * 70)
    
    # Process activities
    results = existing_results.copy()
    processed_count = 0
    start_time = time.time()
    
    for i, activity in enumerate(to_process):
        row_id = activity['row_id']
        
        # Progress indicator
        if (i + 1) % 10 == 0 or i == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(to_process) - i - 1) / rate if rate > 0 else 0
            print(f"Progress: {i + 1}/{len(to_process)} ({(i+1)/len(to_process)*100:.1f}%) | "
                  f"{rate:.1f} activities/sec | ETA: {eta/60:.1f} min")
        
        # Analyze activity
        if use_ai:
            enrichment = analyze_activity(
                activity['description'],
                activity['type'],
                activity['intimacy_level'],
                row_id
            )
            
            # Fallback if AI fails
            if not enrichment:
                print(f"  ⚠️  AI failed for row {row_id}, using keyword fallback")
                enrichment = get_fallback_tags(activity['description'], activity['type'])
        else:
            # Use keyword fallback only
            enrichment = get_fallback_tags(activity['description'], activity['type'])
        
        # Store result
        results[str(row_id)] = {
            **activity,
            **enrichment,
            'enriched_at': datetime.utcnow().isoformat()
        }
        
        processed_count += 1
        
        # Save progress periodically
        if processed_count % save_every == 0:
            save_enrichment_results(results, output_path)
            print(f"  💾 Progress saved ({len(results)} total enrichments)")
        
        # Rate limiting between requests (if using AI)
        if use_ai and i < len(to_process) - 1:
            time.sleep(0.5)  # 0.5s between individual requests
    
    # Final save
    save_enrichment_results(results, output_path)
    
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"✅ Enrichment complete!")
    print(f"   Processed: {processed_count} activities")
    print(f"   Total enriched: {len(results)} activities")
    print(f"   Time: {elapsed/60:.1f} minutes")
    print(f"   Rate: {processed_count/elapsed:.1f} activities/second")
    print("=" * 70)
    
    return results


def show_sample_results(results, count=5):
    """Show sample enrichment results."""
    print("\nSample enrichment results:")
    print("─" * 70)
    
    sample_keys = list(results.keys())[:count]
    
    for key in sample_keys:
        result = results[key]
        print(f"\nRow {result['row_id']}: {result['type'].upper()}")
        print(f"  Description: {result['description'][:60]}...")
        print(f"  Power role: {result.get('power_role', 'N/A')}")
        print(f"  Preferences: {', '.join(result.get('preference_keys', []))}")
        print(f"  Domains: {', '.join(result.get('domains', []))}")
        print(f"  Modifiers: {', '.join(result.get('intensity_modifiers', []))}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich activities with AI-generated tags')
    parser.add_argument('csv_file', help='Path to consolidated activities CSV')
    parser.add_argument('--output', '-o', help='Output JSON file path', 
                       default=None)  # Will use scripts/enriched_activities.json if not specified
    parser.add_argument('--limit', '-l', type=int, help='Limit number to process (for testing)')
    parser.add_argument('--resume-from', '-r', type=int, help='Resume from row number')
    parser.add_argument('--no-ai', action='store_true', help='Use keyword fallback only (no Groq)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without processing')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for Groq requests')
    parser.add_argument('--show-samples', '-s', action='store_true', help='Show sample results after processing')
    
    args = parser.parse_args()
    
    # Check Groq API key if using AI
    if not args.no_ai and not os.getenv('GROQ_API_KEY'):
        print("⚠️  Warning: GROQ_API_KEY not set!")
        print("   Either:")
        print("   1. Set GROQ_API_KEY environment variable, or")
        print("   2. Use --no-ai flag for keyword fallback only")
        print()
        response = input("Continue with keyword fallback? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
        args.no_ai = True
    
    # Run enrichment
    try:
        results = enrich_activities_batch(
            csv_path=args.csv_file,
            output_path=args.output,
            limit=args.limit,
            resume_from=args.resume_from,
            use_ai=not args.no_ai,
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        
        if results and args.show_samples:
            show_sample_results(results, count=10)
        
        sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("   Progress has been saved. Use --resume-from to continue.")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

