#!/usr/bin/env python3
"""
Script para FECHAR os 10 chamados de janeiro que estão ABERTOS/AGUARDANDO.

Esses chamados serão marcados como "Concluído" e seus SLAs serão recalculados.
"""

import sys
from pathlib import Path
from datetime import datetime

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from core.db import SessionLocal
from ti.models import Chamado
from core.utils import now_brazil_naive
from ti.modules.sla.services import SlaTracker

def fechar_janeiro(db: Session) -> None:
    """Fecha todos os chamados abertos de janeiro"""
    
    print("\n" + "=" * 70)
    print("🔴 FECHANDO CHAMADOS ABERTOS DE JANEIRO")
    print("=" * 70)
    
    # Lista dos 10 chamados que precisam ser fechados
    codigos_para_fechar = [
        "EVQ-0338",
        "EVQ-0339", 
        "EVQ-0342",
        "EVQ-0351",
        "EVQ-0356",
        "EVQ-0359",
        "EVQ-0380",
        "EVQ-0385",
        "EVQ-0386",
        "EVQ-0388"
    ]
    
    chamados = db.query(Chamado).filter(
        Chamado.codigo.in_(codigos_para_fechar),
        Chamado.deletado_em == None
    ).all()
    
    print(f"\n📊 Chamados para fechar: {len(chamados)}\n")
    
    if len(chamados) == 0:
        print("✅ Nenhum chamado encontrado para fechar!")
        return
    
    tracker = SlaTracker(db)
    agora = now_brazil_naive()
    
    for i, chamado in enumerate(chamados, 1):
        try:
            print(f"🔄 [{i}/{len(chamados)}] Fechando {chamado.codigo}...")
            
            # Atualizar status para Concluído
            chamado.status = "Concluído"
            chamado.data_conclusao = agora
            
            # Recalcular SLA (isso vai congelar os valores)
            resultado = tracker.concluir_sla(chamado)
            
            print(f"  ✓ {chamado.codigo} - {resultado['tempo_resolucao']:.2f}h - {resultado.get('status_sla', '?')}")
        
        except Exception as e:
            print(f"  ✗ {chamado.codigo} - ERRO: {e}")
    
    db.commit()
    
    print(f"\n✅ {len(chamados)} chamados fechados!")
    
    # Diagnóstico final
    print("\n" + "=" * 70)
    print("📊 ESTADO FINAL")
    print("=" * 70)
    
    inicio_janeiro = datetime(2026, 1, 1)
    fim_janeiro = datetime(2026, 1, 31, 23, 59, 59)
    
    abertos_jan = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_janeiro,
        Chamado.data_abertura <= fim_janeiro,
        Chamado.status.in_(["Aberto", "Em atendimento", "Em Atendimento", "Aguardando"]),
        Chamado.deletado_em == None
    ).count()
    
    concluidos_jan = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_janeiro,
        Chamado.data_abertura <= fim_janeiro,
        Chamado.status.in_(["Concluído", "Concluido"]),
        Chamado.deletado_em == None
    ).count()
    
    print(f"\n  • Chamados ABERTOS de janeiro: {abertos_jan}")
    print(f"  • Chamados CONCLUÍDOS de janeiro: {concluidos_jan}")
    print(f"  • Total janeiro: {abertos_jan + concluidos_jan}")
    print()


def main():
    """Executa fechamento de chamados"""
    print("\n" + "=" * 70)
    print("🔧 SCRIPT DE FECHAMENTO DE CHAMADOS DE JANEIRO")
    print("=" * 70)
    print(f"Data/Hora: {now_brazil_naive().isoformat()}")
    
    db = SessionLocal()
    
    try:
        # Pedir confirmação
        print("\n⚠️  Este script vai fechar 10 chamados de janeiro que estão ABERTOS")
        print("\nChamados a fechar:")
        print("  • EVQ-0338, EVQ-0339, EVQ-0342, EVQ-0351, EVQ-0356")
        print("  • EVQ-0359, EVQ-0380, EVQ-0385, EVQ-0386, EVQ-0388")
        print("\nEles serão marcados como 'Concluído' e seus SLAs recalculados.")
        
        resposta = input("\nDeseja continuar? (s/n): ").lower().strip()
        
        if resposta == 's':
            fechar_janeiro(db)
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
