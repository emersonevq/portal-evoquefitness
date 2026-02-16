"""
Routes para dashboard de SLA.
"""

from fastapi import APIRouter, Depends, Query
from datetime import date
from sqlalchemy.orm import Session
from ti.modules.sla.services import MetricasService, CacheService
from ti.schemas.sla_dashboard import SlaDashboardResponse, SlaMetricasGerais, SlaIndicadores
from core.db import get_db

router = APIRouter(prefix="/sla/dashboard", tags=["SLA - Dashboard"])

@router.get("/indicadores", response_model=SlaIndicadores)
def obter_indicadores(db: Session = Depends(get_db)):
    """Obtém indicadores em tempo real"""
    cache = CacheService(db)
    
    # Tenta obter do cache
    indicadores_cache = cache.obter("indicadores_agora")
    if indicadores_cache:
        return SlaIndicadores(**indicadores_cache.get("indicadores", {}))
    
    # Se não houver no cache, calcula
    metricas = MetricasService(db)
    indicadores = metricas.obter_indicadores_agora()
    
    return SlaIndicadores(**indicadores)

@router.get("/metricas", response_model=SlaMetricasGerais)
def obter_metricas(
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    db: Session = Depends(get_db)
):
    """Obtém métricas de SLA para um período"""
    metricas_service = MetricasService(db)
    cache = CacheService(db)
    
    # Determina o tipo de período para cache
    periodo_type = "periodo_customizado"
    if data_inicio == data_fim:
        periodo_type = "dia"
    
    # Tenta cache
    cache_key = f"metricas_{periodo_type}_{data_inicio}_{data_fim}"
    metricas_cache = cache.obter(cache_key)
    
    if metricas_cache and "metricas" in metricas_cache:
        metricas = metricas_cache["metricas"]
    else:
        metricas = metricas_service.obter_metricas_periodo(data_inicio, data_fim)
    
    # Obtém métricas por prioridade
    metricas_por_prioridade = metricas_service.obter_metricas_por_prioridade(
        data_inicio,
        data_fim
    )
    
    from ti.schemas.sla_dashboard import SlaPrioridadeMetrica
    
    prioridades_list = [
        SlaPrioridadeMetrica(
            prioridade=prio,
            total_chamados=dados["total"],
            cumprimento=dados["taxa_cumprimento"],
            tempo_resposta_medio=0.0,
            tempo_resolucao_medio=0.0,
            chamados_em_risco=0,
            chamados_vencidos=0
        )
        for prio, dados in metricas_por_prioridade.items()
    ]
    
    return SlaMetricasGerais(
        periodo=f"{data_inicio} a {data_fim}",
        data_calculo=None,
        total_chamados=metricas["total_chamados"],
        chamados_concluidos=metricas["total_chamados"],
        chamados_em_risco=0,
        chamados_vencidos=0,
        taxa_cumprimento_geral=metricas["taxa_cumprimento"],
        tempo_resposta_medio=metricas["tempo_resposta_medio"],
        tempo_resolucao_medio=metricas["tempo_resolucao_medio"],
        tempo_pausa_total=metricas["tempo_pausa_total"],
        metricas_por_prioridade=prioridades_list
    )

@router.get("/relatorio-diario")
def obter_relatorio_diario(db: Session = Depends(get_db)):
    """Obtém relatório de SLA do dia"""
    from datetime import date
    
    hoje = date.today()
    metricas_service = MetricasService(db)
    
    metricas = metricas_service.obter_metricas_periodo(hoje, hoje)
    indicadores = metricas_service.obter_indicadores_agora()
    metricas_por_prioridade = metricas_service.obter_metricas_por_prioridade(hoje, hoje)
    
    return {
        "data": hoje,
        "metricas": metricas,
        "indicadores": indicadores,
        "metricas_por_prioridade": metricas_por_prioridade
    }
