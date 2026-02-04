from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List


# ==================== Configuração ====================

class SlaConfigBase(BaseModel):
    prioridade: str = Field(..., min_length=1, max_length=50)
    tempo_resposta_horas: float = Field(..., ge=0)
    tempo_resolucao_horas: float = Field(..., ge=0)
    descricao: Optional[str] = None
    ativo: bool = True
    
    @field_validator('tempo_resolucao_horas')
    @classmethod
    def validar_resolucao_maior_que_resposta(cls, v, info):
        if 'tempo_resposta_horas' in info.data:
            if v < info.data['tempo_resposta_horas']:
                raise ValueError('Tempo de resolução deve ser maior ou igual ao tempo de resposta')
        return v


class SlaConfigCreate(SlaConfigBase):
    pass


class SlaConfigUpdate(BaseModel):
    tempo_resposta_horas: Optional[float] = Field(None, ge=0)
    tempo_resolucao_horas: Optional[float] = Field(None, ge=0)
    descricao: Optional[str] = None
    ativo: Optional[bool] = None


class SlaConfigResponse(SlaConfigBase):
    id: int
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== Feriados ====================

class FeriadoBase(BaseModel):
    data: datetime
    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = None
    ativo: bool = True


class FeriadoCreate(FeriadoBase):
    pass


class FeriadoResponse(FeriadoBase):
    id: int
    criado_em: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== Pausas ====================

class PausaResponse(BaseModel):
    id: int
    chamado_id: int
    pausado_em: datetime
    retomado_em: Optional[datetime] = None
    motivo: str
    duracao_minutos: Optional[int] = None
    ativa: bool
    
    class Config:
        from_attributes = True


class PausasChamadoResponse(BaseModel):
    chamado_id: int
    total_pausas: int
    pausas: List[PausaResponse]
    tempo_total_pausado_minutos: int
    tempo_total_pausado_horas: float
    pausa_ativa: bool


# ==================== Status Chamado SLA ====================

class SlaChamadoStatus(BaseModel):
    chamado_id: int
    codigo: str
    protocolo: Optional[str] = None
    prioridade: str
    status: str
    status_normalizado: str
    solicitante: Optional[str] = None
    unidade: Optional[str] = None
    problema: Optional[str] = None
    data_abertura: datetime
    
    # Métricas SLA
    tempo_limite_horas: float
    tempo_decorrido_horas: float
    tempo_pausado_horas: float = 0
    tempo_restante_horas: float
    percentual_consumido: float
    
    # Status
    em_risco: bool
    vencido: bool
    pausado: bool = False
    
    # Prazo
    prazo_limite: Optional[datetime] = None


# ==================== Dashboard ====================

class SlaDashboard(BaseModel):
    periodo_inicio: datetime
    periodo_fim: datetime
    
    total_chamados: int
    total_chamados_ativos: int
    total_chamados_concluidos: int
    
    dentro_sla_resposta: int
    fora_sla_resposta: int
    percentual_sla_resposta: float
    tempo_medio_resposta_horas: float
    
    dentro_sla_resolucao: int
    fora_sla_resolucao: int
    percentual_sla_resolucao: float
    tempo_medio_resolucao_horas: float
    
    chamados_em_risco: int
    chamados_vencidos: int
    chamados_pausados: int
    
    lista_em_risco: List[SlaChamadoStatus]
    lista_vencidos: List[SlaChamadoStatus]
    lista_pausados: List[SlaChamadoStatus]
    
    ultima_atualizacao: datetime
    proximo_recalculo: Optional[datetime] = None


class SlaDashboardResumo(BaseModel):
    percentual_sla_resposta: float
    percentual_sla_resolucao: float
    chamados_em_risco: int
    chamados_vencidos: int
    chamados_pausados: int
    tempo_medio_resposta_horas: float
    tempo_medio_resolucao_horas: float
    ultima_atualizacao: datetime


# ==================== Mudança de Status ====================

class MudancaStatusRequest(BaseModel):
    chamado_id: int
    status_anterior: str
    status_novo: str
    usuario_id: Optional[int] = None


class MudancaStatusResponse(BaseModel):
    chamado_id: int
    status_anterior: str
    status_novo: str
    status_anterior_normalizado: str
    status_novo_normalizado: str
    acao_sla: Optional[str] = None
    pausa_id: Optional[int] = None
    tempo_pausado_minutos: Optional[int] = None
    mensagem: str


# ==================== Recálculo ====================

class RecalculoResponse(BaseModel):
    sucesso: bool
    chamados_processados: int
    chamados_atualizados: int
    chamados_em_risco: int
    chamados_vencidos: int
    chamados_pausados: int
    tempo_execucao_ms: float
    timestamp: datetime
    erro: Optional[str] = None


# ==================== Scheduler ====================

class SchedulerJob(BaseModel):
    id: str
    name: str
    next_run: Optional[str] = None
    interval_minutes: float


class SchedulerStatus(BaseModel):
    running: bool
    jobs: List[SchedulerJob]
    ultima_execucao: Optional[datetime] = None
    ultimo_resultado: Optional[dict] = None
    config: dict
