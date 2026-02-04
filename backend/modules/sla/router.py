from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging

from core.db import get_db
from .service import SlaService
from .scheduler import get_scheduler_status, executar_recalculo_manual, reset_falhas
from .schemas import (
    SlaConfigCreate,
    SlaConfigUpdate,
    SlaConfigResponse,
    FeriadoCreate,
    FeriadoResponse,
    SlaDashboard,
    SlaDashboardResumo,
    SlaChamadoStatus,
    MudancaStatusRequest,
    MudancaStatusResponse,
    PausasChamadoResponse,
    RecalculoResponse,
    SchedulerStatus
)
from .exceptions import (
    ConfiguracaoDuplicadaError,
    FeriadoDuplicadoError,
    ChamadoNaoEncontradoError,
    ConfiguracaoNaoEncontradaError
)

logger = logging.getLogger("sla.router")

router = APIRouter(prefix="/sla", tags=["SLA"])


# ==================== Health Check ====================

@router.get("/health", summary="Health check do módulo SLA")
def health_check():
    return {
        "status": "ok",
        "module": "sla",
        "timestamp": datetime.now().isoformat()
    }


# ==================== Dashboard ====================

@router.get(
    "/dashboard",
    response_model=SlaDashboard,
    summary="Dashboard completo de SLA"
)
def get_dashboard(
    data_inicio: Optional[datetime] = Query(None, description="Início do período"),
    data_fim: Optional[datetime] = Query(None, description="Fim do período"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade"),
    db: Session = Depends(get_db)
):
    """
    Retorna dashboard completo com métricas de SLA.
    
    - Período padrão: últimos 30 dias
    - Inclui listas de chamados em risco, vencidos e pausados
    """
    try:
        service = SlaService(db)
        return service.get_dashboard(data_inicio, data_fim, prioridade)
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao gerar dashboard"
        )


@router.get(
    "/dashboard/resumo",
    response_model=SlaDashboardResumo,
    summary="Resumo do dashboard para widgets"
)
def get_dashboard_resumo(db: Session = Depends(get_db)):
    """Retorna versão resumida do dashboard"""
    try:
        service = SlaService(db)
        return service.get_dashboard_resumo()
    except Exception as e:
        logger.error(f"Erro ao gerar resumo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao gerar resumo"
        )


# ==================== Chamado Individual ====================

@router.get(
    "/chamado/{chamado_id}",
    response_model=SlaChamadoStatus,
    summary="Status SLA de um chamado"
)
def get_sla_chamado(chamado_id: int, db: Session = Depends(get_db)):
    """Retorna status detalhado do SLA de um chamado"""
    try:
        service = SlaService(db)
        resultado = service.get_sla_chamado(chamado_id)
        
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chamado {chamado_id} não encontrado"
            )
        
        return resultado
    
    except ConfiguracaoNaoEncontradaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar SLA do chamado {chamado_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar SLA do chamado"
        )


@router.get(
    "/chamado/{chamado_id}/pausas",
    response_model=PausasChamadoResponse,
    summary="Histórico de pausas do chamado"
)
def get_pausas_chamado(chamado_id: int, db: Session = Depends(get_db)):
    """Retorna todas as pausas de SLA de um chamado"""
    try:
        service = SlaService(db)
        return service.get_pausas_chamado(chamado_id)
    
    except ChamadoNaoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao buscar pausas do chamado {chamado_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar pausas"
        )


@router.post(
    "/chamado/mudanca-status",
    response_model=MudancaStatusResponse,
    summary="Registrar mudança de status"
)
def registrar_mudanca_status(
    data: MudancaStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Registra mudança de status e gerencia pausa do SLA.
    
    **IMPORTANTE**: Chamar sempre que o status do chamado mudar!
    
    - Status "Em análise" → SLA é pausado
    - Sai de "Em análise" → SLA é retomado
    """
    try:
        service = SlaService(db)
        return service.registrar_mudanca_status(
            data.chamado_id,
            data.status_anterior,
            data.status_novo,
            data.usuario_id
        )
    except Exception as e:
        logger.error(f"Erro ao registrar mudança de status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar mudança de status"
        )


# ==================== Configurações ====================

@router.get(
    "/config",
    response_model=List[SlaConfigResponse],
    summary="Listar configurações de SLA"
)
def listar_configuracoes(db: Session = Depends(get_db)):
    """Lista todas as configurações de SLA por prioridade"""
    service = SlaService(db)
    return service.get_configs()


@router.post(
    "/config",
    response_model=SlaConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar configuração de SLA"
)
def criar_configuracao(data: SlaConfigCreate, db: Session = Depends(get_db)):
    """Cria nova configuração de SLA para uma prioridade"""
    try:
        service = SlaService(db)
        return service.create_config(data)
    
    except ConfiguracaoDuplicadaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao criar config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar configuração"
        )


@router.patch(
    "/config/{config_id}",
    response_model=SlaConfigResponse,
    summary="Atualizar configuração de SLA"
)
def atualizar_configuracao(
    config_id: int,
    data: SlaConfigUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza configuração de SLA existente"""
    try:
        service = SlaService(db)
        config = service.update_config(config_id, data)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuração não encontrada"
            )
        
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar config {config_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar configuração"
        )


@router.delete(
    "/config/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar configuração de SLA"
)
def deletar_configuracao(config_id: int, db: Session = Depends(get_db)):
    """Desativa (soft delete) uma configuração de SLA"""
    service = SlaService(db)
    if not service.delete_config(config_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração não encontrada"
        )


# ==================== Feriados ====================

@router.get(
    "/feriados",
    response_model=List[FeriadoResponse],
    summary="Listar feriados"
)
def listar_feriados(
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    db: Session = Depends(get_db)
):
    """Lista feriados cadastrados"""
    service = SlaService(db)
    return service.get_feriados(ano)


@router.post(
    "/feriados",
    response_model=FeriadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar feriado"
)
def criar_feriado(data: FeriadoCreate, db: Session = Depends(get_db)):
    """Cadastra novo feriado"""
    try:
        service = SlaService(db)
        return service.create_feriado(data.model_dump())
    
    except FeriadoDuplicadoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao criar feriado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar feriado"
        )


@router.delete(
    "/feriados/{feriado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover feriado"
)
def deletar_feriado(feriado_id: int, db: Session = Depends(get_db)):
    """Remove um feriado"""
    service = SlaService(db)
    if not service.delete_feriado(feriado_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feriado não encontrado"
        )


# ==================== Scheduler ====================

@router.get(
    "/scheduler/status",
    summary="Status do scheduler"
)
def scheduler_status():
    """Retorna status do scheduler de recálculo automático"""
    return get_scheduler_status()


@router.post(
    "/scheduler/executar",
    response_model=RecalculoResponse,
    summary="Executar recálculo manual"
)
def executar_recalculo(db: Session = Depends(get_db)):
    """Executa recálculo de SLA imediatamente"""
    try:
        service = SlaService(db)
        return service.recalcular_todos_chamados()
    except Exception as e:
        logger.error(f"Erro ao executar recálculo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao executar recálculo"
        )


@router.post(
    "/scheduler/executar-ilimitado",
    response_model=RecalculoResponse,
    summary="Executar recálculo manual SEM limite de data"
)
def executar_recalculo_ilimitado(db: Session = Depends(get_db)):
    """
    Executa recálculo de SLA de TODOS os chamados sem limite de data.

    **CUIDADO**: Operação pesada! Use apenas em casos especiais de auditoria.
    Use `/scheduler/executar` para o recálculo padrão (últimos 30 dias).
    """
    try:
        service = SlaService(db)
        return service.recalcular_todos_chamados_ilimitado()
    except Exception as e:
        logger.error(f"Erro ao executar recálculo ilimitado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao executar recálculo ilimitado"
        )


@router.post(
    "/scheduler/reset-falhas",
    summary="Reset contador de falhas"
)
def reset_falhas_endpoint():
    """Reseta o contador de falhas consecutivas do scheduler"""
    reset_falhas()
    return {"message": "Contador de falhas resetado"}


# ==================== Cache ====================

@router.get(
    "/cache/status",
    summary="Status do cache"
)
def cache_status(db: Session = Depends(get_db)):
    """Retorna status do cache de SLA"""
    service = SlaService(db)
    return service.get_cache_status()


@router.post(
    "/cache/invalidar",
    summary="Invalidar cache"
)
def invalidar_cache(db: Session = Depends(get_db)):
    """Invalida todo o cache de SLA"""
    service = SlaService(db)
    service.invalidar_cache()
    return {"message": "Cache invalidado"}


# ==================== Logs ====================

@router.get(
    "/logs",
    summary="Logs de cálculos"
)
def listar_logs(
    limite: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retorna últimos logs de cálculo de SLA"""
    from .repository import SlaRepository
    repo = SlaRepository(db)
    logs = repo.get_logs_recentes(limite)
    
    return [
        {
            "id": log.id,
            "tipo": log.calculation_type,
            "data": log.last_calculated_at.isoformat() if log.last_calculated_at else None,
            "chamados": log.chamados_count,
            "em_risco": log.chamados_em_risco,
            "vencidos": log.chamados_vencidos,
            "pausados": log.chamados_pausados,
            "tempo_ms": log.execution_time_ms,
            "sucesso": log.success,
            "erro": log.error_message
        }
        for log in logs
    ]
