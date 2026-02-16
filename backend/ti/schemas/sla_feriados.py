from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class FeriadoCreate(BaseModel):
    nome: str
    data: date
    tipo: str = "fixo"  # 'fixo', 'movel', 'pontual'
    recorrente: bool = False
    ativo: bool = True
    descricao: Optional[str] = None

class FeriadoUpdate(BaseModel):
    nome: Optional[str] = None
    data: Optional[date] = None
    tipo: Optional[str] = None
    recorrente: Optional[bool] = None
    ativo: Optional[bool] = None
    descricao: Optional[str] = None

class FeriadoResponse(BaseModel):
    id: int
    nome: str
    data: date
    tipo: str
    recorrente: bool
    ativo: bool
    descricao: Optional[str] = None
    data_criacao: datetime
    usuario_criacao: Optional[int] = None

    class Config:
        from_attributes = True
