"""
Task periódica: Atualizar métricas a cada 30 minutos.

- Calcula métricas gerais
- Calcula métricas por prioridade
- Obtém indicadores em tempo real
- Salva em cache para dashboard
- Tratamento robusto de erros com logging
"""

import logging
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from ti.modules.sla.services import MetricasService, CacheService
from ti.modules.sla.utils import CACHE_TTL_METRICAS

logger = logging.getLogger("sla.tasks")

def atualizar_metricas_tarefa(db: Session) -> None:
    """
    Atualiza métricas de SLA e salva em cache.

    Calcula:
    - Métricas do dia
    - Métricas da semana
    - Métricas do mês
    - Indicadores em tempo real

    Erros são capturados para não interromper o sistema.
    """
    try:
        metricas = MetricasService(db)
        cache = CacheService(db)

        agora = datetime.utcnow()
        hoje = agora.date()

        logger.info("[TASK atualizar_metricas] Iniciando atualização de métricas")

        # Métricas do dia
        try:
            metricas_hoje = metricas.obter_metricas_periodo(hoje, hoje)
            cache.salvar(
                "metricas_dia",
                {
                    "periodo": "dia",
                    "data": hoje.isoformat(),
                    "metricas": metricas_hoje,
                    "atualizado_em": agora.isoformat()
                },
                ttl_minutos=CACHE_TTL_METRICAS
            )
            logger.info(f"[TASK atualizar_metricas] Dia: {metricas_hoje.get('taxa_cumprimento', 0):.1f}% cumprimento")
        except Exception as e:
            logger.error(f"[TASK atualizar_metricas] Erro ao calcular métricas do dia: {e}", exc_info=True)

        # Métricas da semana
        try:
            inicio_semana = hoje - timedelta(days=hoje.weekday())
            fim_semana = hoje
            metricas_semana = metricas.obter_metricas_periodo(inicio_semana, fim_semana)
            cache.salvar(
                "metricas_semana",
                {
                    "periodo": "semana",
                    "data_inicio": inicio_semana.isoformat(),
                    "data_fim": fim_semana.isoformat(),
                    "metricas": metricas_semana,
                    "atualizado_em": agora.isoformat()
                },
                ttl_minutos=CACHE_TTL_METRICAS
            )
            logger.info(f"[TASK atualizar_metricas] Semana: {metricas_semana.get('taxa_cumprimento', 0):.1f}% cumprimento")
        except Exception as e:
            logger.error(f"[TASK atualizar_metricas] Erro ao calcular métricas da semana: {e}", exc_info=True)

        # Métricas do mês
        try:
            inicio_mes = hoje.replace(day=1)
            fim_mes = hoje
            metricas_mes = metricas.obter_metricas_periodo(inicio_mes, fim_mes)
            cache.salvar(
                "metricas_mes",
                {
                    "periodo": "mês",
                    "data_inicio": inicio_mes.isoformat(),
                    "data_fim": fim_mes.isoformat(),
                    "metricas": metricas_mes,
                    "atualizado_em": agora.isoformat()
                },
                ttl_minutos=CACHE_TTL_METRICAS
            )
            logger.info(f"[TASK atualizar_metricas] Mês: {metricas_mes.get('taxa_cumprimento', 0):.1f}% cumprimento")
        except Exception as e:
            logger.error(f"[TASK atualizar_metricas] Erro ao calcular métricas do mês: {e}", exc_info=True)

        # Métricas por prioridade
        try:
            metricas_por_prioridade = metricas.obter_metricas_por_prioridade(hoje, hoje)
            cache.salvar(
                "metricas_por_prioridade",
                metricas_por_prioridade,
                ttl_minutos=CACHE_TTL_METRICAS
            )
            logger.debug("[TASK atualizar_metricas] Métricas por prioridade salvas em cache")
        except Exception as e:
            logger.error(f"[TASK atualizar_metricas] Erro ao calcular métricas por prioridade: {e}", exc_info=True)

        # Indicadores em tempo real
        try:
            indicadores = metricas.obter_indicadores_agora()
            cache.salvar(
                "indicadores_agora",
                {
                    "indicadores": indicadores,
                    "atualizado_em": agora.isoformat()
                },
                ttl_minutos=5  # Maior frequência para indicadores
            )
            logger.info(
                f"[TASK atualizar_metricas] Indicadores: "
                f"{indicadores.get('abertos', 0)} abertos, "
                f"{indicadores.get('em_atendimento', 0)} em atendimento, "
                f"{indicadores.get('em_risco', 0)} em risco, "
                f"{indicadores.get('vencidos', 0)} vencidos"
            )
        except Exception as e:
            logger.error(f"[TASK atualizar_metricas] Erro ao calcular indicadores: {e}", exc_info=True)

        logger.info("[TASK atualizar_metricas] Atualização de métricas concluída com sucesso")

    except Exception as e:
        logger.error(
            f"[TASK atualizar_metricas] Erro fatal na atualização de métricas: {e}",
            exc_info=True
        )
