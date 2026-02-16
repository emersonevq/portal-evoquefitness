from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SlaPrioridadeMetrica(BaseModel):
    prioridade: str
    total_chamados: int
    cumprimento: float  # percentual
    tempo_resposta_medio: float  # horas
    tempo_resolucao_medio: float  # horas
    chamados_em_risco: int
    chamados_vencidos: int

class SlaMetricasGerais(BaseModel):
    periodo: str  # 'hoje', 'semana', 'mes', 'ano'
    data_calculo: datetime
    total_chamados: int
    chamados_concluidos: int
    chamados_em_risco: int
    chamados_vencidos: int
    taxa_cumprimento_geral: float  # percentual
    tempo_resposta_medio: float  # horas
    tempo_resolucao_medio: float  # horas
    tempo_pausa_total: float  # horas
    metricas_por_prioridade: list[SlaPrioridadeMetrica]

class SlaIndicadores(BaseModel):
    chamados_abertos_agora: int
    chamados_em_atendimento_agora: int
    chamados_em_risco_agora: int
    chamados_vencidos_agora: int
    chamados_aguardando_agora: int

class SlaDashboardResponse(BaseModel):
    metricas_gerais: SlaMetricasGerais
    indicadores: SlaIndicadores
    data_atualizacao: datetime

    class Config:
        from_attributes = True
