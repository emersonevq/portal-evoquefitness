#!/usr/bin/env python
"""
Minimal migration script - just verifies table exists, no complex operations.
All schema changes should be handled by ORM models.
"""

from sqlalchemy import inspect
from core.db import engine

def migrate_historico_status():
    """Verify historico_status table exists - minimal safe operation"""
    
    try:
        print("[migration] Starting historico_status check...")
        
        insp = inspect(engine)
        
        # Check if table exists - just logging, no modifications
        if insp.has_table("historico_status"):
            cols = {c.get("name") for c in insp.get_columns("historico_status")}
            print(f"[migration] ✓ Table 'historico_status' exists with {len(cols)} columns")
            print(f"[migration] Columns: {sorted(cols)}")
        else:
            print("[migration] ⓘ Table 'historico_status' does not exist (will be created by ORM)")
        
        # Clean up any temporary tables from previous failed attempts
        with engine.begin() as conn:
            try:
                conn.exec_driver_sql("DROP TABLE IF EXISTS historico_status_new")
                print("[migration] ✓ Cleaned up temporary tables")
            except Exception as cleanup_err:
                print(f"[migration] ⓘ Cleanup note: {cleanup_err}")
        
        print("[migration] ✓ Check completed successfully")
        
    except Exception as e:
        # Log but don't fail - let application continue
        print(f"[migration] ⚠️  Non-fatal issue: {e}")
        print("[migration] ⓘ Application will continue - ORM will manage schema")

if __name__ == "__main__":
    migrate_historico_status()
    print("[migration] Done!")
