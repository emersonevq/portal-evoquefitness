#!/usr/bin/env python3
"""
Script para MARCAR como retroativo todos os chamados com data_abertura < 01-01-2026.

Isso deve ser executado PRIMEIRO, antes de qualquer cálculo de SLA.
"""

import sys
from pathlib import Path
from datetime import datetime, date

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from core.db import SessionLocal
from ti.models import Chamado
from core.utils import now_brazil_naive

def marcar_retroativos(db: Session) -> None:
    """Marca todos os chamados anteriores a 01-01-2026 como retroativo"""
    
    print("\n" + "=" * 70)
    print("🔴 MARCANDO CHAMADOS RETROATIVOS")
    print("=" * 70)
    
    data_corte = datetime(2026, 2, 15)

    # Buscar todos os chamados ANTES de 2026-02-15 que NÃO foram marcados como retroativo
    chamados_retroativos = db.query(Chamado).filter(
        Chamado.data_abertura < data_corte,
        Chamado.retroativo != True,
        Chamado.deletado_em == None
    ).all()
    
    print(f"\n📊 Total de chamados para marcar como retroativo: {len(chamados_retroativos)}")
    
    if len(chamados_retroativos) == 0:
        print("\n✅ Nenhum chamado para marcar como retroativo!")
        return
    
    print(f"\n🔄 Marcando como retroativo...\n")
    
    for i, chamado in enumerate(chamados_retroativos, 1):
        try:
            chamado.retroativo = True
            db.add(chamado)
            
            if i % 100 == 0:
                db.commit()
                print(f"✓ [{i}/{len(chamados_retroativos)}] Processados...")
        
        except Exception as e:
            print(f"✗ [{i}/{len(chamados_retroativos)}] {chamado.codigo} - ERRO: {e}")
    
    db.commit()
    
    print(f"\n✅ {len(chamados_retroativos)} chamados marcados como retroativo!")
    
    # Diagnóstico final
    print("\n" + "=" * 70)
    print("📊 DIAGNÓSTICO FINAL")
    print("=" * 70)
    
    total = db.query(Chamado).filter(Chamado.deletado_em == None).count()
    retroativos = db.query(Chamado).filter(
        Chamado.retroativo == True,
        Chamado.deletado_em == None
    ).count()
    ativos_2026 = db.query(Chamado).filter(
        Chamado.data_abertura >= data_corte,
        Chamado.retroativo != True,
        Chamado.deletado_em == None
    ).count()
    
    print(f"\n  • Total de chamados: {total}")
    print(f"  • Retroativos (antes de 15-02-2026): {retroativos}")
    print(f"  • Válidos para SLA (15-02-2026+): {ativos_2026}")
    print()


def main():
    """Executa marcação de retroativos"""
    print("\n" + "=" * 70)
    print("🔧 SCRIPT DE MARCAÇÃO DE RETROATIVOS")
    print("=" * 70)
    print(f"Data/Hora: {now_brazil_naive().isoformat()}")
    
    db = SessionLocal()
    
    try:
        # Pedir confirmação
        print("\n⚠️  Este script vai marcar como retroativo todos os chamados")
        print("    com data_abertura ANTES de 15-02-2026")
        print("\nISSO DEVE SER EXECUTADO ANTES de cualquier cálculo de SLA!")
        resposta = input("\nDeseja continuar? (s/n): ").lower().strip()
        
        if resposta == 's':
            marcar_retroativos(db)
        else:
            print("\nOperação cancelada.")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
        print("\n✅ Script finalizado!")


if __name__ == "__main__":
    main()
