from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ConfiguracesSlaCreate(BaseModel):
    prioridade: str
    tempo_primeira_resposta: float = Field(..., description="Tempo em horas")
    tempo_resolucao: float = Field(..., description="Tempo em horas")
    considera_horario_comercial: bool = True
    considera_feriados: bool = True
    escalar_automaticamente: bool = True
    notificar_em_risco: bool = True
    percentual_risco: float = Field(75.0, ge=0, le=100)
    ativo: bool = True

class ConfiguracesSlaUpdate(BaseModel):
    prioridade: Optional[str] = None
    tempo_primeira_resposta: Optional[float] = None
    tempo_resolucao: Optional[float] = None
    considera_horario_comercial: Optional[bool] = None
    considera_feriados: Optional[bool] = None
    escalar_automaticamente: Optional[bool] = None
    notificar_em_risco: Optional[bool] = None
    percentual_risco: Optional[float] = None
    ativo: Optional[bool] = None

class ConfiguracesSlaResponse(BaseModel):
    id: int
    prioridade: str
    tempo_primeira_resposta: float
    tempo_resolucao: float
    considera_horario_comercial: bool
    considera_feriados: bool
    escalar_automaticamente: bool
    notificar_em_risco: bool
    percentual_risco: float
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime
    usuario_atualizacao: Optional[int] = None

    class Config:
        from_attributes = True
