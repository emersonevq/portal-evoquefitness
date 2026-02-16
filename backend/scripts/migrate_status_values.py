"""
Database migration script to update ticket status values.
Run this on the backend to update the database.

Changes:
- "Cancelado" -> "Expirado"
- "Em análise" -> "Aguardando"
- "Em andamento" -> "Em atendimento"

Usage:
    python backend/scripts/migrate_status_values.py
"""

import os
import sys
from datetime import datetime
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db import engine
from ti.models.chamado import Chamado

def migrate_status_values():
    """Migrate old status values to new ones"""

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        from datetime import datetime

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

        # Update "Em andamento" -> "Em atendimento"
        andamento_count = session.query(Chamado).filter(Chamado.status == "Em andamento").count()
        if andamento_count > 0:
            session.query(Chamado).filter(Chamado.status == "Em andamento").update(
                {Chamado.status: "Em atendimento"},
                synchronize_session=False
            )
            print(f"✓ Updated {andamento_count} 'Em andamento' tickets to 'Em atendimento'")

        # Mark retroactive tickets (before 01.01.2026) as Expirado
        sla_start_date = datetime(2026, 1, 1, 0, 0, 0)
        retroativo_count = session.query(Chamado).filter(
            Chamado.data_abertura < sla_start_date,
            Chamado.status != "Expirado"
        ).count()
        if retroativo_count > 0:
            session.query(Chamado).filter(
                Chamado.data_abertura < sla_start_date,
                Chamado.status != "Expirado"
            ).update(
                {Chamado.status: "Expirado"},
                synchronize_session=False
            )
            print(f"✓ Updated {retroativo_count} retroactive tickets (before 01.01.2026) to 'Expirado'")

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
