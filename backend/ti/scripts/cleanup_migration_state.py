#!/usr/bin/env python
"""
Cleanup script to recover from failed migrations.
Run this if you encounter migration errors.

Usage:
    cd backend
    python ti/scripts/cleanup_migration_state.py
"""

from sqlalchemy import inspect, text
from core.db import engine

def cleanup_migration_state():
    """Clean up any partial/temporary tables from failed migrations"""
    
    print("[CLEANUP] Starting migration state cleanup...")
    
    try:
        with engine.begin() as conn:
            # List of temporary tables to remove
            temp_tables = [
                "historico_status_new",
                "historico_status_temp",
                "chamado_temp",
                "chamado_new",
            ]
            
            insp = inspect(engine)
            existing_tables = set(insp.get_table_names())
            
            for table_name in temp_tables:
                if table_name in existing_tables:
                    try:
                        conn.exec_driver_sql(f"DROP TABLE IF EXISTS {table_name}")
                        print(f"[CLEANUP] ✓ Dropped table: {table_name}")
                    except Exception as e:
                        print(f"[CLEANUP] ⚠️  Could not drop {table_name}: {e}")
            
            print("[CLEANUP] ✓ Temporary tables cleanup complete")
        
        print("[CLEANUP] ✅ Migration state cleanup completed successfully")
        print("[CLEANUP] You can now restart the application")
        
    except Exception as e:
        print(f"[CLEANUP] ❌ Error during cleanup: {e}")
        print("[CLEANUP] Please check your database connection and try again")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_migration_state()
