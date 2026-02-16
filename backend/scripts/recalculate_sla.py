#!/usr/bin/env python3
"""
Script para recalcular métricas de SLA em chamados existentes.

Atualiza os campos:
- sla_percentual_consumido
- sla_em_risco
- sla_vencido
- sla_tempo_decorrido_horas
- sla_tempo_pausado_horas
"""

import sys
from pathlib import Path
from datetime import datetime, date

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from sqlalchemy import extract
from core.db import SessionLocal
from ti.models import Chamado, ConfiguracesSla
from ti.modules.sla.services import SlaTracker

def recalculate_sla(db: Session) -> None:
    """Recalcula SLA para todos os chamados"""
    print("\n" + "=" * 60)
    print("🔄 RECALCULANDO SLA PARA TODOS OS CHAMADOS")
    print("=" * 60)
    
    # Verificar configurações
    configs = db.query(ConfiguracesSla).filter(ConfiguracesSla.ativo == True).count()
    if configs == 0:
        print("\n❌ ERRO: Nenhuma configuração de SLA!")
        return
    
    print(f"✓ {configs} configurações de SLA encontradas\n")
    
    # Buscar chamados de 2026 que não são retroativos
    chamados = db.query(Chamado).filter(
        extract('year', Chamado.data_abertura) >= 2026,
        Chamado.deletado_em == None
    ).all()
    
    print(f"📋 Recalculando SLA para {len(chamados)} chamados de 2026+...\n")
    
    tracker = SlaTracker(db)
    atualizados = 0
    sem_config = 0
    erros = 0
    
    for i, chamado in enumerate(chamados, 1):
        try:
            # Obter config
            config = tracker.obter_config_por_prioridade(chamado.prioridade)
            if not config:
                print(f"  ⚠️  {chamado.codigo}: sem config para '{chamado.prioridade}'")
                sem_config += 1
                continue
            
            # Atualizar monitoramento (calcula os valores)
            tracker.atualizar_monitoramento(chamado)
            
            # Se já está concluído, calcular o resultado final
            if chamado.status == "Concluído":
                resultado = tracker.concluir_sla(chamado)
            
            atualizados += 1
            
            # Mostrar progresso
            if i % 50 == 0:
                print(f"  ✓ Processados {i}/{len(chamados)}...")
                
        except Exception as e:
            print(f"  ❌ Erro ao processar {chamado.codigo}: {e}")
            erros += 1
    
    db.commit()
    
    print(f"\n✅ Resultado:")
    print(f"  • SLA recalculados: {atualizados}")
    print(f"  • Sem configuração: {sem_config}")
    print(f"  • Erros: {erros}")
    print(f"  • Total processados: {atualizados + sem_config + erros}")


def main():
    """Executa recalculação"""
    print("\n" + "=" * 60)
    print("📊 RECALCULAR SLA")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().isoformat()}")
    
    db = SessionLocal()
    
    try:
        recalculate_sla(db)
        
        print("\n" + "=" * 60)
        print("✅ Recalculação concluída!")
        print("=" * 60)
        print("Dashboard deve agora mostrar os dados corretos.")
        print("Recarregue a página: http://localhost:3005")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
