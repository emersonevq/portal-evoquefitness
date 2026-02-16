"""
Script to restore original status for retroativo tickets from history.
This fixes the issue where status was lost when marking tickets as "Expirado".
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db import SessionLocal
from ti.models.chamado import Chamado
from ti.models.historico_status import HistoricoStatus

def restore_retroativo_status():
    """Restore original status for retroativo tickets from history"""
    
    session = SessionLocal()
    
    try:
        print("\n[RESTORE] 🔄 Starting restoration of retroativo ticket status...")
        
        # Find all tickets that are marked retroativo or are "Expirado" with old dates
        sla_start_date = datetime(2026, 1, 1, 0, 0, 0)
        
        # Find tickets with status="Expirado" and data_abertura < 2026-01-01
        retroativo_expirado = session.query(Chamado).filter(
            Chamado.status == "Expirado",
            Chamado.data_abertura < sla_start_date
        ).all()
        
        restored_count = 0
        
        for chamado in retroativo_expirado:
            # Try to find the previous status from history
            # Get the first status change that has this ticket's history
            historicos = session.query(HistoricoStatus).filter(
                HistoricoStatus.chamado_id == chamado.id
            ).order_by(HistoricoStatus.created_at.asc()).all()
            
            # Find the last non-"Expirado" status
            previous_status = None
            for historico in reversed(historicos):
                if historico.status and historico.status != "Expirado":
                    previous_status = historico.status
                    break
            
            # If no history, use the status before "Expirado" from descricao
            if not previous_status:
                for historico in reversed(historicos):
                    if historico.descricao and "→" in historico.descricao:
                        parts = historico.descricao.split("→")
                        if len(parts) > 0:
                            previous_status = parts[0].replace("Migrado: ", "").strip()
                            break
            
            # If we found a previous status, restore it
            if previous_status and previous_status != "Expirado":
                chamado.status = previous_status
                chamado.retroativo = True
                session.add(chamado)
                restored_count += 1
                print(f"[RESTORE] ✓ Ticket {chamado.codigo}: restored status to '{previous_status}'")
            else:
                # If we can't find history, mark as retroativo with current status
                chamado.retroativo = True
                session.add(chamado)
                print(f"[RESTORE] ℹ️ Ticket {chamado.codigo}: no history found, keeping '{chamado.status}' but marked as retroativo")
        
        session.commit()
        print(f"[RESTORE] ✅ Restoration completed! {restored_count} tickets restored from history\n")
        
    except Exception as e:
        session.rollback()
        print(f"[RESTORE] ⚠️  Error during restoration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    restore_retroativo_status()
