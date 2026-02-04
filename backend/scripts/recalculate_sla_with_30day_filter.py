#!/usr/bin/env python3
"""
Script de migração para recalcular SLAs com novo filtro de 30 dias.

Novo comportamento:
- Apenas chamados abertos há ≤30 dias contam para as MÉTRICAS de SLA
- Tempo só corre quando status é "aberto" ou "em andamento"
- Tempo pausa quando status é "em análise" ou "aguardando"
- Chamados com >30 dias são desconsiderados das métricas agregadas

Este script:
1. Valida que o novo código está em uso
2. Força recalcular todas as métricas
3. Exibe estatísticas antes/depois (se aplicável)
4. Invalida caches para garantir atualização
"""

import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

# Adicionar backend ao path
sys.path.insert(0, '/app')

from core.db import get_db, engine
from core.utils import now_brazil_naive
from ti.models.chamado import Chamado
from ti.models.sla_config import SLAConfiguration
from ti.services.sla_metrics_unified import UnifiedSLAMetricsCalculator
from ti.services.sla_cache import SLACacheManager

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_info(text):
    print(f"ℹ️  {text}")

def print_success(text):
    print(f"✅ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def print_error(text):
    print(f"❌ {text}")

def get_db_session():
    """Cria uma sessão de banco de dados"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    db_session = next(get_db())
    return db_session

def validate_new_code():
    """Valida que o novo código com filtro de 30 dias está em uso"""
    print_header("1. Validando Código")
    
    try:
        # Verifica se a constante de 30 dias existe
        if hasattr(UnifiedSLAMetricsCalculator, 'SLA_AGE_LIMIT_DAYS'):
            limit_days = UnifiedSLAMetricsCalculator.SLA_AGE_LIMIT_DAYS
            print_success(f"Constante de limite de idade encontrada: {limit_days} dias")
            return True
        else:
            print_warning("Constante SLA_AGE_LIMIT_DAYS não encontrada")
            return False
    except Exception as e:
        print_error(f"Erro ao validar código: {e}")
        return False

def count_chamados_by_age(db: Session):
    """Conta chamados por intervalo de idade"""
    print_header("2. Análise de Chamados por Idade")
    
    agora = now_brazil_naive()
    
    # Contadores
    stats = {
        "total": 0,
        "0_7_dias": 0,
        "7_14_dias": 0,
        "14_30_dias": 0,
        "30_60_dias": 0,
        "maior_60_dias": 0,
        "ativos_30d": 0,
        "inativos": 0,
    }
    
    try:
        # Total de chamados
        total = db.query(Chamado).filter(
            Chamado.status != "Cancelado"
        ).count()
        stats["total"] = total
        print_info(f"Total de chamados (não cancelados): {total}")
        
        # Chamados por intervalo de idade
        intervals = [
            ("0_7_dias", 0, 7),
            ("7_14_dias", 7, 14),
            ("14_30_dias", 14, 30),
            ("30_60_dias", 30, 60),
            ("maior_60_dias", 60, None),
        ]
        
        for key, min_days, max_days in intervals:
            min_date = agora - timedelta(days=max_days) if max_days else None
            max_date = agora - timedelta(days=min_days)
            
            if min_date:
                count = db.query(Chamado).filter(
                    and_(
                        Chamado.data_abertura >= min_date,
                        Chamado.data_abertura <= max_date,
                        Chamado.status != "Cancelado"
                    )
                ).count()
            else:
                count = db.query(Chamado).filter(
                    and_(
                        Chamado.data_abertura <= max_date,
                        Chamado.status != "Cancelado"
                    )
                ).count()
            
            stats[key] = count
            interval_name = f"{min_days}-{max_days}" if max_days else f">{min_days}"
            print_info(f"Chamados com {interval_name} dias: {count}")
        
        # Chamados ativos com ≤30 dias (os que contarão para SLA)
        data_limite_30d = agora - timedelta(days=30)
        ativos_30d = db.query(Chamado).filter(
            and_(
                Chamado.data_abertura >= data_limite_30d,
                Chamado.status.notin_(["Concluido", "Cancelado"])
            )
        ).count()
        stats["ativos_30d"] = ativos_30d
        print_success(f"Chamados ATIVOS com ≤30 dias (contam para SLA): {ativos_30d}")
        
        # Chamados com >30 dias (não contarão para métricas de SLA)
        inativos = total - ativos_30d - (
            db.query(Chamado).filter(
                and_(
                    Chamado.data_abertura >= data_limite_30d,
                    Chamado.status.in_(["Concluido", "Cancelado"])
                )
            ).count()
        )
        stats["inativos"] = inativos
        print_warning(f"Chamados com >30 dias (NÃO contam para métricas SLA): {inativos}")
        
        return stats
    except Exception as e:
        print_error(f"Erro ao contar chamados: {e}")
        return stats

def recalculate_metrics(db: Session):
    """Recalcula as métricas de SLA"""
    print_header("3. Recalculando Métricas de SLA")
    
    try:
        agora = now_brazil_naive()
        
        # Recalcula SLA de 24h
        print_info("Calculando SLA das últimas 24 horas...")
        sla_24h = UnifiedSLAMetricsCalculator.get_sla_compliance_24h(db)
        print_success(f"SLA 24h: {sla_24h['percentual']}% dentro do SLA ({sla_24h['dentro_sla']}/{sla_24h['total']})")
        
        # Recalcula SLA do mês
        print_info("Calculando SLA do mês atual...")
        sla_mes = UnifiedSLAMetricsCalculator.get_sla_compliance_month(db)
        print_success(f"SLA Mês: {sla_mes['percentual']}% dentro do SLA ({sla_mes['dentro_sla']}/{sla_mes['total']})")
        
        # Recalcula SLA dos últimos 30 dias
        print_info("Calculando SLA dos últimos 30 dias...")
        data_30d = agora - timedelta(days=30)
        sla_30d = UnifiedSLAMetricsCalculator.calculate_sla_distribution_period(db, data_30d, agora)
        print_success(f"SLA 30d: {sla_30d['percentual_dentro']}% dentro do SLA ({sla_30d['dentro_sla']}/{sla_30d['total']})")
        
        return {
            "sla_24h": sla_24h,
            "sla_mes": sla_mes,
            "sla_30d": sla_30d,
        }
    except Exception as e:
        print_error(f"Erro ao recalcular métricas: {e}")
        import traceback
        traceback.print_exc()
        return None

def invalidate_caches(db: Session):
    """Invalida todos os caches de SLA"""
    print_header("4. Invalidando Caches")
    
    try:
        print_info("Invalidando cache de SLA...")
        SLACacheManager.invalidate_all_sla(db)
        print_success("Cache de SLA invalidado")
        
        print_info("Invalidando cache de métricas incrementais...")
        try:
            from ti.services.cache_manager_incremental import IncrementalMetricsCache
            IncrementalMetricsCache.invalidate_all()
            print_success("Cache de métricas invalidado")
        except Exception as e:
            print_warning(f"Aviso ao invalidar cache de métricas: {e}")
        
        return True
    except Exception as e:
        print_error(f"Erro ao invalidar caches: {e}")
        return False

def main():
    print_header("🔄 Script de Recalcular SLA com Filtro de 30 Dias")
    print_info(f"Iniciado em: {now_brazil_naive()}")
    
    db = get_db_session()
    
    try:
        # 1. Validar código
        if not validate_new_code():
            print_error("Código não está validado. Interrompendo.")
            return False
        
        # 2. Analisar chamados
        stats_chamados = count_chamados_by_age(db)
        
        # 3. Recalcular métricas
        metrics = recalculate_metrics(db)
        if not metrics:
            print_error("Erro ao recalcular métricas")
            return False
        
        # 4. Invalidar caches
        if not invalidate_caches(db):
            print_warning("Erro ao invalidar caches (mas pode continuar)")
        
        # Resumo final
        print_header("✅ Resumo Final")
        print_success("Recálculo de SLA com filtro de 30 dias concluído!")
        print_info(f"Chamados analisados: {stats_chamados['total']}")
        print_info(f"Chamados ativos ≤30 dias (contam para SLA): {stats_chamados['ativos_30d']}")
        print_info(f"Chamados >30 dias (não contam para SLA): {stats_chamados['inativos']}")
        print_info(f"\nMétricas finais:")
        print_info(f"  - SLA 24h: {metrics['sla_24h']['percentual']}%")
        print_info(f"  - SLA Mês: {metrics['sla_mes']['percentual']}%")
        print_info(f"  - SLA 30d: {metrics['sla_30d']['percentual_dentro']}%")
        
        print_header("🎉 Processo Concluído com Sucesso!")
        return True
        
    except Exception as e:
        print_error(f"Erro não tratado: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
