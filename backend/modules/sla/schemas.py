"""Schemas Pydantic para API do SLA"""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


# ========== SLA Configuration ==========

class SlaConfigBase(BaseModel):
    prioridade: str
    tempo_resposta_horas: float
    tempo_resolucao_horas: float
    descricao: Optional[str] = None
    ativo: bool = True


class SlaConfigCreate(SlaConfigBase):
    pass


class SlaConfigUpdate(BaseModel):
    tempo_resposta_horas: Optional[float] = None
    tempo_resolucao_horas: Optional[float] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None


class SlaConfig(SlaConfigBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime
    ultimo_reset_em: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Feriados ==========

class SlaFeriadoBase(BaseModel):
    data: datetime
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True


class SlaFeriadoCreate(SlaFeriadoBase):
    pass


class SlaFeriado(SlaFeriadoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# ========== Pausas de SLA ==========

class SlaPausaBase(BaseModel):
    chamado_id: int
    pausado_em: datetime
    motivo: str = "Em análise"


class SlaPausaCreate(SlaPausaBase):
    criado_por_id: Optional[int] = None


class SlaPausaUpdate(BaseModel):
    retomado_em: datetime
    duracao_minutos: Optional[int] = None


class SlaPausa(SlaPausaBase):
    id: int
    retomado_em: Optional[datetime] = None
    duracao_minutos: Optional[int] = None
    ativa: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# ========== Status de um Chamado ==========

class SlaChamadoStatus(BaseModel):
    """Status SLA de um chamado específico"""
    chamado_id: int
    codigo: str
    prioridade: str
    status: str
    
    # Tempos em horas
    tempo_decorrido_horas: float
    tempo_pausado_horas: float
    tempo_limite_resposta_horas: float
    tempo_limite_resolucao_horas: float
    
    # Status
    resposta_em_dia: bool
    resposta_em_risco: bool
    resposta_vencida: bool
    
    resolucao_em_dia: bool
    resolucao_em_risco: bool
    resolucao_vencida: bool
    
    percentual_resposta: float
    percentual_resolucao: float
    
    pausado: bool
    ativo: bool


# ========== Dashboard ==========

class SlaDashboard(BaseModel):
    """Dashboard completo de SLA"""
    periodo_inicio: datetime
    periodo_fim: datetime
    
    # Contadores
    total_chamados: int
    chamados_ativos: int
    chamados_concluidos: int
    
    # Resposta
    chamados_resposta_ok: int
    chamados_resposta_risco: int
    chamados_resposta_vencido: int
    percentual_resposta_ok: float
    tempo_medio_resposta_horas: float
    
    # Resolução
    chamados_resolucao_ok: int
    chamados_resolucao_risco: int
    chamados_resolucao_vencido: int
    percentual_resolucao_ok: float
    tempo_medio_resolucao_horas: float
    
    # Alertas
    chamados_em_risco: int
    chamados_vencidos: int
    chamados_pausados: int
    
    # Detalhes
    lista_em_risco: List[SlaChamadoStatus] = []
    lista_vencidos: List[SlaChamadoStatus] = []
    lista_pausados: List[SlaChamadoStatus] = []
    
    ultima_atualizacao: datetime


class SlaDashboardResumo(BaseModel):
    """Resumo rápido do SLA"""
    percentual_resposta_ok: float
    percentual_resolucao_ok: float
    chamados_em_risco: int
    chamados_vencidos: int
    chamados_pausados: int
    tempo_medio_resposta_horas: float
    tempo_medio_resolucao_horas: float
    ultima_atualizacao: datetime


# ========== Scheduler Status ==========

class SchedulerStatus(BaseModel):
    """Status do scheduler"""
    ativo: bool
    proxima_execucao: Optional[datetime] = None
    ultima_execucao: Optional[datetime] = None
    total_execucoes: int = 0
    erros: int = 0
