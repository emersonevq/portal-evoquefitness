"""
Scheduler de SLA com APScheduler - Executa a cada 15 minutos

Características:
- Executa recálculo incremental a cada 15 minutos
- Atualiza cache automaticamente
- Primeira execução na inicialização
- Preenche cache completamente na primeira execução
- Usa APScheduler para agendamento robusta

Uso:
    from ti.services.sla_scheduler_15min import init_sla_scheduler_15min
    
    # Na startup da aplicação:
    init_sla_scheduler_15min()
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from core.db import SessionLocal
from core.utils import now_brazil_naive
from ti.services.sla_cache import SLACacheManager
from ti.scripts.recalculate_sla_complete import SLARecalculator

logger = logging.getLogger(__name__)

# Instância global do scheduler
_scheduler_instance = None
_first_run = True


def _recalculate_sla_incremental():
    """Executa recálculo incremental de SLA com cache"""
    global _first_run
    
    db = SessionLocal()
    try:
        agora = now_brazil_naive()
        
        if _first_run:
            logger.info("=" * 80)
            logger.info("🚀 PRIMEIRA EXECUÇÃO DE SLA - RECALCULANDO TUDO COM FILTRO 01.01.2026")
            logger.info("=" * 80)
            _first_run = False
        else:
            logger.info(f"🔄 Atualização incremental de SLA em {agora.isoformat()}")
        
        # Executa recálculo
        recalculator = SLARecalculator(db)
        stats = recalculator.recalculate_all(verbose=False)
        
        # Log dos resultados
        logger.info(f"✅ SLA Recalculado:")
        logger.info(f"   - Total processados: {stats['total_chamados']}")
        logger.info(f"   - Recalculados: {stats['recalculados']}")
        logger.info(f"   - Com erro: {stats['com_erro']}")
        logger.info(f"   - Tempo médio resposta: {stats['tempo_medio_resposta_horas']:.2f}h")
        logger.info(f"   - Tempo médio resolução: {stats['tempo_medio_resolucao_horas']:.2f}h")
        
        # Aquece o cache com as métricas principais
        _warmup_cache(db)
        
        db.commit()
        logger.info("✅ Cache atualizado com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro durante recalculação de SLA: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def _warmup_cache(db: Session):
    """Pré-aquece o cache com as métricas principais"""
    try:
        from ti.services.metrics import MetricsCalculator
        
        logger.debug("🔥 Aquecendo cache com métricas principais...")
        
        # Calcula e cacheia as métricas principais
        MetricsCalculator.get_sla_compliance_24h(db)
        MetricsCalculator.get_sla_compliance_mes(db)
        MetricsCalculator.get_sla_distribution(db)
        MetricsCalculator.get_tempo_medio_resposta_24h(db)
        MetricsCalculator.get_tempo_medio_resposta_mes(db)
        
        # Invalida cache para forçar recalcular tudo da próxima vez
        SLACacheManager.invalidate_all_sla(db)
        
        logger.debug("✅ Cache aquecido com sucesso")
    except Exception as e:
        logger.warning(f"⚠️  Erro ao aquecer cache: {e}", exc_info=True)


def init_sla_scheduler_15min():
    """
    Inicializa o scheduler de SLA com execução a cada 15 minutos.
    
    - Primeira execução: IMEDIATAMENTE (recalcula tudo)
    - Próximas: A cada 15 minutos
    - Cache: Preenchido automaticamente
    """
    global _scheduler_instance
    
    try:
        if _scheduler_instance is not None:
            logger.warning("⚠️  Scheduler de SLA 15min já está em execução")
            return _scheduler_instance
        
        # Cria scheduler
        _scheduler_instance = BackgroundScheduler()
        
        # Primeira execução: AGORA
        logger.info("⏱️  Executando primeira recalculação de SLA...")
        _recalculate_sla_incremental()
        
        # Agendamento: a cada 15 minutos
        _scheduler_instance.add_job(
            func=_recalculate_sla_incremental,
            trigger="interval",
            minutes=15,
            id="sla_recalc_15min",
            name="Recalculação incremental de SLA (15min)",
            replace_existing=True
        )
        
        # Inicia scheduler
        _scheduler_instance.start()
        
        logger.info("=" * 80)
        logger.info("✅ SCHEDULER DE SLA INICIADO")
        logger.info("=" * 80)
        logger.info(f"⏱️  Intervalo: 15 minutos")
        logger.info(f"🕐 Próxima execução: {agora_mais_15_min()}")
        logger.info("=" * 80)
        
        return _scheduler_instance
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar scheduler de SLA: {e}", exc_info=True)
        return None


def agora_mais_15_min():
    """Retorna o horário da próxima execução (daqui 15 minutos)"""
    from datetime import timedelta
    proxima = now_brazil_naive() + timedelta(minutes=15)
    return proxima.strftime("%H:%M:%S")


def stop_sla_scheduler():
    """Para o scheduler"""
    global _scheduler_instance
    
    if _scheduler_instance is not None:
        _scheduler_instance.shutdown()
        _scheduler_instance = None
        logger.info("⏹️  Scheduler de SLA parado")
