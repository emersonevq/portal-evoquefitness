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


def format_hours(hours: float) -> str:
    """Converte horas em formato legível (ex: 2.5h -> '2h 30m')"""
    if not hours:
        return "—"
    hours_int = int(hours)
    minutes = int((hours - hours_int) * 60)
    if hours_int == 0:
        return f"{minutes}m"
    elif minutes == 0:
        return f"{hours_int}h"
    else:
        return f"{hours_int}h {minutes}m"


@router.get("/dashboard/basic")
def get_dashboard_basic(
    range: str = Query("30d"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Dashboard básico com resumo geral de chamados.
    Retorna formato esperado pelo Overview.tsx

    FILTROS:
    - Ignora chamados retroativos (antes de 15-02-2026)
    - Conta apenas chamados de 15-02-2026+
    - Status abertos não contam para métricas de SLA (apenas para visão geral)
    """
    try:
        agora = now_brazil_naive()
        data_corte_2026 = datetime(2026, 2, 15)

        # Determinar período
        if start_date and end_date:
            try:
                data_inicio = datetime.fromisoformat(start_date).date()
                data_fim = datetime.fromisoformat(end_date).date()
            except:
                data_inicio = (agora - timedelta(days=30)).date()
                data_fim = agora.date()
        else:
            # Parse range (ex: "30d" = 30 dias, "3m" = 3 meses)
            if range.endswith("d"):
                dias = int(range[:-1])
            elif range.endswith("m"):
                meses = int(range[:-1])
                dias = 30 * meses
            else:
                dias = 30

            data_inicio = (agora - timedelta(days=dias)).date()
            data_fim = agora.date()

        # Contar chamados de hoje (apenas 2026+, não retroativos)
        chamados_hoje = db.query(func.count(Chamado.id)).filter(
            func.date(Chamado.data_abertura) == agora.date(),
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).scalar() or 0

        # Contar chamados de ontem (apenas 2026+, não retroativos)
        ontem = agora.date() - timedelta(days=1)
        chamados_ontem = db.query(func.count(Chamado.id)).filter(
            func.date(Chamado.data_abertura) == ontem,
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).scalar() or 0

        # Calcular percentual de mudança
        percentual = 0
        direcao = "up"
        if chamados_ontem > 0:
            percentual = ((chamados_hoje - chamados_ontem) / chamados_ontem * 100)
        elif chamados_hoje > 0:
            percentual = 100

        direcao = "up" if percentual >= 0 else "down"

        # Contar por status (apenas 2026+, não retroativos)
        em_atendimento = db.query(func.count(Chamado.id)).filter(
            Chamado.status.in_(["Em atendimento", "Em Atendimento"]),
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).scalar() or 0

        concluidos = db.query(func.count(Chamado.id)).filter(
            Chamado.status.in_(["Concluído", "Concluido"]),
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).scalar() or 0

        # Em risco: apenas chamados CONCLUÍDOS de 2026+ que NÃO cumpriram SLA
        em_risco = db.query(func.count(Chamado.id)).filter(
            Chamado.sla_em_risco == True,
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).scalar() or 0

        return {
            "chamados_hoje": chamados_hoje,
            "em_atendimento": em_atendimento,
            "concluidos": concluidos,
            "em_risco": em_risco,
            "comparacao_ontem": {
                "hoje": chamados_hoje,
                "ontem": chamados_ontem,
                "percentual": round(percentual, 1),
                "direcao": direcao
            },
            "status": "ok"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "chamados_hoje": 0,
            "em_atendimento": 0,
            "concluidos": 0,
            "em_risco": 0,
            "comparacao_ontem": {"hoje": 0, "ontem": 0, "percentual": 0, "direcao": "up"},
            "status": "error",
            "error": str(e)
        }


@router.get("/chamados-por-dia")
def get_chamados_por_dia(
    dias: int = Query(7, ge=1, le=90),
    statuses: str = Query("Aberto,Em atendimento,Concluído"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retorna chamados por dia nos últimos N dias.
    Formato esperado pelo Overview.tsx
    FILTRO: Apenas chamados de 2026+, não retroativos
    """
    try:
        agora = now_brazil_naive()
        data_corte_2026 = datetime(2026, 2, 15)

        # Determinar período
        if start_date and end_date:
            try:
                data_inicio = datetime.fromisoformat(start_date).date()
                data_fim = datetime.fromisoformat(end_date).date()
            except:
                data_inicio = (agora - timedelta(days=dias)).date()
                data_fim = agora.date()
        else:
            data_inicio = (agora - timedelta(days=dias)).date()
            data_fim = agora.date()

        status_list = [s.strip() for s in statuses.split(",")]

        # Query todos os chamados no período (2026+, não retroativos)
        chamados = db.query(Chamado).filter(
            func.date(Chamado.data_abertura) >= data_inicio,
            func.date(Chamado.data_abertura) <= data_fim,
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).all()

        # Organizar por data
        resultado_dict = {}
        for chamado in chamados:
            data = chamado.data_abertura.date().isoformat() if hasattr(chamado.data_abertura, 'date') else chamado.data_abertura.isoformat()

            if data not in resultado_dict:
                resultado_dict[data] = {
                    "dia": data,
                    "aberto": 0,
                    "em_atendimento": 0,
                    "aguardando": 0,
                    "concluido": 0,
                    "expirado": 0
                }

            status = chamado.status or ""

            if "Aberto" in status:
                resultado_dict[data]["aberto"] += 1
            elif "atendimento" in status.lower():
                resultado_dict[data]["em_atendimento"] += 1
            elif "Aguardando" in status:
                resultado_dict[data]["aguardando"] += 1
            elif "Concluído" in status or "Concluido" in status:
                resultado_dict[data]["concluido"] += 1
            elif "Expirado" in status:
                resultado_dict[data]["expirado"] += 1

        # Ordenar por data
        dados = sorted(resultado_dict.values(), key=lambda x: x["dia"])

        return {
            "dados": dados,
            "status": "ok"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "dados": [],
            "status": "error",
            "error": str(e)
        }


@router.get("/chamados-por-semana")
def get_chamados_por_semana(
    semanas: int = Query(4, ge=1, le=52),
    statuses: str = Query("Aberto,Em atendimento,Concluído"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retorna chamados por semana nos últimos N semanas.
    Formato esperado pelo Overview.tsx
    FILTRO: Apenas chamados de 2026+, não retroativos
    """
    try:
        agora = now_brazil_naive()
        data_corte_2026 = datetime(2026, 2, 15)

        # Determinar período
        if start_date and end_date:
            try:
                data_inicio = datetime.fromisoformat(start_date).date()
                data_fim = datetime.fromisoformat(end_date).date()
            except:
                data_inicio = (agora - timedelta(weeks=semanas)).date()
                data_fim = agora.date()
        else:
            data_inicio = (agora - timedelta(weeks=semanas)).date()
            data_fim = agora.date()

        status_list = [s.strip() for s in statuses.split(",")]

        # Query todos os chamados no período (2026+, não retroativos)
        chamados = db.query(Chamado).filter(
            func.date(Chamado.data_abertura) >= data_inicio,
            func.date(Chamado.data_abertura) <= data_fim,
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).all()

        # Organizar por semana (usando ISO week)
        resultado_dict = {}
        for chamado in chamados:
            data = chamado.data_abertura.date() if hasattr(chamado.data_abertura, 'date') else chamado.data_abertura
            semana_iso = data.isocalendar()
            semana_key = f"{semana_iso[0]}-W{semana_iso[1]:02d}"
            
            if semana_key not in resultado_dict:
                resultado_dict[semana_key] = {
                    "semana": semana_key,
                    "aberto": 0,
                    "em_atendimento": 0,
                    "aguardando": 0,
                    "concluido": 0,
                    "expirado": 0
                }
            
            status = chamado.status or ""
            
            if "Aberto" in status:
                resultado_dict[semana_key]["aberto"] += 1
            elif "atendimento" in status:
                resultado_dict[semana_key]["em_atendimento"] += 1
            elif "Aguardando" in status:
                resultado_dict[semana_key]["aguardando"] += 1
            elif "Concluído" in status or "Conclu" in status:
                resultado_dict[semana_key]["concluido"] += 1
            elif "Expirado" in status:
                resultado_dict[semana_key]["expirado"] += 1

        # Ordenar por semana
        dados = sorted(resultado_dict.values(), key=lambda x: x["semana"])

        return {
            "dados": dados,
            "status": "ok"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "dados": [],
            "status": "error",
            "error": str(e)
        }


@router.get("/chamados-por-mes")
def get_chamados_por_mes(
    range: str = Query("30d"),
    statuses: str = Query("Aberto,Em atendimento,Concluído"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retorna chamados por mês.
    Formato esperado pelo Overview.tsx
    FILTRO: Apenas chamados de 2026+, não retroativos
    """
    try:
        agora = now_brazil_naive()
        data_corte_2026 = datetime(2026, 2, 15)

        # Determinar período
        if start_date and end_date:
            try:
                data_inicio = datetime.fromisoformat(start_date).date()
                data_fim = datetime.fromisoformat(end_date).date()
            except:
                data_inicio = (agora - timedelta(days=30)).date()
                data_fim = agora.date()
        else:
            if range.endswith("d"):
                dias = int(range[:-1])
            elif range.endswith("m"):
                meses = int(range[:-1])
                dias = 30 * meses
            else:
                dias = 30

            data_inicio = (agora - timedelta(days=dias)).date()
            data_fim = agora.date()

        status_list = [s.strip() for s in statuses.split(",")]

        # Query todos os chamados no período (2026+, não retroativos)
        chamados = db.query(Chamado).filter(
            func.date(Chamado.data_abertura) >= data_inicio,
            func.date(Chamado.data_abertura) <= data_fim,
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).all()

        # Organizar por mês
        resultado_dict = {}
        for chamado in chamados:
            data = chamado.data_abertura.date() if hasattr(chamado.data_abertura, 'date') else chamado.data_abertura
            mes_key = data.strftime("%Y-%m")
            
            if mes_key not in resultado_dict:
                resultado_dict[mes_key] = {
                    "mes": mes_key,
                    "aberto": 0,
                    "em_atendimento": 0,
                    "aguardando": 0,
                    "concluido": 0,
                    "expirado": 0
                }
            
            status = chamado.status or ""
            
            if "Aberto" in status:
                resultado_dict[mes_key]["aberto"] += 1
            elif "atendimento" in status:
                resultado_dict[mes_key]["em_atendimento"] += 1
            elif "Aguardando" in status:
                resultado_dict[mes_key]["aguardando"] += 1
            elif "Concluído" in status or "Conclu" in status:
                resultado_dict[mes_key]["concluido"] += 1
            elif "Expirado" in status:
                resultado_dict[mes_key]["expirado"] += 1

        # Ordenar por mês
        dados = sorted(resultado_dict.values(), key=lambda x: x["mes"])

        return {
            "dados": dados,
            "status": "ok"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "dados": [],
            "status": "error",
            "error": str(e)
        }


@router.get("/performance")
def get_performance_metrics(db: Session = Depends(get_db)):
    """
    Retorna métricas de performance no formato esperado pelo Overview.tsx
    Usa os campos SLA já calculados (horário comercial, respeitando pausas)

    FILTROS:
    - Apenas chamados concluídos de 2026+ (não retroativos)
    - Ignora chamados abertos/em pausa (não geram métrica de resolução)
    """
    try:
        agora = now_brazil_naive()
        data_corte_2026 = datetime(2026, 2, 15)

        # Chamados concluídos de 2026+ (não retroativos)
        concluidos = db.query(Chamado).filter(
            Chamado.status.in_(["Concluído", "Concluido"]),
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).all()

        # Tempo médio de resolução USANDO O CAMPO SLA JÁ CALCULADO
        # sla_tempo_decorrido_horas já considera horário comercial e pausas
        tempos_resolucao = []
        for c in concluidos:
            if c.sla_tempo_decorrido_horas and c.sla_tempo_decorrido_horas > 0:
                tempos_resolucao.append(c.sla_tempo_decorrido_horas)

        tempo_resolucao_medio = sum(tempos_resolucao) / len(tempos_resolucao) if tempos_resolucao else 0
        tempo_resolucao_formatado = format_hours(tempo_resolucao_medio)

        # Primeira resposta média (tempo até primeira_resposta)
        tempos_primeira_resposta = []
        for c in concluidos:
            if c.data_primeira_resposta and c.data_abertura:
                # Usar o tempo bruto de primeira resposta
                tempo_hrs = (c.data_primeira_resposta - c.data_abertura).total_seconds() / 3600
                tempos_primeira_resposta.append(tempo_hrs)

        primeira_resposta_media = sum(tempos_primeira_resposta) / len(tempos_primeira_resposta) if tempos_primeira_resposta else 0
        primeira_resposta_formatada = format_hours(primeira_resposta_media)

        # Taxa de reaberturas (chamados reabertos / total concluídos de 2026+)
        total_concluidos = len(concluidos)
        reabertos = 0
        for c in concluidos:
            if c.reaberto or c.numero_reaberturas > 0:
                reabertos += 1

        taxa_reaberturas = (reabertos / total_concluidos * 100) if total_concluidos > 0 else 0
        taxa_reaberturas_formatada = f"{taxa_reaberturas:.1f}%"

        # Chamados em backlog (abertos/em atendimento/aguardando de 2026+, não retroativos)
        chamados_backlog = db.query(func.count(Chamado.id)).filter(
            Chamado.status.in_(["Aberto", "Em atendimento", "Em Atendimento", "Aguardando"]),
            Chamado.data_abertura >= data_corte_2026,
            Chamado.retroativo != True,
            Chamado.deletado_em == None
        ).scalar() or 0

        return {
            "tempo_resolucao_medio": tempo_resolucao_formatado,
            "primeira_resposta_media": primeira_resposta_formatada,
            "taxa_reaberturas": taxa_reaberturas_formatada,
            "chamados_backlog": chamados_backlog,
            "status": "ok"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "tempo_resolucao_medio": "—",
            "primeira_resposta_media": "—",
            "taxa_reaberturas": "0%",
            "chamados_backlog": 0,
            "status": "error",
            "error": str(e)
        }
