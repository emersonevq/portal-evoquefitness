from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class SLAStatusEnum(str, Enum):
    """Estados de SLA mutuamente exclusivos"""
    CUMPRIDO = "cumprido"
    VIOLADO = "violado"
    DENTRO_PRAZO = "dentro_prazo"
    PROXIMO_VENCER = "proximo_vencer"
    VENCIDO_ATIVO = "vencido_ativo"
    PAUSADO = "pausado"
    SEM_SLA = "sem_sla"


class SLAConfigurationCreate(BaseModel):
    prioridade: str = Field(..., description="Nível de prioridade")
    tempo_resposta_horas: float = Field(..., gt=0, description="Tempo máximo de resposta em horas (deve ser positivo)")
    tempo_resolucao_horas: float = Field(..., gt=0, description="Tempo máximo de resolução em horas (deve ser positivo)")
    descricao: str | None = Field(None, description="Descrição da configuração")
    ativo: bool = Field(True, description="Se a configuração está ativa")

    @validator("tempo_resposta_horas", "tempo_resolucao_horas")
    def validate_positive_hours(cls, v):
        if v <= 0:
            raise ValueError("Tempo deve ser maior que zero")
        return v

    @validator("tempo_resolucao_horas")
    def validate_resolucao_maior_que_resposta(cls, v, values):
        if "tempo_resposta_horas" in values:
            if v < values["tempo_resposta_horas"]:
                raise ValueError("Tempo de resolução deve ser >= tempo de resposta")
        return v


class SLAConfigurationUpdate(BaseModel):
    tempo_resposta_horas: float | None = None
    tempo_resolucao_horas: float | None = None
    descricao: str | None = None
    ativo: bool | None = None


class SLAConfigurationOut(BaseModel):
    id: int
    prioridade: str
    tempo_resposta_horas: float
    tempo_resolucao_horas: float
    descricao: str | None
    ativo: bool
    criado_em: datetime | None
    atualizado_em: datetime | None

    class Config:
        from_attributes = True


class SLABusinessHoursCreate(BaseModel):
    dia_semana: int = Field(..., description="Dia da semana (0=segunda, 6=domingo)")
    hora_inicio: str = Field(..., description="Hora de início (HH:MM)")
    hora_fim: str = Field(..., description="Hora de término (HH:MM)")
    ativo: bool = Field(True, description="Se o horário está ativo")


class SLABusinessHoursOut(BaseModel):
    id: int
    dia_semana: int
    hora_inicio: str
    hora_fim: str
    ativo: bool
    criado_em: datetime | None
    atualizado_em: datetime | None

    class Config:
        from_attributes = True


class HistoricoSLAOut(BaseModel):
    id: int
    chamado_id: int
    usuario_id: int | None
    acao: str
    status_anterior: str | None
    status_novo: str | None
    data_conclusao_anterior: datetime | None
    data_conclusao_nova: datetime | None
    tempo_resolucao_horas: float | None
    limite_sla_horas: float | None
    status_sla: str | None
    criado_em: datetime | None

    class Config:
        from_attributes = True


class SLAStatusResponse(BaseModel):
    chamado_id: int
    prioridade: str
    status: str
    tempo_decorrido_horas: float
    tempo_resposta_limite_horas: float
    tempo_resolucao_limite_horas: float
    tempo_resposta_status: str
    tempo_resolucao_status: str
    data_abertura: datetime | None
    data_primeira_resposta: datetime | None
    data_conclusao: datetime | None
