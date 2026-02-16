"""
Task periódica: Atualizar métricas a cada 30 minutos.

- Calcula métricas gerais
- Calcula métricas por prioridade
- Obtém indicadores em tempo real
- Salva em cache para dashboard
"""

from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from ti.modules.sla.services import MetricasService, CacheService
from ti.modules.sla.utils import CACHE_TTL_METRICAS

def atualizar_metricas_tarefa(db: Session) -> None:
    """
    Atualiza métricas de SLA e salva em cache.
    
    Calcula:
    - Métricas do dia
    - Métricas da semana
    - Métricas do mês
    - Indicadores em tempo real
    """
    metricas = MetricasService(db)
    cache = CacheService(db)
    
    agora = datetime.utcnow()
    hoje = agora.date()
    
    print("[TASK] Atualizando métricas de SLA...")
    
    # Métricas do dia
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
    print(f"[TASK] Métricas do dia: {metricas_hoje['taxa_cumprimento']:.1f}% cumprimento")
    
    # Métricas da semana
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
    print(f"[TASK] Métricas da semana: {metricas_semana['taxa_cumprimento']:.1f}% cumprimento")
    
    # Métricas do mês
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
    print(f"[TASK] Métricas do mês: {metricas_mes['taxa_cumprimento']:.1f}% cumprimento")
    
    # Métricas por prioridade
    metricas_por_prioridade = metricas.obter_metricas_por_prioridade(hoje, hoje)
    cache.salvar(
        "metricas_por_prioridade",
        metricas_por_prioridade,
        ttl_minutos=CACHE_TTL_METRICAS
    )
    
    # Indicadores em tempo real
    indicadores = metricas.obter_indicadores_agora()
    cache.salvar(
        "indicadores_agora",
        {
            "indicadores": indicadores,
            "atualizado_em": agora.isoformat()
        },
        ttl_minutos=5  # Maior frequência para indicadores
    )
    print(f"[TASK] Indicadores: {indicadores['abertos']} abertos, "
          f"{indicadores['em_atendimento']} em atendimento, "
          f"{indicadores['em_risco']} em risco, "
          f"{indicadores['vencidos']} vencidos")
    
    print("[TASK] Atualização de métricas concluída")
