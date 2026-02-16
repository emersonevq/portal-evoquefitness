from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class SlaRelatorioFiltros(BaseModel):
    data_inicio: date
    data_fim: date
    prioridade: Optional[str] = None
    status: Optional[str] = None
    unidade: Optional[str] = None

class SlaRelatorioItemChamado(BaseModel):
    codigo: str
    protocolo: str
    prioridade: str
    status: str
    data_abertura: datetime
    data_conclusao: Optional[datetime] = None
    tempo_resposta_horas: float
    limite_resposta_horas: float
    tempo_resolucao_horas: float
    limite_resolucao_horas: float
    cumpriu_resposta: bool
    cumpriu_resolucao: bool
    dias_em_pausa: float

class SlaRelatorioResponse(BaseModel):
    periodo: str
    data_geracao: datetime
    total_chamados: int
    chamados_dentro_sla: int
    chamados_fora_sla: int
    taxa_cumprimento: float  # percentual
    tempo_resposta_medio: float
    tempo_resolucao_medio: float
    itens: list[SlaRelatorioItemChamado]

    class Config:
        from_attributes = True
