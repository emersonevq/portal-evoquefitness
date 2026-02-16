from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class HistoricoSlaResponse(BaseModel):
    id: int
    chamado_id: int
    usuario_id: Optional[int] = None
    acao: str
    status_anterior: Optional[str] = None
    status_novo: Optional[str] = None
    data_conclusao_anterior: Optional[datetime] = None
    data_conclusao_nova: Optional[datetime] = None
    tempo_resposta_horas: Optional[float] = None
    limite_sla_resposta_horas: Optional[float] = None
    tempo_resolucao_horas: Optional[float] = None
    limite_sla_horas: Optional[float] = None
    status_sla: Optional[str] = None  # 'dentro', 'fora'
    observacoes: Optional[str] = None
    data_criacao: datetime
    criado_em: datetime

    class Config:
        from_attributes = True

class HistoricoSlaListResponse(BaseModel):
    total: int
    items: list[HistoricoSlaResponse]
