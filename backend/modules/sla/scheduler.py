"""Scheduler para recálculo automático de SLA"""

import logging
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from core.db import SessionLocal
from .service import SlaService
from .config import settings

logger = logging.getLogger("sla.scheduler")

# Instância global
_scheduler = None


def recalcular_sla_job():
    """Job que executa recálculo de SLA"""
    try:
        inicio = time.time()
        db = SessionLocal()
        
        try:
            service = SlaService(db)
            dashboard = service.obter_dashboard()
            
            tempo_ms = (time.time() - inicio) * 1000
            
            logger.info(
                f"✅ Recálculo SLA concluído em {tempo_ms:.2f}ms | "
                f"{dashboard.total_chamados} chamados | "
                f"Em risco: {dashboard.chamados_em_risco} | "
                f"Vencidos: {dashboard.chamados_vencidos}"
            )
            
            # Registrar no banco
            repo = service.repo
            repo.registrar_calculo(
                "recalculo_automatico",
                dashboard.total_chamados,
                tempo_ms,
                success=True
            )
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Erro no recálculo automático: {e}", exc_info=True)
        
        # Registrar erro no banco
        try:
            db = SessionLocal()
            repo = SlaService(db).repo
            repo.registrar_calculo(
                "recalculo_automatico",
                0,
                0,
                success=False,
                error_message=str(e)
            )
            db.close()
        except:
            pass


def start_scheduler():
    """Inicia o scheduler de recálculo"""
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler já está rodando")
        return
    
    if not settings.SCHEDULER_ENABLED:
        logger.warning("Scheduler está desabilitado")
        return
    
    try:
        _scheduler = BackgroundScheduler()
        
        # Agendar recálculo a cada X minutos
        _scheduler.add_job(
            recalcular_sla_job,
            'interval',
            minutes=settings.SCHEDULER_INTERVAL_MINUTES,
            id='recalculo_sla',
            name='Recálculo automático de SLA'
        )
        
        _scheduler.start()
        logger.info(
            f"✅ Scheduler iniciado - Recálculo a cada {settings.SCHEDULER_INTERVAL_MINUTES} minutos"
        )
    
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler: {e}", exc_info=True)
        raise


def stop_scheduler():
    """Para o scheduler"""
    global _scheduler
    
    if _scheduler is None:
        return
    
    try:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("✅ Scheduler parado")
    except Exception as e:
        logger.error(f"❌ Erro ao parar scheduler: {e}")


def get_scheduler_status() -> dict:
    """Retorna status do scheduler"""
    global _scheduler
    
    if _scheduler is None:
        return {
            "ativo": False,
            "proxima_execucao": None
        }
    
    proxima = None
    if _scheduler.running:
        job = _scheduler.get_job('recalculo_sla')
        if job:
            proxima = job.next_run_time
    
    return {
        "ativo": _scheduler.running,
        "proxima_execucao": proxima
    }


def executar_recalculo_manual():
    """Executa recálculo manual (síncrono)"""
    logger.info("Iniciando recálculo manual de SLA...")
    recalcular_sla_job()
    logger.info("Recálculo manual concluído")
