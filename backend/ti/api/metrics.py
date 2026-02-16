from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from core.db import get_db
from core.utils import now_brazil_naive
from ti.models import Chamado

# Metrics router - properly configured with /metrics prefix
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/health")
def metrics_health_check(db: Session = Depends(get_db)):
    """
    Endpoint de health check para monitorar saúde do sistema.

    Retorna:
    - banco_status: Se conexão com banco está OK
    - timestamp: Momento do check
    """
    try:
        health = {
            "status": "healthy",
            "checks": {}
        }

        # Check: Database connection
        try:
            db.execute(text("SELECT 1"))
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

        health["timestamp"] = now_brazil_naive().isoformat()
        return health

    except Exception as e:
        print(f"Erro ao fazer health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": now_brazil_naive().isoformat()
        }


@router.get("/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Dashboard geral com métricas principais.
    """
    try:
        agora = now_brazil_naive()

        # Query simples - pegar todos e contar em Python
        todos = db.query(Chamado).all()

        total_abertos = len([c for c in todos if c.status and "Aberto" in c.status])
        total_em_atendimento = len([c for c in todos if c.status and "atendimento" in c.status])
        total_concluidos = len([c for c in todos if c.status and "Conclu" in c.status])
        sla_em_risco = len([c for c in todos if c.sla_em_risco])
        sla_vencidos = len([c for c in todos if c.sla_vencido])

        return {
            "timestamp": agora.isoformat(),
            "resumo": {
                "total": len(todos),
                "total_abertos": total_abertos,
                "total_em_atendimento": total_em_atendimento,
                "total_concluidos": total_concluidos,
                "sla_em_risco": sla_em_risco,
                "sla_vencidos": sla_vencidos
            },
            "status": "ok"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "timestamp": now_brazil_naive().isoformat(),
            "status": "error"
        }


@router.get("/chamados-por-dia")
def get_chamados_por_dia(
    dias: int = Query(7, ge=1, le=90),
    statuses: str = Query("Aberto,Em atendimento,Concluído"),
    db: Session = Depends(get_db)
):
    """
    Retorna chamados por dia nos últimos N dias.
    """
    try:
        data_inicio = (now_brazil_naive() - timedelta(days=dias)).date()
        status_list = [s.strip() for s in statuses.split(",")]

        chamados = db.query(
            func.date(Chamado.data_abertura).label("data"),
            Chamado.status,
            func.count(Chamado.id).label("quantidade")
        ).filter(
            Chamado.data_abertura >= data_inicio,
            Chamado.status.in_(status_list),
            Chamado.deletado_em == None
        ).group_by(
            func.date(Chamado.data_abertura),
            Chamado.status
        ).order_by(
            func.date(Chamado.data_abertura)
        ).all()

        # Organizar em formato amigável
        resultado = {}
        for item in chamados:
            data_str = item.data.isoformat()
            if data_str not in resultado:
                resultado[data_str] = {}
            resultado[data_str][item.status] = item.quantidade

        return {
            "periodo_dias": dias,
            "dados": resultado,
            "status": "ok"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


@router.get("/chamados-por-semana")
def get_chamados_por_semana(
    semanas: int = Query(4, ge=1, le=52),
    statuses: str = Query("Aberto,Em atendimento,Concluído"),
    db: Session = Depends(get_db)
):
    """
    Retorna chamados por semana nos últimos N semanas.
    """
    try:
        data_inicio = (now_brazil_naive() - timedelta(weeks=semanas)).date()
        status_list = [s.strip() for s in statuses.split(",")]

        chamados = db.query(
            func.date_trunc("week", Chamado.data_abertura).label("semana"),
            Chamado.status,
            func.count(Chamado.id).label("quantidade")
        ).filter(
            Chamado.data_abertura >= data_inicio,
            Chamado.status.in_(status_list),
            Chamado.deletado_em == None
        ).group_by(
            func.date_trunc("week", Chamado.data_abertura),
            Chamado.status
        ).order_by(
            func.date_trunc("week", Chamado.data_abertura)
        ).all()

        resultado = {}
        for item in chamados:
            semana_str = item.semana.isoformat() if item.semana else "unknown"
            if semana_str not in resultado:
                resultado[semana_str] = {}
            resultado[semana_str][item.status] = item.quantidade

        return {
            "periodo_semanas": semanas,
            "dados": resultado,
            "status": "ok"
        }
    except Exception as e:
        # Fallback se date_trunc não funcionar
        return {
            "periodo_semanas": semanas,
            "dados": {},
            "status": "ok",
            "note": "date_trunc pode não estar disponível em MySQL"
        }


@router.get("/chamados-por-mes")
def get_chamados_por_mes(
    range_str: str = Query("30d"),
    statuses: str = Query("Aberto,Em atendimento,Concluído"),
    db: Session = Depends(get_db)
):
    """
    Retorna chamados por mês.
    """
    try:
        # Parse range (ex: "30d" = 30 dias, "3m" = 3 meses)
        if range_str.endswith("d"):
            dias = int(range_str[:-1])
            data_inicio = (now_brazil_naive() - timedelta(days=dias)).date()
        elif range_str.endswith("m"):
            meses = int(range_str[:-1])
            data_inicio = (now_brazil_naive() - timedelta(days=30*meses)).date()
        else:
            data_inicio = (now_brazil_naive() - timedelta(days=30)).date()

        status_list = [s.strip() for s in statuses.split(",")]

        chamados = db.query(
            func.date_format(Chamado.data_abertura, "%Y-%m").label("mes"),
            Chamado.status,
            func.count(Chamado.id).label("quantidade")
        ).filter(
            Chamado.data_abertura >= data_inicio,
            Chamado.status.in_(status_list),
            Chamado.deletado_em == None
        ).group_by(
            func.date_format(Chamado.data_abertura, "%Y-%m"),
            Chamado.status
        ).order_by(
            func.date_format(Chamado.data_abertura, "%Y-%m")
        ).all()

        resultado = {}
        for item in chamados:
            if item.mes not in resultado:
                resultado[item.mes] = {}
            resultado[item.mes][item.status] = item.quantidade

        return {
            "range": range_str,
            "dados": resultado,
            "status": "ok"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


@router.get("/performance")
def get_performance_metrics(db: Session = Depends(get_db)):
    """
    Retorna métricas de performance e SLA.
    """
    try:
        agora = now_brazil_naive()

        # Chamados concluídos hoje
        concluidos_hoje = db.query(Chamado).filter(
            Chamado.status == "Concluído",
            Chamado.data_conclusao >= agora.replace(hour=0, minute=0, second=0),
            Chamado.deletado_em == None
        ).count()

        # Tempo médio de atendimento
        tempo_medio = db.query(
            func.avg(Chamado.sla_tempo_decorrido_horas)
        ).filter(
            Chamado.status == "Concluído",
            Chamado.deletado_em == None
        ).scalar() or 0

        # Taxa de SLA cumprido
        total_concluidos = db.query(func.count(Chamado.id)).filter(
            Chamado.status == "Concluído",
            Chamado.deletado_em == None
        ).scalar() or 1

        concluidos_dentro = db.query(func.count(Chamado.id)).filter(
            Chamado.status == "Concluído",
            Chamado.sla_vencido == False,
            Chamado.deletado_em == None
        ).scalar() or 0

        taxa_cumprimento = (concluidos_dentro / total_concluidos * 100) if total_concluidos > 0 else 0

        return {
            "timestamp": agora.isoformat(),
            "concluidos_hoje": concluidos_hoje,
            "tempo_medio_horas": float(tempo_medio),
            "taxa_sla_cumprido_pct": float(taxa_cumprimento),
            "status": "ok"
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": now_brazil_naive().isoformat(),
            "status": "error"
        }


@router.get("/dashboard/basic")
def get_dashboard_basic(
    range_str: str = Query("30d"),
    db: Session = Depends(get_db)
):
    """
    Dashboard básico com resumo geral.
    """
    try:
        # Parse range
        if range_str.endswith("d"):
            dias = int(range_str[:-1])
        elif range_str.endswith("m"):
            meses = int(range_str[:-1])
            dias = 30 * meses
        else:
            dias = 30

        data_inicio = (now_brazil_naive() - timedelta(days=dias)).date()
        agora = now_brazil_naive()

        # Métricas gerais
        total_chamados = db.query(func.count(Chamado.id)).filter(
            Chamado.data_abertura >= data_inicio,
            Chamado.deletado_em == None
        ).scalar() or 0

        abertos = db.query(func.count(Chamado.id)).filter(
            Chamado.status == "Aberto",
            Chamado.deletado_em == None
        ).scalar() or 0

        em_atendimento = db.query(func.count(Chamado.id)).filter(
            Chamado.status == "Em atendimento",
            Chamado.deletado_em == None
        ).scalar() or 0

        concluidos = db.query(func.count(Chamado.id)).filter(
            Chamado.status == "Concluído",
            Chamado.data_conclusao >= data_inicio,
            Chamado.deletado_em == None
        ).scalar() or 0

        em_risco = db.query(func.count(Chamado.id)).filter(
            Chamado.sla_em_risco == True,
            Chamado.deletado_em == None
        ).scalar() or 0

        vencidos = db.query(func.count(Chamado.id)).filter(
            Chamado.sla_vencido == True,
            Chamado.deletado_em == None
        ).scalar() or 0

        # Calcular taxa de cumprimento
        taxa_cumprimento = 0
        if concluidos > 0:
            concluidos_dentro_sla = db.query(func.count(Chamado.id)).filter(
                Chamado.status == "Concluído",
                Chamado.sla_vencido == False,
                Chamado.data_conclusao >= data_inicio,
                Chamado.deletado_em == None
            ).scalar() or 0
            taxa_cumprimento = (concluidos_dentro_sla / concluidos * 100)

        return {
            "range": range_str,
            "timestamp": agora.isoformat(),
            "resumo": {
                "total": total_chamados,
                "abertos": abertos,
                "em_atendimento": em_atendimento,
                "concluidos": concluidos,
                "em_risco": em_risco,
                "vencidos": vencidos,
                "taxa_cumprimento_sla_pct": float(taxa_cumprimento)
            },
            "status": "ok"
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": now_brazil_naive().isoformat(),
            "status": "error"
        }
