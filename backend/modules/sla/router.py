"""Endpoints da API de SLA"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from core.db import get_db
from .service import SlaService
from .scheduler import get_scheduler_status, executar_recalculo_manual
from .schemas import (
    SlaConfig, SlaConfigCreate,
    SlaFeriado, SlaFeriadoCreate,
    SlaDashboard, SlaDashboardResumo,
    SlaChamadoStatus
)

router = APIRouter(prefix="/sla", tags=["SLA"])


# ========== Dashboard ==========

@router.get("/dashboard", response_model=SlaDashboard)
async def obter_dashboard(
    data_inicio: datetime = None,
    data_fim: datetime = None,
    db: Session = Depends(get_db)
):
    """Obtém dashboard completo de SLA dos últimos 30 dias"""
    service = SlaService(db)
    return service.obter_dashboard(data_inicio, data_fim)


@router.get("/dashboard/resumo", response_model=SlaDashboardResumo)
async def obter_resumo_dashboard(
    db: Session = Depends(get_db)
):
    """Obtém resumo rápido de SLA"""
    service = SlaService(db)
    dashboard = service.obter_dashboard()
    
    return SlaDashboardResumo(
        percentual_resposta_ok=dashboard.percentual_resposta_ok,
        percentual_resolucao_ok=dashboard.percentual_resolucao_ok,
        chamados_em_risco=dashboard.chamados_em_risco,
        chamados_vencidos=dashboard.chamados_vencidos,
        chamados_pausados=dashboard.chamados_pausados,
        tempo_medio_resposta_horas=dashboard.tempo_medio_resposta_horas,
        tempo_medio_resolucao_horas=dashboard.tempo_medio_resolucao_horas,
        ultima_atualizacao=dashboard.ultima_atualizacao
    )


# ========== Configurações ==========

@router.get("/config", response_model=List[SlaConfig])
async def obter_configuracoes(db: Session = Depends(get_db)):
    """Obtém todas as configurações de SLA"""
    service = SlaService(db)
    configs = service.repo.obter_todas_configs()
    return [
        SlaConfig(
            id=c.id,
            prioridade=c.prioridade,
            tempo_resposta_horas=c.tempo_resposta_horas,
            tempo_resolucao_horas=c.tempo_resolucao_horas,
            descricao=c.descricao,
            ativo=c.ativo,
            criado_em=c.criado_em,
            atualizado_em=c.atualizado_em,
            ultimo_reset_em=c.ultimo_reset_em
        )
        for c in configs
    ]


@router.post("/config", response_model=SlaConfig)
async def criar_configuracao(
    config: SlaConfigCreate,
    db: Session = Depends(get_db)
):
    """Cria uma nova configuração de SLA"""
    service = SlaService(db)
    nova_config = service.repo.criar_config(
        config.prioridade,
        config.tempo_resposta_horas,
        config.tempo_resolucao_horas
    )
    return SlaConfig.from_orm(nova_config)


# ========== Feriados ==========

@router.get("/feriados", response_model=List[SlaFeriado])
async def obter_feriados(db: Session = Depends(get_db)):
    """Obtém todos os feriados cadastrados"""
    service = SlaService(db)
    feriados = service.repo.obter_feriados_ativo()
    return [SlaFeriado.from_orm(f) for f in feriados]


@router.post("/feriados", response_model=SlaFeriado)
async def criar_feriado(
    feriado: SlaFeriadoCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo feriado"""
    service = SlaService(db)
    novo_feriado = service.repo.criar_feriado(
        feriado.data,
        feriado.nome,
        feriado.descricao
    )
    # Invalidar cache
    service.cache.invalidate_feriados()
    return SlaFeriado.from_orm(novo_feriado)


@router.delete("/feriados/{feriado_id}", status_code=204)
async def deletar_feriado(
    feriado_id: int,
    db: Session = Depends(get_db)
):
    """Deleta um feriado"""
    from .models import SlaFeriado as SlaFeriadoModel
    
    feriado = db.query(SlaFeriadoModel).filter(SlaFeriadoModel.id == feriado_id).first()
    if not feriado:
        raise HTTPException(status_code=404, detail="Feriado não encontrado")
    
    db.delete(feriado)
    db.commit()
    
    # Invalidar cache
    service = SlaService(db)
    service.cache.invalidate_feriados()


# ========== Chamados ==========

@router.get("/chamado/{chamado_id}", response_model=SlaChamadoStatus)
async def obter_sla_chamado(
    chamado_id: int,
    db: Session = Depends(get_db)
):
    """Obtém SLA de um chamado específico"""
    from ti.models.chamado import Chamado
    
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    service = SlaService(db)
    sla_status = service.calcular_sla_chamado(
        chamado.id,
        chamado.data_abertura,
        chamado.data_primeira_resposta,
        chamado.data_conclusao,
        chamado.status,
        chamado.prioridade
    )
    
    if not sla_status:
        raise HTTPException(status_code=404, detail="SLA não calculado")
    
    return sla_status


# ========== Scheduler ==========

@router.get("/scheduler/status")
async def obter_status_scheduler():
    """Obtém status do scheduler"""
    return get_scheduler_status()


@router.post("/scheduler/executar")
async def executar_recalculo(db: Session = Depends(get_db)):
    """Executa recálculo manual de SLA"""
    try:
        executar_recalculo_manual()
        return {"status": "sucesso", "mensagem": "Recálculo executado"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== Cache ==========

@router.get("/cache/status")
async def obter_status_cache(db: Session = Depends(get_db)):
    """Obtém status do cache"""
    service = SlaService(db)
    return service.cache.get_status()


@router.post("/cache/invalidar", status_code=204)
async def invalidar_cache(db: Session = Depends(get_db)):
    """Invalida todo o cache"""
    service = SlaService(db)
    service.cache.invalidate_all()
