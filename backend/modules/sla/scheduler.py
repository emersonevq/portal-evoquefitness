"""
Scheduler para recálculo automático de SLA
- Tratamento robusto de erros
- Controle de falhas consecutivas
- Logs detalhados
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from datetime import datetime
import logging
import traceback

from core.db import SessionLocal
from .service import SlaService
from .config import settings

logger = logging.getLogger("sla.scheduler")

# Instância global do scheduler
scheduler = BackgroundScheduler(
    timezone="America/Sao_Paulo",
    job_defaults={
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 60
    }
)

# Controle de estado
_ultima_execucao: datetime = None
_ultimo_resultado: dict = None
_falhas_consecutivas: int = 0
MAX_FALHAS_CONSECUTIVAS: int = 5


def _job_listener(event):
    """Listener para eventos do scheduler"""
    global _ultima_execucao
    
    if event.exception:
        logger.error(f"[SLA Scheduler] Erro no job: {event.exception}")
    else:
        _ultima_execucao = datetime.now()


def recalcular_sla_job():
    """Job principal: recalcula SLA de todos os chamados ativos"""
    global _ultimo_resultado, _falhas_consecutivas
    
    logger.info(f"[SLA] Iniciando recálculo automático - {datetime.now()}")
    
    try:
        db = SessionLocal()
        try:
            service = SlaService(db)
            resultado = service.recalcular_todos_chamados()
            
            _ultimo_resultado = {
                "timestamp": resultado.timestamp.isoformat(),
                "chamados_processados": resultado.chamados_processados,
                "chamados_atualizados": resultado.chamados_atualizados,
                "em_risco": resultado.chamados_em_risco,
                "vencidos": resultado.chamados_vencidos,
                "pausados": resultado.chamados_pausados,
                "tempo_ms": resultado.tempo_execucao_ms,
                "sucesso": resultado.sucesso
            }
            
            # Reset falhas
            _falhas_consecutivas = 0
            
            # Alertas
            if resultado.chamados_vencidos > 0:
                logger.warning(
                    f"[SLA] ❌ ALERTA: {resultado.chamados_vencidos} chamados com SLA VENCIDO!"
                )
            
            if resultado.chamados_em_risco > 0:
                logger.warning(
                    f"[SLA] ⚠️ ALERTA: {resultado.chamados_em_risco} chamados em RISCO!"
                )
        finally:
            db.close()
    
    except Exception as e:
        _falhas_consecutivas += 1
        error_msg = str(e)
        
        logger.error(
            f"[SLA] Erro no recálculo ({_falhas_consecutivas}/{MAX_FALHAS_CONSECUTIVAS}): {error_msg}"
        )
        logger.error(f"[SLA] Traceback:\n{traceback.format_exc()}")
        
        _ultimo_resultado = {
            "timestamp": datetime.now().isoformat(),
            "sucesso": False,
            "erro": error_msg,
            "falhas_consecutivas": _falhas_consecutivas
        }
        
        # Se muitas falhas, para o scheduler
        if _falhas_consecutivas >= MAX_FALHAS_CONSECUTIVAS:
            logger.critical(
                f"[SLA] CRÍTICO: {MAX_FALHAS_CONSECUTIVAS} falhas consecutivas! "
                "Scheduler será pausado. Requer intervenção manual."
            )


def verificar_alertas_job():
    """Job secundário: verifica e loga alertas de SLA"""
    logger.debug(f"[SLA] Verificando alertas - {datetime.now()}")
    
    try:
        db = SessionLocal()
        try:
            service = SlaService(db)
            resumo = service.get_dashboard_resumo()
            
            logger.info(
                f"[SLA] Status: "
                f"Resposta {resumo.percentual_sla_resposta:.1f}% | "
                f"Resolução {resumo.percentual_sla_resolucao:.1f}% | "
                f"Risco: {resumo.chamados_em_risco} | "
                f"Vencidos: {resumo.chamados_vencidos} | "
                f"Pausados: {resumo.chamados_pausados}"
            )
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"[SLA] Erro na verificação de alertas: {str(e)}")


def start_scheduler():
    """Inicia o scheduler"""
    global _falhas_consecutivas
    _falhas_consecutivas = 0
    
    # Listener
    scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    # Job 1: Recálculo
    scheduler.add_job(
        recalcular_sla_job,
        trigger=IntervalTrigger(minutes=settings.SLA_RECALC_INTERVAL_MINUTES),
        id="recalcular_sla",
        name="Recalcular SLA de chamados ativos",
        replace_existing=True
    )
    
    # Job 2: Alertas
    scheduler.add_job(
        verificar_alertas_job,
        trigger=IntervalTrigger(minutes=settings.SLA_CHECK_RISK_INTERVAL_MINUTES),
        id="verificar_alertas",
        name="Verificar alertas de SLA",
        replace_existing=True
    )
    
    # Recálculo inicial (na inicialização)
    scheduler.add_job(
        recalcular_sla_job,
        trigger='date',
        run_date=datetime.now(),
        id="recalculo_inicial",
        name="Recálculo inicial",
        replace_existing=True
    )
    
    scheduler.start()
    
    logger.info(
        f"[SLA] Scheduler iniciado | "
        f"Recálculo: {settings.SLA_RECALC_INTERVAL_MINUTES}min | "
        f"Alertas: {settings.SLA_CHECK_RISK_INTERVAL_MINUTES}min"
    )


def stop_scheduler():
    """Para o scheduler"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SLA] Scheduler parado")


def get_scheduler_status() -> dict:
    """Retorna status do scheduler"""
    jobs = []
    for job in scheduler.get_jobs():
        trigger_interval = 0
        if hasattr(job.trigger, 'interval'):
            trigger_interval = job.trigger.interval.total_seconds() / 60
        
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "interval_minutes": trigger_interval
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs,
        "ultima_execucao": _ultima_execucao.isoformat() if _ultima_execucao else None,
        "ultimo_resultado": _ultimo_resultado,
        "falhas_consecutivas": _falhas_consecutivas,
        "max_falhas": MAX_FALHAS_CONSECUTIVAS,
        "config": {
            "recalc_interval": settings.SLA_RECALC_INTERVAL_MINUTES,
            "check_risk_interval": settings.SLA_CHECK_RISK_INTERVAL_MINUTES
        }
    }


def reset_falhas():
    """Reset manual do contador de falhas"""
    global _falhas_consecutivas
    _falhas_consecutivas = 0
    logger.info("[SLA] Contador de falhas resetado")


def executar_recalculo_manual() -> dict:
    """Executa recálculo manualmente"""
    recalcular_sla_job()
    return _ultimo_resultado or {"message": "Recálculo executado"}
