#!/usr/bin/env python3
"""
Script para popular campos de SLA em chamados existentes.

Diagnóstico e preenchimento:
1. Verifica status de chamados no banco
2. Inicializa SLA para chamados sem SLA
3. Atualiza métricas de SLA
"""

import sys
from pathlib import Path
from datetime import datetime, date

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from core.db import SessionLocal
from ti.models import Chamado, ConfiguracesSla
from ti.modules.sla.services import SlaTracker

def diagnostico(db: Session) -> None:
    """Executa diagnóstico do estado dos chamados"""
    print("\n" + "=" * 60)
    print("📊 DIAGNÓSTICO DO BANCO DE DADOS")
    print("=" * 60)
    
    total = db.query(Chamado).count()
    print(f"\n✓ Total de chamados: {total}")
    
    # Por status
    statuses = ["Aberto", "Em atendimento", "Concluído", "Aguardando", "Reabertu"]
    print("\nChamados por status:")
    for status in statuses:
        count = db.query(Chamado).filter(Chamado.status == status).count()
        if count > 0:
            print(f"  • {status}: {count}")
    
    # Por ano
    print("\nChamados por ano:")
    from sqlalchemy import func, extract
    
    anos = db.query(extract('year', Chamado.data_abertura).label('ano')).distinct().all()
    for (ano,) in anos:
        if ano:
            count = db.query(Chamado).filter(
                extract('year', Chamado.data_abertura) == ano
            ).count()
            print(f"  • {int(ano)}: {count}")
    
    # SLA status
    print("\nStatus de SLA:")
    com_sla = db.query(Chamado).filter(Chamado.sla_em_risco != None).count()
    sem_sla = db.query(Chamado).filter(Chamado.sla_em_risco == None).count()
    print(f"  • Com SLA inicializado: {com_sla}")
    print(f"  • Sem SLA inicializado: {sem_sla}")
    
    # Exemplo
    print("\nExemplo de chamado:")
    exemplo = db.query(Chamado).first()
    if exemplo:
        print(f"  • ID: {exemplo.id}")
        print(f"  • Código: {exemplo.codigo}")
        print(f"  • Status: {exemplo.status}")
        print(f"  • Data abertura: {exemplo.data_abertura}")
        print(f"  • Data conclusão: {exemplo.data_conclusao}")
        print(f"  • Prioridade: {exemplo.prioridade}")
        print(f"  • SLA em risco: {exemplo.sla_em_risco}")
        print(f"  • SLA vencido: {exemplo.sla_vencido}")
        print(f"  • SLA percentual: {exemplo.sla_percentual_consumido}")
        print(f"  • Retroativo: {exemplo.retroativo}")


def populate_sla(db: Session) -> None:
    """Popula SLA para chamados existentes"""
    print("\n" + "=" * 60)
    print("🔄 INICIALIZANDO SLA PARA CHAMADOS")
    print("=" * 60)
    
    # Verificar se configurações existem
    configs = db.query(ConfiguracesSla).filter(ConfiguracesSla.ativo == True).count()
    if configs == 0:
        print("\n❌ ERRO: Nenhuma configuração de SLA encontrada!")
        print("Execute primeiro: python scripts/seed_sla.py")
        return
    
    print(f"\n✓ {configs} configurações de SLA encontradas")
    
    # Buscar chamados sem SLA inicializado
    chamados_sem_sla = db.query(Chamado).filter(
        Chamado.sla_em_risco == None,
        Chamado.deletado_em == None,
        Chamado.retroativo != True
    ).all()
    
    print(f"\n📋 Inicializando SLA para {len(chamados_sem_sla)} chamados...")
    
    tracker = SlaTracker(db)
    inicializados = 0
    retroativos = 0
    sem_config = 0
    
    for i, chamado in enumerate(chamados_sem_sla, 1):
        try:
            # Validar data de corte
            if chamado.data_abertura:
                data_abertura = chamado.data_abertura
                if isinstance(data_abertura, datetime):
                    data_abertura = data_abertura.date()
                
                data_corte = date(2026, 2, 13)
                if data_abertura < data_corte:
                    chamado.retroativo = True
                    db.add(chamado)
                    db.commit()
                    retroativos += 1
                    continue
            
            # Inicializar SLA
            config = tracker.obter_config_por_prioridade(chamado.prioridade)
            if not config:
                sem_config += 1
                continue
            
            # Inicia SLA
            tracker.iniciar_sla(chamado)
            
            # Atualiza monitoramento (calcula percentual, marca em risco/vencido)
            tracker.atualizar_monitoramento(chamado)
            
            inicializados += 1
            
            # Mostrar progresso
            if i % 50 == 0:
                print(f"  ✓ Processados {i}/{len(chamados_sem_sla)}...")
        
        except Exception as e:
            print(f"  ⚠️  Erro ao processar chamado {chamado.codigo}: {e}")
    
    db.commit()
    
    print(f"\n✅ Resultado:")
    print(f"  • SLA inicializados: {inicializados}")
    print(f"  • Retroativos (antes de 13-02-2026): {retroativos}")
    print(f"  • Sem configuração de SLA: {sem_config}")
    print(f"  • Total processados: {inicializados + retroativos + sem_config}")


def main():
    """Executa diagnóstico e população"""
    print("\n" + "=" * 60)
    print("🔧 SCRIPT DE POPULAÇÃO DE SLA")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().isoformat()}")
    
    db = SessionLocal()
    
    try:
        # Diagnóstico
        diagnostico(db)
        
        # Perguntar se deseja continuar
        print("\n" + "=" * 60)
        print("⚠️  Este script vai inicializar SLA para chamados existentes")
        print("=" * 60)
        resposta = input("\nDeseja continuar? (s/n): ").lower().strip()
        
        if resposta == 's':
            populate_sla(db)
        else:
            print("\nOperação cancelada.")
        
        # Diagnóstico final
        print("\n" + "=" * 60)
        print("📊 ESTADO FINAL DO BANCO")
        print("=" * 60)
        diagnostico(db)
        
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
