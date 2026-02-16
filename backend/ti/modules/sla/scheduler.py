"""
SLA Scheduler - Integração com APScheduler.

Agenda todas as tasks periódicas do módulo SLA:
- verificar_sla_tarefa() - a cada 5 minutos
- atualizar_metricas_tarefa() - a cada 30 minutos  
- verificar_feriados_tarefa() - diariamente às 00:01
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from core.db import SessionLocal
from ti.modules.sla.tasks import (
    verificar_sla_tarefa,
    atualizar_metricas_tarefa,
    verificar_feriados_tarefa,
)

# Logger para tasks
logger = logging.getLogger("sla.scheduler")

# Instância global do scheduler
_scheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Retorna a instância global do scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def _create_db_wrapper(task_func):
    """
    Cria um wrapper que fornece sessão do banco de dados à task.
    
    As tasks precisam de uma sessão do banco de dados (Session),
    então este wrapper cria uma nova sessão, executa a task,
    e fecha a sessão após a conclusão.
    """
    def wrapper():
        db = SessionLocal()
        try:
            logger.info(f"[TASK] Iniciando {task_func.__name__}")
            task_func(db)
            logger.info(f"[TASK] Concluído {task_func.__name__}")
        except Exception as e:
            logger.error(f"[TASK] Erro em {task_func.__name__}: {e}", exc_info=True)
        finally:
            db.close()
    
    return wrapper


def schedule_sla_tasks() -> None:
    """
    Agenda todas as tasks periódicas do módulo SLA.
    
    Tarefas agendadas:
    1. verificar_sla_tarefa() - a cada 5 minutos
       - Atualiza tempo decorrido dos chamados ativos
       - Marca como "em risco" (≥75%) ou "vencido" (≥100%)
       - Escalona automaticamente se vencido
    
    2. atualizar_metricas_tarefa() - a cada 30 minutos
       - Calcula métricas do dia/semana/mês
       - Cacheia indicadores em tempo real
    
    3. verificar_feriados_tarefa() - diariamente às 00:01
       - Pausa/retoma automaticamente por feriados
    """
    scheduler = get_scheduler()
    
    logger.info("[SCHEDULER] Iniciando agendamento de tasks de SLA...")
    
    try:
        # Task 1: Verificar SLA a cada 5 minutos
        logger.info("[SCHEDULER] Agendando verificar_sla_tarefa() - intervalo: 5 minutos")
        scheduler.add_job(
            _create_db_wrapper(verificar_sla_tarefa),
            'interval',
            minutes=5,
            id='sla_verificar_5min',
            replace_existing=True,
            max_instances=1,  # Garante que apenas uma instância roda por vez
        )
        logger.info("✓ Task 'verificar_sla_tarefa' agendada com sucesso")
        
        # Task 2: Atualizar métricas a cada 30 minutos
        logger.info("[SCHEDULER] Agendando atualizar_metricas_tarefa() - intervalo: 30 minutos")
        scheduler.add_job(
            _create_db_wrapper(atualizar_metricas_tarefa),
            'interval',
            minutes=30,
            id='sla_metricas_30min',
            replace_existing=True,
            max_instances=1,
        )
        logger.info("✓ Task 'atualizar_metricas_tarefa' agendada com sucesso")
        
        # Task 3: Verificar feriados diariamente às 00:01
        logger.info("[SCHEDULER] Agendando verificar_feriados_tarefa() - diariamente às 00:01")
        scheduler.add_job(
            _create_db_wrapper(verificar_feriados_tarefa),
            'cron',
            hour=0,
            minute=1,
            id='sla_feriados_daily',
            replace_existing=True,
            max_instances=1,
        )
        logger.info("✓ Task 'verificar_feriados_tarefa' agendada com sucesso")
        
    except Exception as e:
        logger.error(f"[SCHEDULER] Erro ao agendar tasks: {e}", exc_info=True)
        raise


def start_scheduler() -> None:
    """
    Inicia o scheduler de background.
    
    Deve ser chamado no evento 'startup' da aplicação FastAPI.
    """
    scheduler = get_scheduler()
    
    if scheduler.running:
        logger.warning("[SCHEDULER] Scheduler já estava em execução")
        return
    
    try:
        logger.info("[SCHEDULER] Iniciando APScheduler...")
        schedule_sla_tasks()
        scheduler.start()
        logger.info(f"[SCHEDULER] ✓ APScheduler iniciado com sucesso")
        logger.info(f"[SCHEDULER] Próxima execução:")
        for job in scheduler.get_jobs():
            logger.info(f"  - {job.id}: {job.next_run_time}")
    except Exception as e:
        logger.error(f"[SCHEDULER] ✗ Erro ao iniciar scheduler: {e}", exc_info=True)
        raise


def stop_scheduler() -> None:
    """
    Para o scheduler de background.
    
    Deve ser chamado no evento 'shutdown' da aplicação FastAPI.
    """
    scheduler = get_scheduler()
    
    if not scheduler.running:
        logger.warning("[SCHEDULER] Scheduler já estava parado")
        return
    
    try:
        logger.info("[SCHEDULER] Parando APScheduler...")
        scheduler.shutdown(wait=True)
        logger.info("[SCHEDULER] ✓ APScheduler parado com sucesso")
    except Exception as e:
        logger.error(f"[SCHEDULER] ✗ Erro ao parar scheduler: {e}", exc_info=True)


def get_scheduler_status() -> dict:
    """
    Retorna status do scheduler e suas jobs agendadas.
    
    Útil para debugging e monitoramento.
    """
    scheduler = get_scheduler()
    
    return {
        "running": scheduler.running,
        "jobs_count": len(scheduler.get_jobs()),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time),
                "trigger": str(job.trigger),
            }
            for job in scheduler.get_jobs()
        ]
    }
