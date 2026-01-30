#!/usr/bin/env python3
"""
Test script to verify Session database access works.

Run: python test_connection.py
"""

import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session_controller.config import SessionConfig


def main():
    print("=" * 60)
    print("Session Controller - Connection Test")
    print("=" * 60)

    # Find profiles
    print("\n1. Finding Session profiles...")
    profiles = SessionConfig.find_profiles()
    if not profiles:
        print("   No Session profiles found!")
        print("   Make sure Session has been run at least once.")
        return 1

    print(f"   Found profiles: {profiles if profiles else ['(production)']}")

    # Use first profile (empty string = production)
    profile = profiles[0] if profiles else None
    config = SessionConfig(profile=profile if profile else None)

    print(f"\n2. Session data path: {config.data_path}")
    print(f"   Exists: {config.exists()}")

    if not config.exists():
        print("   ERROR: Session data folder not found!")
        return 1

    print(f"\n3. Config file: {config.config_path}")
    print(f"   Exists: {config.config_path.exists()}")

    try:
        cfg = config.load_config()
        print(f"   Keys: {list(cfg.keys())}")
        print(f"   Has password: {config.has_password}")
        db_key = config.db_key
        print(f"   DB key (first 8 chars): {db_key[:8]}...")
    except Exception as e:
        print(f"   ERROR loading config: {e}")
        return 1

    print(f"\n4. Database: {config.db_path}")
    print(f"   Exists: {config.db_path.exists()}")

    # Try to import sqlcipher
    print("\n5. Checking sqlcipher...")
    try:
        from sqlcipher3 import dbapi2 as sqlite

        print("   sqlcipher3 is available!")
    except ImportError:
        try:
            from pysqlcipher3 import dbapi2 as sqlite

            print("   pysqlcipher3 is available!")
        except ImportError:
            print("   ERROR: No sqlcipher module found!")
            print("   Install with: pip install sqlcipher3")
            print("   Or on Mac: brew install sqlcipher && pip install sqlcipher3")
            return 1

    # Try to connect
    print("\n6. Testing database connection...")
    try:
        from session_controller.database import SessionDatabase

        with SessionDatabase(config) as db:
            print("   Connected successfully!")

            # Get conversations
            convos = db.get_conversations()
            print(f"\n7. Found {len(convos)} conversations:")
            for c in convos[:5]:  # Show first 5
                print(
                    f"   - {c.name} ({c.type}): {c.last_message[:50] if c.last_message else '(no messages)'}..."
                )

            # Get our pubkey
            our_pk = db.get_our_pubkey()
            print(
                f"\n8. Our Session ID: {our_pk[:16]}..."
                if our_pk
                else "\n8. Session ID not found (not logged in?)"
            )

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
