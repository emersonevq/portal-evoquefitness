#!/usr/bin/env python3
"""
Script de diagnóstico para encontrar chamados ABERTOS/EM ATENDIMENTO a partir de 13-02-2026.

Se não deveriam existir, identifica o problema.
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

def diagnosticar(db: Session) -> None:
    """Diagnostica chamados abertos de janeiro"""
    
    print("\n" + "=" * 70)
    print("🔍 DIAGNÓSTICO: CHAMADOS ABERTOS A PARTIR DE 15-02-2026")
    print("=" * 70)

    # Período: 15-02-2026 em diante
    inicio_fevereiro = datetime(2026, 2, 15)
    fim_fevereiro = datetime(2026, 12, 31, 23, 59, 59)
    
    # Buscar chamados ABERTOS/EM ATENDIMENTO a partir de 15-02-2026
    chamados_ativos_fev = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_fevereiro,
        Chamado.data_abertura <= fim_fevereiro,
        Chamado.status.in_(["Aberto", "Em atendimento", "Em Atendimento", "Aguardando"]),
        Chamado.deletado_em == None
    ).all()

    print(f"\n📊 Chamados ABERTOS/EM ATENDIMENTO a partir de 15-02-2026: {len(chamados_ativos_fev)}\n")
    
    if len(chamados_ativos_fev) > 0:
        print("⚠️  ENCONTRADOS CHAMADOS ABERTOS QUE NÃO DEVERIAM ESTAR!")
        print("\nDetalhes:\n")

        for chamado in chamados_ativos_fev:
            dias_aberto = (now_brazil_naive().date() - chamado.data_abertura.date()).days
            print(f"  Código: {chamado.codigo}")
            print(f"    Status: {chamado.status}")
            print(f"    Abertura: {chamado.data_abertura}")
            print(f"    Dias aberto: {dias_aberto}")
            print(f"    SLA em risco: {chamado.sla_em_risco}")
            print(f"    SLA vencido: {chamado.sla_vencido}")
            print(f"    Tempo decorrido: {chamado.sla_tempo_decorrido_horas:.2f}h")
            print()
    else:
        print("✅ Nenhum chamado aberto a partir de 15-02-2026 encontrado!")

    # Também buscar CONCLUÍDOS a partir de 15-02-2026 para comparação
    chamados_concluidos_fev = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_fevereiro,
        Chamado.data_abertura <= fim_fevereiro,
        Chamado.status.in_(["Concluído", "Concluido"]),
        Chamado.deletado_em == None
    ).count()

    print("\n" + "=" * 70)
    print(f"📊 Chamados CONCLUÍDOS a partir de 15-02-2026: {chamados_concluidos_fev}")
    print(f"📊 Chamados ABERTOS a partir de 15-02-2026: {len(chamados_ativos_fev)}")
    print(f"📊 Total a partir de 15-02-2026: {chamados_concluidos_fev + len(chamados_ativos_fev)}")
    print("=" * 70)
    print()


def main():
    """Executa diagnóstico"""
    print("\n" + "=" * 70)
    print("🔧 SCRIPT DE DIAGNÓSTICO")
    print("=" * 70)
    print(f"Data/Hora: {now_brazil_naive().isoformat()}")
    
    db = SessionLocal()
    
    try:
        diagnosticar(db)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
        print("✅ Script finalizado!")


if __name__ == "__main__":
    main()
