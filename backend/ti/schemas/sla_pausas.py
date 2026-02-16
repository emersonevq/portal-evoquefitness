from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SlaPausaCreate(BaseModel):
    chamado_id: int
    motivo: Optional[str] = None

class SlaPausaRetoma(BaseModel):
    pausa_id: int

class SlaPausaResponse(BaseModel):
    id: int
    chamado_id: int
    pausado_em: datetime
    retomado_em: Optional[datetime] = None
    motivo: Optional[str] = None
    duracao_minutos: Optional[float] = None
    criado_por_id: Optional[int] = None
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True

class SlaPausaListResponse(BaseModel):
    id: int
    chamado_id: int
    pausado_em: datetime
    retomado_em: Optional[datetime] = None
    motivo: Optional[str] = None
    duracao_minutos: Optional[float] = None
    ativa: bool  # Derived property

    class Config:
        from_attributes = True
