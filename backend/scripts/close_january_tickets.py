#!/usr/bin/env python3
"""
Script para FECHAR chamados a partir de 15-02-2026 que estão ABERTOS/AGUARDANDO.

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

def fechar_fevereiro(db: Session) -> None:
    """Fecha todos os chamados abertos a partir de 15-02-2026"""

    print("\n" + "=" * 70)
    print("🔴 FECHANDO CHAMADOS ABERTOS A PARTIR DE 15-02-2026")
    print("=" * 70)

    # Buscar automaticamente chamados abertos a partir de 13-02-2026
    inicio_fevereiro = datetime(2026, 2, 13)
    chamados_abertos = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_fevereiro,
        Chamado.status.in_(["Aberto", "Em atendimento", "Em Atendimento", "Aguardando"]),
        Chamado.deletado_em == None
    ).all()

    codigos_para_fechar = [chamado.codigo for chamado in chamados_abertos]
    
    chamados = [c for c in chamados_abertos if c.codigo in codigos_para_fechar]

    print(f"\n📊 Chamados para fechar: {len(chamados)}\n")
    if len(chamados) > 0:
        print("Códigos:")
        for codigo in codigos_para_fechar:
            print(f"  • {codigo}")
        print()
    
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

    inicio_fevereiro = datetime(2026, 2, 15)
    fim_fevereiro = datetime(2026, 12, 31, 23, 59, 59)

    abertos_fev = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_fevereiro,
        Chamado.data_abertura <= fim_fevereiro,
        Chamado.status.in_(["Aberto", "Em atendimento", "Em Atendimento", "Aguardando"]),
        Chamado.deletado_em == None
    ).count()

    concluidos_fev = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_fevereiro,
        Chamado.data_abertura <= fim_fevereiro,
        Chamado.status.in_(["Concluído", "Concluido"]),
        Chamado.deletado_em == None
    ).count()

    print(f"\n  • Chamados ABERTOS a partir de 15-02-2026: {abertos_fev}")
    print(f"  • Chamados CONCLUÍDOS a partir de 15-02-2026: {concluidos_fev}")
    print(f"  • Total a partir de 15-02-2026: {abertos_fev + concluidos_fev}")
    print()


def main():
    """Executa fechamento de chamados"""
    print("\n" + "=" * 70)
    print("🔧 SCRIPT DE FECHAMENTO DE CHAMADOS A PARTIR DE 15-02-2026")
    print("=" * 70)
    print(f"Data/Hora: {now_brazil_naive().isoformat()}")

    db = SessionLocal()

    try:
        # Pedir confirmação
        print("\n⚠️  Este script vai fechar chamados que estão ABERTOS a partir de 13-02-2026")
        print("\nEles serão marcados como 'Concluído' e seus SLAs recalculados.")
        
        resposta = input("\nDeseja continuar? (s/n): ").lower().strip()
        
        if resposta == 's':
            fechar_fevereiro(db)
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
