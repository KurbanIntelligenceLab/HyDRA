#!/usr/bin/env python3
"""Background cleanup job to remove inactive sessions.

This script can run in two modes:
1. One-shot: Clean up expired sessions once and exit (default)
2. Continuous: Run as a background service with periodic cleanup (--interval)

Usage:
    python backend/cleanup.py                    # One-shot cleanup
    python backend/cleanup.py --max-age 7200     # Clean sessions older than 2 hours
    python backend/cleanup.py --interval 1800    # Run cleanup every 30 minutes
"""

import argparse
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tools import project_manager


def cleanup_expired_sessions(max_age_seconds: int) -> dict:
    """Clean up sessions that haven't been active for max_age_seconds.

    Args:
        max_age_seconds: Maximum age in seconds before a session is deleted

    Returns:
        dict with cleanup statistics
    """
    current_time = time.time()
    sessions = project_manager.list_sessions()

    cleaned = []
    kept = []
    errors = []

    for session in sessions:
        session_id = session["session_id"]
        last_activity = session["last_activity"]
        age_seconds = current_time - last_activity

        if age_seconds > max_age_seconds:
            try:
                success = project_manager.cleanup_session(session_id)
                if success:
                    cleaned.append({
                        "session_id": session_id,
                        "age_hours": round(age_seconds / 3600, 2),
                        "num_projects": session["num_projects"],
                    })
                    print(f"✓ Cleaned session {session_id[:8]}... (age: {age_seconds/3600:.1f}h, projects: {session['num_projects']})")
                else:
                    errors.append(f"Session {session_id[:8]}... not found")
            except Exception as e:
                errors.append(f"Failed to clean {session_id[:8]}...: {e}")
                print(f"✗ Error cleaning {session_id[:8]}...: {e}")
        else:
            kept.append({
                "session_id": session_id,
                "age_hours": round(age_seconds / 3600, 2),
            })

    return {
        "cleaned": len(cleaned),
        "kept": len(kept),
        "errors": len(errors),
        "cleaned_sessions": cleaned,
        "kept_sessions": kept,
        "error_messages": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Clean up inactive session data")
    parser.add_argument(
        "--max-age",
        type=int,
        default=7200,
        help="Maximum session age in seconds before cleanup (default: 7200 = 2 hours)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Run continuously with this interval in seconds (default: 0 = one-shot)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without actually deleting",
    )

    args = parser.parse_args()

    if args.dry_run:
        print(f"DRY RUN MODE - no sessions will be deleted")

    print(f"Session cleanup service started")
    print(f"  Max age: {args.max_age}s ({args.max_age/3600:.1f} hours)")

    if args.interval > 0:
        print(f"  Mode: Continuous (every {args.interval}s = {args.interval/60:.1f} min)")
        print(f"  Press Ctrl+C to stop")

        try:
            while True:
                print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running cleanup...")
                if not args.dry_run:
                    result = cleanup_expired_sessions(args.max_age)
                    print(f"  Cleaned: {result['cleaned']}, Kept: {result['kept']}, Errors: {result['errors']}")
                else:
                    # In dry-run, show what would be cleaned
                    sessions = project_manager.list_sessions()
                    current_time = time.time()
                    would_clean = sum(1 for s in sessions if current_time - s["last_activity"] > args.max_age)
                    print(f"  Would clean: {would_clean}, Would keep: {len(sessions) - would_clean}")

                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\nCleanup service stopped")
            sys.exit(0)
    else:
        print(f"  Mode: One-shot")
        if not args.dry_run:
            result = cleanup_expired_sessions(args.max_age)
            print(f"\nCleanup complete:")
            print(f"  Cleaned: {result['cleaned']}")
            print(f"  Kept: {result['kept']}")
            print(f"  Errors: {result['errors']}")

            if result['errors']:
                print(f"\nErrors:")
                for error in result['error_messages']:
                    print(f"  - {error}")
        else:
            # Dry-run mode
            sessions = project_manager.list_sessions()
            current_time = time.time()
            would_clean = []
            would_keep = []

            for session in sessions:
                age = current_time - session["last_activity"]
                if age > args.max_age:
                    would_clean.append(session)
                else:
                    would_keep.append(session)

            print(f"\nDry run results:")
            print(f"  Would clean: {len(would_clean)}")
            print(f"  Would keep: {len(would_keep)}")

            if would_clean:
                print(f"\nSessions that would be cleaned:")
                for s in would_clean:
                    age_hours = (current_time - s["last_activity"]) / 3600
                    print(f"  - {s['session_id'][:8]}... (age: {age_hours:.1f}h, projects: {s['num_projects']})")


if __name__ == "__main__":
    main()
