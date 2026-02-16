from pydantic import BaseModel, Field
from datetime import datetime, time
from typing import Optional

class HorarioComercialCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    hora_inicio: time
    hora_fim: time
    segunda: bool = True
    terca: bool = True
    quarta: bool = True
    quinta: bool = True
    sexta: bool = True
    sabado: bool = False
    domingo: bool = False
    considera_almoco: bool = False
    almoco_inicio: Optional[time] = None
    almoco_fim: Optional[time] = None
    emergencia_ativo: bool = False
    emergencia_inicio: Optional[time] = None
    emergencia_fim: Optional[time] = None
    emergencia_dias_semana: Optional[str] = None
    timezone: str = "America/Sao_Paulo"
    considera_feriados: bool = True
    ativo: bool = True
    padrao: bool = False

class HorarioComercialUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None
    segunda: Optional[bool] = None
    terca: Optional[bool] = None
    quarta: Optional[bool] = None
    quinta: Optional[bool] = None
    sexta: Optional[bool] = None
    sabado: Optional[bool] = None
    domingo: Optional[bool] = None
    considera_almoco: Optional[bool] = None
    almoco_inicio: Optional[time] = None
    almoco_fim: Optional[time] = None
    emergencia_ativo: Optional[bool] = None
    emergencia_inicio: Optional[time] = None
    emergencia_fim: Optional[time] = None
    emergencia_dias_semana: Optional[str] = None
    timezone: Optional[str] = None
    considera_feriados: Optional[bool] = None
    ativo: Optional[bool] = None
    padrao: Optional[bool] = None

class HorarioComercialResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    hora_inicio: time
    hora_fim: time
    segunda: bool
    terca: bool
    quarta: bool
    quinta: bool
    sexta: bool
    sabado: bool
    domingo: bool
    considera_almoco: bool
    almoco_inicio: Optional[time] = None
    almoco_fim: Optional[time] = None
    emergencia_ativo: bool
    emergencia_inicio: Optional[time] = None
    emergencia_fim: Optional[time] = None
    emergencia_dias_semana: Optional[str] = None
    timezone: str
    considera_feriados: bool
    ativo: bool
    padrao: bool
    data_criacao: datetime
    data_atualizacao: datetime
    usuario_criacao: Optional[int] = None
    usuario_atualizacao: Optional[int] = None

    class Config:
        from_attributes = True
