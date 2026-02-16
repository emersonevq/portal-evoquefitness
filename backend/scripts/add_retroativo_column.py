"""
Script to add retroativo column to chamado table if it doesn't exist.
"""

import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db import engine

def add_retroativo_column():
    """Add retroativo column to chamado table"""
    
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'chamado' 
                AND COLUMN_NAME = 'retroativo'
            """))
            
            if result.fetchone():
                print("✓ Column 'retroativo' already exists in 'chamado' table")
                return
            
            # Add column if it doesn't exist
            conn.execute(text("""
                ALTER TABLE chamado 
                ADD COLUMN retroativo BOOLEAN NOT NULL DEFAULT FALSE
            """))
            conn.commit()
            print("✓ Column 'retroativo' added to 'chamado' table")
            
        except Exception as e:
            print(f"⚠️ Error adding column: {e}")

if __name__ == "__main__":
    add_retroativo_column()
