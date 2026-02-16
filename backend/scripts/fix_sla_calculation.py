#!/usr/bin/env python3
"""
Script para RECALCULAR corretamente os campos de SLA.

PROBLEMA: O populate_sla.py chamou atualizar_monitoramento() para TODOS os chamados,
mas essa função ignora chamados Concluídos!

SOLUÇÃO: 
- Chamados Concluídos de 2026+ → chamar concluir_sla()
- Chamados Abertos/Em Atendimento de 2026+ → chamar atualizar_monitoramento()
- Chamados anteriores a 2026 → marcar como retroativo
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
from ti.modules.sla.services import SlaTracker
from core.utils import now_brazil_naive

def recalcular_sla(db: Session) -> None:
    """Recalcula SLA corretamente para todos os chamados de 2026+"""
    
    print("\n" + "=" * 70)
    print("🔧 RECÁLCULO CORRETO DE SLA")
    print("=" * 70)
    
    data_corte = date(2026, 1, 1)
    tracker = SlaTracker(db)
    
    # Buscar APENAS chamados de 2026+ que NÃO são retroativos
    chamados_2026 = db.query(Chamado).filter(
        Chamado.data_abertura >= datetime.combine(data_corte, datetime.min.time()),
        Chamado.retroativo != True,
        Chamado.deletado_em == None
    ).all()
    
    print(f"\n📊 Total de chamados 2026+: {len(chamados_2026)}")
    
    concluidos_processados = 0
    ativos_processados = 0
    erros = 0
    
    print("\n🔄 Processando chamados...\n")
    
    for i, chamado in enumerate(chamados_2026, 1):
        try:
            # Verificar status (normalizar para aceitar com/sem acento, variações)
            status = chamado.status.strip() if chamado.status else ""
            status_lower = status.lower()

            # Normalizar para tratar "Concluído" e "Concluido" igualmente
            if "conclu" in status_lower:
                # Para concluídos: chamar concluir_sla()
                # Isso calcula o tempo total com pausas e o congela
                try:
                    resultado = tracker.concluir_sla(chamado)
                    if resultado:  # Se retornar algo, significa que tem SLA configurado
                        concluidos_processados += 1
                        print(f"✓ [{i}/{len(chamados_2026)}] {chamado.codigo} (Concluído) - {resultado['tempo_resolucao']:.2f}h / {resultado.get('status_sla', '?')}")
                except Exception as e:
                    print(f"✗ [{i}/{len(chamados_2026)}] {chamado.codigo} (Concluído) - ERRO: {e}")
                    erros += 1

            elif status_lower in ["aberto", "em atendimento", "aguardando"]:
                # Para ativos: chamar atualizar_monitoramento()
                # Isso calcula o tempo decorrido até agora
                try:
                    tracker.atualizar_monitoramento(chamado)
                    ativos_processados += 1
                    print(f"✓ [{i}/{len(chamados_2026)}] {chamado.codigo} ({status}) - {chamado.sla_tempo_decorrido_horas:.2f}h / {chamado.sla_percentual_consumido:.1f}%")
                except Exception as e:
                    print(f"✗ [{i}/{len(chamados_2026)}] {chamado.codigo} ({status}) - ERRO: {e}")
                    erros += 1
            else:
                print(f"⊘ [{i}/{len(chamados_2026)}] {chamado.codigo} (Status desconhecido: {status})")
        
        except Exception as e:
            print(f"✗ [{i}/{len(chamados_2026)}] {chamado.codigo} - ERRO CRÍTICO: {e}")
            erros += 1
        
        # Commit a cada 50 para não sobrecarregar memória
        if i % 50 == 0:
            db.commit()
    
    db.commit()
    
    print("\n" + "=" * 70)
    print("✅ RECÁLCULO FINALIZADO")
    print("=" * 70)
    print(f"\n📊 Resultado:")
    print(f"  • Chamados Concluídos processados: {concluidos_processados}")
    print(f"  • Chamados Ativos processados: {ativos_processados}")
    print(f"  • Erros: {erros}")
    print(f"  • Total: {concluidos_processados + ativos_processados + erros}")
    print()


def main():
    """Executa recálculo de SLA"""
    print("\n" + "=" * 70)
    print("🔧 SCRIPT DE RECÁLCULO DE SLA")
    print("=" * 70)
    print(f"Data/Hora: {now_brazil_naive().isoformat()}")
    
    db = SessionLocal()
    
    try:
        # Pedir confirmação
        print("\n⚠️  Este script vai recalcular SLA para todos os chamados de 2026+")
        print("\nIsso pode levar alguns minutos dependendo da quantidade de chamados.")
        resposta = input("\nDeseja continuar? (s/n): ").lower().strip()
        
        if resposta == 's':
            recalcular_sla(db)
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
