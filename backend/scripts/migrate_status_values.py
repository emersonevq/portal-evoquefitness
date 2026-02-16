"""
Database migration script to update ticket status values.
Run this on the backend to update the database.

Changes:
- "Cancelado" -> "Expirado" 
- "Em análise" -> "Aguardando"

Usage:
    python backend/scripts/migrate_status_values.py
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db import SQLALCHEMY_DATABASE_URL
from ti.models.chamado import Chamado

def migrate_status_values():
    """Migrate old status values to new ones"""
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Update "Cancelado" -> "Expirado"
        cancelado_count = session.query(Chamado).filter(Chamado.status == "Cancelado").count()
        if cancelado_count > 0:
            session.query(Chamado).filter(Chamado.status == "Cancelado").update(
                {Chamado.status: "Expirado"},
                synchronize_session=False
            )
            print(f"✓ Updated {cancelado_count} 'Cancelado' tickets to 'Expirado'")
        
        # Update "Em análise" -> "Aguardando"
        analise_count = session.query(Chamado).filter(Chamado.status == "Em análise").count()
        if analise_count > 0:
            session.query(Chamado).filter(Chamado.status == "Em análise").update(
                {Chamado.status: "Aguardando"},
                synchronize_session=False
            )
            print(f"✓ Updated {analise_count} 'Em análise' tickets to 'Aguardando'")
        
        session.commit()
        print("\n✓ Database migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    migrate_status_values()
