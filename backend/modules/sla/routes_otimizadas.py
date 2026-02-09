"""
Endpoints otimizados para SLA
Retornam dados do cache para máxima performance
Atualizados automaticamente a cada 15 minutos
"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status, Depends
from sqlalchemy.orm import Session

from .cache_service import get_cache_manager
from .metrics import ServicoMetricasSLA
from .calculator import CalculadorSLA
from .models import Chamado
from .schemas import MetricasSLA

router_otimizado = APIRouter(prefix="/api/sla/cache", tags=["SLA - Cache Otimizado"])


def get_db() -> Session:
    """Dependência para obter sessão - implementar no seu projeto"""
    raise NotImplementedError("Implemente get_db()")


# ==================== Métricas Gerais (Rápido) ====================

@router_otimizado.get("/metricas")
def obter_metricas_cache(
    periodo_dias: int = Query(30, ge=7, le=90, description="Período em dias (7, 30, 60, 90)"),
):
    """
    Obtém métricas gerais de SLA do cache (MUITO RÁPIDO!)
    
    Atualizado a cada 15 minutos automaticamente
    
    Query params:
    - periodo_dias: 7, 30, 60 ou 90 dias
    """
    cache = get_cache_manager()
    
    data_fim = date.today()
    data_inicio = data_fim - timedelta(days=periodo_dias)
    
    # Tenta obter do cache
    metricas = cache.get_metricas_gerais(str(data_inicio), str(data_fim))
    
    if metricas is None:
        # Se não tem cache, retorna erro instruindo a usar endpoint que calcula
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache não disponível. Aguarde a próxima atualização automática (máx 15 min)"
        )
    
    return {
        "periodo": {
            "inicio": str(data_inicio),
            "fim": str(data_fim),
            "dias": periodo_dias
        },
        "metricas": metricas,
        "cache": {
            "fonte": "cache",
            "atualizado_em": metricas.get("cached_at", "desconhecido"),
            "tempo_resposta_ms": "<1ms"
        }
    }


# ==================== Métricas por Prioridade (Rápido) ====================

@router_otimizado.get("/metricas/por-prioridade")
def obter_metricas_prioridade_cache(
    periodo_dias: int = Query(30, ge=7, le=90),
):
    """
    Obtém métricas agrupadas por prioridade do cache
    
    Retorna dados em cache (ULTRA RÁPIDO!)
    """
    cache = get_cache_manager()
    
    data_fim = date.today()
    data_inicio = data_fim - timedelta(days=periodo_dias)
    
    metricas = cache.get_metricas_por_prioridade(str(data_inicio), str(data_fim))
    
    if metricas is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache não disponível"
        )
    
    return {
        "periodo_dias": periodo_dias,
        "por_prioridade": metricas,
        "total_prioridades": len(metricas)
    }


# ==================== Chamados em Risco (Rápido) ====================

@router_otimizado.get("/chamados/em-risco")
def obter_chamados_em_risco_cache():
    """
    Obtém TOP 50 chamados em risco do cache
    
    MUITO RÁPIDO: retorna dados pré-calculados
    Atualizado a cada 15 minutos
    """
    cache = get_cache_manager()
    
    chamados = cache.get_chamados_em_risco()
    
    if chamados is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache não disponível"
        )
    
    return {
        "total": len(chamados),
        "chamados": chamados,
        "alerta": "⚠️ " if len(chamados) > 0 else "✅ ",
        "mensagem": f"{len(chamados)} chamados precisam de atenção imediata"
    }


# ==================== Chamados Vencidos (Rápido) ====================

@router_otimizado.get("/chamados/vencidos")
def obter_chamados_vencidos_cache():
    """
    Obtém TOP 50 chamados com SLA vencido do cache
    
    CRÍTICO: estes chamados já passaram do prazo
    Retorna dados em cache (instantâneo)
    """
    cache = get_cache_manager()
    
    chamados = cache.get_chamados_vencidos()
    
    if chamados is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache não disponível"
        )
    
    return {
        "total": len(chamados),
        "chamados": chamados,
        "alerta": "🔴" if len(chamados) > 0 else "✅",
        "severidade": "CRÍTICA" if len(chamados) > 0 else "OK"
    }


# ==================== Dashboard Executivo (Rápido) ====================

@router_otimizado.get("/dashboard")
def obter_dashboard_cache():
    """
    Obtém dashboard executivo completo do cache
    
    Inclui:
    - Métricas gerais
    - Métricas por prioridade
    - Chamados em risco
    - Chamados vencidos
    - Observações e alertas
    
    Tempo de resposta: < 1ms (dados em cache)
    """
    cache = get_cache_manager()
    
    data_inicio = str(date.today() - timedelta(days=30))
    data_fim = str(date.today())
    
    dashboard = cache.get_dashboard(data_inicio, data_fim)
    
    if dashboard is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dashboard não disponível em cache"
        )
    
    # Adiciona informações de cache
    dashboard["cache_info"] = {
        "fonte": "cache",
        "atualizado_em": dashboard.get("cached_at", "desconhecido"),
        "proxima_atualizacao": "automática a cada 15 minutos",
        "tempo_resposta_ms": "<1"
    }
    
    return dashboard


# ==================== Cache Status ====================

@router_otimizado.get("/status")
def obter_status_cache():
    """
    Obtém status do cache e estatísticas
    
    Retorna:
    - Se cache está ativo
    - Estatísticas de hits/misses
    - Próxima atualização
    """
    cache = get_cache_manager()
    stats = cache.get_stats()
    
    return {
        "status": "ativo",
        "tipo_cache": "memória",
        "ttl_padrao_minutos": 15,
        "estatisticas": stats,
        "atualizacao_intervalo_minutos": 15
    }


# ==================== Atualizar Manualmente ====================

@router_otimizado.post("/atualizar")
def atualizar_sla_manualmente(db: Session = Depends(get_db)):
    """
    Força atualização imediata do cache de SLA
    
    Útil para quando o usuário clica no botão "Atualizar"
    Recalcula tudo e atualiza cache em segundos
    """
    from .scheduler import get_scheduler
    import logging
    
    logger = logging.getLogger("sla.api")
    
    try:
        logger.info("🔄 Atualização manual solicitada via API")
        
        # Obtém factory de sessão (você precisa fornecer isso)
        # Por enquanto usa a sessão fornecida
        
        # Atualiza tudo
        cache = get_cache_manager()
        servico = ServicoMetricasSLA(db)
        calculator = CalculadorSLA(db)
        
        # Recalcula SLAs
        stats = calculator.recalcular_todos()
        
        # Atualiza métricas
        periodos = [
            (date.today() - timedelta(days=7), date.today()),
            (date.today() - timedelta(days=30), date.today()),
            (date.today() - timedelta(days=60), date.today()),
            (date.today() - timedelta(days=90), date.today()),
        ]
        
        for data_inicio, data_fim in periodos:
            metricas = servico.obter_metricas_gerais(data_inicio, data_fim)
            cache.set_metricas_gerais(str(data_inicio), str(data_fim), metricas)
        
        # Atualiza alertas
        em_risco = servico.obter_chamados_em_risco()
        cache.set_chamados_em_risco(em_risco)
        
        vencidos = servico.obter_chamados_vencidos()
        cache.set_chamados_vencidos(vencidos)
        
        # Atualiza dashboard
        dashboard = servico.obter_dashboard_executivo()
        cache.set_dashboard(
            str(date.today() - timedelta(days=30)),
            str(date.today()),
            dashboard
        )
        
        return {
            "sucesso": True,
            "mensagem": "✅ SLA atualizado com sucesso",
            "timestamp": date.today().isoformat(),
            "dados_atualizados": {
                "chamados_processados": stats["total_processados"],
                "em_risco": stats["em_risco"],
                "vencidos": stats["vencidos"],
                "pausados": stats["pausados"]
            }
        }
    
    except Exception as e:
        logger.error(f"Erro ao atualizar SLA manualmente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar: {str(e)}"
        )


# ==================== SLA Individual ====================

@router_otimizado.get("/chamado/{chamado_id}")
def obter_sla_chamado_cache(
    chamado_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém SLA detalhado de um chamado do cache
    
    Se não estiver em cache, calcula e retorna
    Cache: 5 minutos
    """
    cache = get_cache_manager()
    
    # Tenta cache
    sla = cache.get_sla_chamado(chamado_id)
    
    if sla:
        return {
            "chamado_id": chamado_id,
            "sla": sla,
            "fonte": "cache"
        }
    
    # Se não tem cache, calcula
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    
    if not chamado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chamado {chamado_id} não encontrado"
        )
    
    calculator = CalculadorSLA(db)
    sla_info = calculator.calcular_sla(chamado)
    
    # Armazena em cache
    cache.set_sla_chamado(chamado_id, sla_info)
    
    return {
        "chamado_id": chamado_id,
        "sla": sla_info,
        "fonte": "calculado"
    }


# ==================== Limpar Cache ====================

@router_otimizado.post("/limpar")
def limpar_cache():
    """
    Limpa todo o cache de SLA
    
    Use apenas em caso de emergência
    O cache será reconstruído na próxima atualização automática (máx 15 min)
    """
    cache = get_cache_manager()
    cache.invalidar_tudo()
    
    return {
        "sucesso": True,
        "mensagem": "⚠️ Cache limpo completamente",
        "proxima_atualizacao": "automática em até 15 minutos"
    }
