#!/usr/bin/env python3
"""
Script de diagnóstico para encontrar chamados ABERTOS/EM ATENDIMENTO de janeiro de 2026.

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
    print("🔍 DIAGNÓSTICO: CHAMADOS ABERTOS DE JANEIRO 2026")
    print("=" * 70)
    
    # Período: 01-01-2026 a 31-01-2026
    inicio_janeiro = datetime(2026, 1, 1)
    fim_janeiro = datetime(2026, 1, 31, 23, 59, 59)
    
    # Buscar chamados ABERTOS/EM ATENDIMENTO de janeiro
    chamados_ativos_jan = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_janeiro,
        Chamado.data_abertura <= fim_janeiro,
        Chamado.status.in_(["Aberto", "Em atendimento", "Em Atendimento", "Aguardando"]),
        Chamado.deletado_em == None
    ).all()
    
    print(f"\n📊 Chamados ABERTOS/EM ATENDIMENTO de janeiro: {len(chamados_ativos_jan)}\n")
    
    if len(chamados_ativos_jan) > 0:
        print("⚠️  ENCONTRADOS CHAMADOS ABERTOS QUE NÃO DEVERIAM ESTAR!")
        print("\nDetalhes:\n")
        
        for chamado in chamados_ativos_jan:
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
        print("✅ Nenhum chamado aberto de janeiro encontrado!")
    
    # Também buscar CONCLUÍDOS de janeiro para comparação
    chamados_concluidos_jan = db.query(Chamado).filter(
        Chamado.data_abertura >= inicio_janeiro,
        Chamado.data_abertura <= fim_janeiro,
        Chamado.status.in_(["Concluído", "Concluido"]),
        Chamado.deletado_em == None
    ).count()
    
    print("\n" + "=" * 70)
    print(f"📊 Chamados CONCLUÍDOS de janeiro: {chamados_concluidos_jan}")
    print(f"📊 Chamados ABERTOS de janeiro: {len(chamados_ativos_jan)}")
    print(f"📊 Total janeiro: {chamados_concluidos_jan + len(chamados_ativos_jan)}")
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
