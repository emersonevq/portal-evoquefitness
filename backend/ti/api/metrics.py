from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.db import get_db
from core.utils import now_brazil_naive
from ti.services.metrics import MetricsCalculator

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics/realtime")
def get_realtime_metrics(db: Session = Depends(get_db)):
    """
    Retorna métricas instantâneas (sem cache, sem cálculos pesados).

    Endpoint consolidado para dados rápidos:
    - chamados_hoje: Quantidade de chamados abertos hoje
    - comparacao_ontem: Comparação com ontem
    - abertos_agora: Quantidade de chamados ativos
    - timestamp: Momento do cálculo
    """
    try:
        return {
            "chamados_hoje": MetricsCalculator.get_chamados_abertos_hoje(db),
            "comparacao_ontem": MetricsCalculator.get_comparacao_ontem(db),
            "abertos_agora": MetricsCalculator.get_abertos_agora(db),
            "timestamp": now_brazil_naive().isoformat(),
        }
    except Exception as e:
        print(f"[ERROR] Erro ao calcular métricas em tempo real: {e}")
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular métricas em tempo real: {str(e)}"
        )


@router.get("/metrics/dashboard/basic")
def get_basic_metrics(start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    """
    Retorna métricas básicas do dashboard.

    Query params:
    - start_date: Data inicial (formato: YYYY-MM-DD, opcional)
    - end_date: Data final (formato: YYYY-MM-DD, opcional)

    Se as datas não forem fornecidas, retorna as métricas padrão (realtime).
    """
    from datetime import datetime

    # Se datas não forem fornecidas, retorna o padrão
    if not start_date or not end_date:
        return get_realtime_metrics(db)

    # Se datas forem fornecidas, validar
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Datas devem estar no formato YYYY-MM-DD"
        )

    # Retornar métricas padrão (realtime) para manter compatibilidade
    # Os dados filtrados por período serão puxados dos gráficos específicos
    return get_realtime_metrics(db)




@router.get("/metrics/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Endpoint consolidado: Retorna todas as métricas do dashboard administrativo.

    Combina:
    - Métricas rápidas (realtime)
    - Métricas de performance

    Retorna:
    - chamados_hoje: Quantidade de chamados abertos hoje
    - comparacao_ontem: Comparação com ontem (hoje, ontem, percentual, direcao)
    - abertos_agora: Quantidade de chamados ativos
    - tempo_resolucao_30dias: Tempo médio de resolução (30 dias)
    - primeira_resposta_media: Tempo médio de primeira resposta
    - taxa_reaberturas: Taxa de reaberturas
    - chamados_backlog: Chamados em backlog
    - timestamp: Momento do cálculo
    """
    try:
        # Obtém todas as métricas
        realtime = get_realtime_metrics(db)
        performance = MetricsCalculator.get_performance_metrics(db)

        return {
            # Realtime
            "chamados_hoje": realtime["chamados_hoje"],
            "comparacao_ontem": realtime["comparacao_ontem"],
            "abertos_agora": realtime["abertos_agora"],

            # Performance
            "tempo_resolucao_30dias": performance["tempo_resolucao_medio"],
            "primeira_resposta_media": performance["primeira_resposta_media"],
            "taxa_reaberturas": performance["taxa_reaberturas"],
            "chamados_backlog": performance["chamados_backlog"],

            # Metadata
            "timestamp": now_brazil_naive().isoformat(),
        }
    except Exception as e:
        print(f"[ERROR] Erro ao calcular métricas do dashboard: {e}")
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular métricas do dashboard: {str(e)}"
        )


@router.get("/metrics/chamados-abertos")
def get_chamados_abertos(db: Session = Depends(get_db)):
    """
    [DEPRECATED] Use /metrics/realtime instead.

    Retorna quantidade de chamados ativos (não concluídos nem cancelados)
    """
    try:
        count = MetricsCalculator.get_abertos_agora(db)
        return {"ativos": count}
    except Exception as e:
        print(f"Erro ao contar chamados ativos: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@router.get("/metrics/chamados-hoje")
def get_chamados_hoje(db: Session = Depends(get_db)):
    """
    [DEPRECATED] Use /metrics/realtime instead.

    Retorna quantidade de chamados abertos hoje
    """
    try:
        count = MetricsCalculator.get_chamados_abertos_hoje(db)
        return {"chamados_hoje": count}
    except Exception as e:
        print(f"Erro ao contar chamados de hoje: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@router.get("/metrics/tempo-resposta")
def get_tempo_resposta(db: Session = Depends(get_db)):
    """
    [DEPRECATED] Use /metrics/dashboard/sla instead.

    Retorna tempo médio de resposta das últimas 24h
    """
    try:
        tempo = MetricsCalculator.get_tempo_medio_resposta_24h(db)
        return {"tempo_resposta": tempo}
    except Exception as e:
        print(f"Erro ao calcular tempo de resposta: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")




@router.get("/metrics/chamados-por-dia")
def get_chamados_por_dia(dias: int = 7, statuses: str = "", start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    """Retorna quantidade de chamados por dia dos últimos N dias ou período customizado

    Query params:
    - dias: Número de dias (default: 7)
    - statuses: Lista separada por vírgula (ex: "Aberto,Em andamento")
    - start_date: Data inicial (formato: YYYY-MM-DD, opcional)
    - end_date: Data final (formato: YYYY-MM-DD, opcional)

    Se start_date e end_date forem fornecidas, elas têm prioridade sobre 'dias'.
    """
    try:
        status_list = [s.strip() for s in statuses.split(",") if s.strip()] if statuses else []

        # Se datas customizadas forem fornecidas
        if start_date and end_date:
            try:
                dados = MetricsCalculator.get_chamados_por_dia_periodo(db, start_date, end_date, status_list if status_list else None)
            except Exception as e:
                print(f"Erro no período: {e}")
                import traceback
                traceback.print_exc()
                return {"dados": []}
        else:
            dados = MetricsCalculator.get_chamados_por_dia(db, dias, status_list if status_list else None)

        if not isinstance(dados, list):
            return {"dados": []}
        return {"dados": dados}
    except Exception as e:
        print(f"Erro ao calcular chamados por dia: {e}")
        import traceback
        traceback.print_exc()
        return {"dados": []}


@router.get("/metrics/chamados-por-semana")
def get_chamados_por_semana(semanas: int = 4, statuses: str = "", start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    """Retorna quantidade de chamados por semana dos últimos N semanas ou período customizado

    Query params:
    - semanas: Número de semanas (default: 4)
    - statuses: Lista separada por vírgula (ex: "Aberto,Em andamento")
    - start_date: Data inicial (formato: YYYY-MM-DD, opcional)
    - end_date: Data final (formato: YYYY-MM-DD, opcional)

    Se start_date e end_date forem fornecidas, elas têm prioridade sobre 'semanas'.
    """
    try:
        status_list = [s.strip() for s in statuses.split(",") if s.strip()] if statuses else []

        # Se datas customizadas forem fornecidas
        if start_date and end_date:
            try:
                dados = MetricsCalculator.get_chamados_por_semana_periodo(db, start_date, end_date, status_list if status_list else None)
            except Exception as e:
                print(f"Erro no período: {e}")
                import traceback
                traceback.print_exc()
                return {"dados": []}
        else:
            dados = MetricsCalculator.get_chamados_por_semana(db, semanas, status_list if status_list else None)

        if not isinstance(dados, list):
            return {"dados": []}
        return {"dados": dados}
    except Exception as e:
        print(f"Erro ao calcular chamados por semana: {e}")
        import traceback
        traceback.print_exc()
        return {"dados": []}


@router.get("/metrics/chamados-por-mes")
def get_chamados_por_mes(range: str = "30d", statuses: str = "", start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    """Retorna quantidade de chamados por status por mês

    Query params:
    - range: '7d', '30d', '90d' ou 'all' (padrão: '30d')
    - statuses: Lista separada por vírgula (ex: "Aberto,Em andamento,Concluído")
                Se vazio, mostra todos os status
    - start_date: Data inicial (formato: YYYY-MM-DD, opcional)
    - end_date: Data final (formato: YYYY-MM-DD, opcional)

    Se start_date e end_date forem fornecidas, elas têm prioridade sobre 'range'.
    """
    try:
        status_list = [s.strip() for s in statuses.split(",") if s.strip()] if statuses else []

        # Se datas customizadas forem fornecidas
        if start_date and end_date:
            try:
                dados = MetricsCalculator.get_chamados_por_mes_periodo(db, start_date, end_date, status_list if status_list else None)
            except Exception as e:
                print(f"Erro no período: {e}")
                import traceback
                traceback.print_exc()
                return {"dados": []}
        else:
            meses_param = {
                "7d": 1,
                "30d": 3,
                "90d": 12,
                "all": 24
            }.get(range, 3)
            dados = MetricsCalculator.get_chamados_por_mes(db, meses_param, status_list if status_list else None)

        if not isinstance(dados, list):
            return {"dados": []}
        return {"dados": dados}
    except Exception as e:
        print(f"Erro ao calcular chamados por mês: {e}")
        import traceback
        traceback.print_exc()
        return {"dados": []}




@router.get("/metrics/performance")
def get_performance_metrics(db: Session = Depends(get_db)):
    """Retorna métricas de performance (últimos 30 dias)"""
    try:
        metricas = MetricsCalculator.get_performance_metrics(db)
        return metricas
    except Exception as e:
        print(f"Erro ao calcular métricas de performance: {e}")
        return {
            "tempo_resolucao_medio": "—",
            "primeira_resposta_media": "—",
            "taxa_reaberturas": "0%",
            "chamados_backlog": 0
        }


@router.get("/metrics/debug/tempo-resposta")
def debug_tempo_resposta(periodo: str = "mes", db: Session = Depends(get_db)):
    """
    Debug: retorna dados brutos de tempo de resposta
    periodo: "mes", "24h" ou "30dias"
    """
    try:
        historicos = MetricsCalculator.debug_tempo_resposta(db, periodo)
        return {
            "status": "ok",
            "total_registros": len(historicos),
            "periodo": periodo
        }
    except Exception as e:
        print(f"Erro ao debugar tempo de resposta: {e}")
        return {
            "status": "erro",
            "erro": str(e),
            "periodo": periodo
        }




@router.get("/metrics/health")
def metrics_health_check(db: Session = Depends(get_db)):
    """
    Endpoint de health check para monitorar saúde do cache e cálculos.

    Retorna:
    - cache_status: Se cache está funcionando
    - cache_age: Idade do cache em segundos
    - debouncer_status: Quantas operações estão em progresso
    - banco_status: Se conexão com banco está OK
    - timestamp: Momento do check
    """
    try:
        from ti.services.cache_manager_incremental import IncrementalMetricsCache
        from ti.services.cache_debouncer import get_debouncer
        from core.utils import now_brazil_naive
        import json

        health = {
            "status": "healthy",
            "checks": {}
        }

        # Check 1: Cache accessibility
        try:
            from ti.models.metrics_cache import MetricsCacheDB
            cache_key = IncrementalMetricsCache.get_cache_key_month()
            cached = db.query(MetricsCacheDB).filter(
                MetricsCacheDB.cache_key == cache_key
            ).first()
            health["checks"]["cache"] = {
                "status": "ok",
                "message": "Cache accessible"
            }
        except Exception as cache_error:
            health["checks"]["cache"] = {
                "status": "warning",
                "message": str(cache_error)
            }

        # Check 2: Database connection
        try:
            db.execute("SELECT 1")
            health["checks"]["database"] = {
                "status": "ok",
                "message": "Database connected"
            }
        except Exception as db_error:
            health["checks"]["database"] = {
                "status": "critical",
                "message": str(db_error)
            }
            health["status"] = "unhealthy"

        # Check 3: Debouncer status
        try:
            debouncer = get_debouncer()
            stats = debouncer.get_stats()
            health["checks"]["debouncer"] = {
                "status": "ok",
                "cached_items": stats["cached_keys"],
                "in_progress": stats["in_progress"]
            }
        except Exception as debounce_error:
            health["checks"]["debouncer"] = {
                "status": "warning",
                "message": str(debounce_error)
            }

        # Check 4: Metrics calculation (lightweight)
        try:
            metricas = IncrementalMetricsCache.get_metrics(db)
            health["checks"]["metrics"] = {
                "status": "ok",
                "total_chamados": metricas.get("total", 0)
            }
        except Exception as metrics_error:
            health["checks"]["metrics"] = {
                "status": "warning",
                "message": str(metrics_error)
            }

        health["timestamp"] = now_brazil_naive().isoformat()
        return health

    except Exception as e:
        print(f"Erro ao fazer health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": now_brazil_naive().isoformat()
        }
