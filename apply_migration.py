#!/usr/bin/env python3
"""
Apply database migration to Supabase
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

def apply_migration(migration_file):
    """Apply a SQL migration file to Supabase."""

    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    # Read migration file
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
    except FileNotFoundError:
        print(f"❌ Migration file not found: {migration_file}")
        return False

    # Connect to Supabase
    print(f"📡 Connecting to Supabase...")
    supabase = create_client(url, key)

    # Execute migration
    print(f"🔄 Applying migration: {migration_file}")
    try:
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        print(f"✅ Migration applied successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\n⚠️  Manual application required:")
        print(f"   1. Go to your Supabase dashboard")
        print(f"   2. Open SQL Editor")
        print(f"   3. Copy and paste the contents of: {migration_file}")
        print(f"   4. Run the SQL")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_migration.py <migration_file>")
        print("\nExample:")
        print("  python apply_migration.py migrations/003_add_container_groups.sql")
        sys.exit(1)

    migration_file = sys.argv[1]
    success = apply_migration(migration_file)
    sys.exit(0 if success else 1)
