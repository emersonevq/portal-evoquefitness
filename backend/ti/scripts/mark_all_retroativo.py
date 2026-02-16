"""
Script to mark all retroactive tickets (before 01.01.2026) as retroativo = true
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.db import SessionLocal
from ti.models.chamado import Chamado

def mark_retroativo_tickets():
    """Mark all tickets before 2026-01-01 as retroativo"""
    
    session = SessionLocal()
    
    try:
        print("\n[MARK RETROATIVO] 🔍 Iniciando marcação de chamados retroativos...")
        
        sla_start_date = datetime(2026, 1, 1, 0, 0, 0)
        
        # Find all tickets before SLA start date that are not yet marked
        retroativo_tickets = session.query(Chamado).filter(
            Chamado.data_abertura < sla_start_date,
            (Chamado.retroativo == False) | (Chamado.retroativo.is_(None))
        ).all()
        
        print(f"[MARK RETROATIVO] Encontrados {len(retroativo_tickets)} chamados retroativos para marcar")
        
        if not retroativo_tickets:
            print("[MARK RETROATIVO] ✅ Nenhum chamado precisa ser marcado")
            return
        
        # Mark all as retroativo
        for chamado in retroativo_tickets:
            chamado.retroativo = True
            session.add(chamado)
            print(f"[MARK RETROATIVO] ✓ Chamado {chamado.codigo} marcado como retroativo (data: {chamado.data_abertura})")
        
        session.commit()
        print(f"[MARK RETROATIVO] ✅ {len(retroativo_tickets)} chamados marcados como retroativos com sucesso!\n")
        
    except Exception as e:
        session.rollback()
        print(f"[MARK RETROATIVO] ❌ Erro ao marcar retroativos: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    mark_retroativo_tickets()
