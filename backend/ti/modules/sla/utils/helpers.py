"""
Funções auxiliares do módulo SLA.
"""

from datetime import datetime, time
from .constants import STATUS_ABERTO, STATUS_EM_ATENDIMENTO, STATUSES_PAUSADOS

def is_status_ativo(status: str) -> bool:
    """Verifica se status está ativo para SLA"""
    return status in [STATUS_ABERTO, STATUS_EM_ATENDIMENTO]

def is_status_pausado(status: str) -> bool:
    """Verifica se status pausa o SLA"""
    return status in STATUSES_PAUSADOS

def formatar_horas(horas: float) -> str:
    """Formata horas para string legível"""
    if horas < 0:
        horas = 0
    
    dias = int(horas // 24)
    horas_rest = int(horas % 24)
    minutos = int((horas % 1) * 60)
    
    partes = []
    if dias > 0:
        partes.append(f"{dias}d")
    if horas_rest > 0:
        partes.append(f"{horas_rest}h")
    if minutos > 0 and dias == 0:
        partes.append(f"{minutos}m")
    
    return " ".join(partes) or "0m"

def calcular_percentual_consumido(tempo_decorrido: float, limite: float) -> float:
    """Calcula percentual de consumo do SLA"""
    if limite <= 0:
        return 0.0
    
    percentual = (tempo_decorrido / limite) * 100
    return min(percentual, 100.0)  # Máximo 100%

def eh_dentro_sla(tempo_decorrido: float, limite: float) -> bool:
    """Verifica se o tempo está dentro do SLA"""
    return tempo_decorrido <= limite

def eh_em_risco(percentual_consumido: float, percentual_risco: float = 75.0) -> bool:
    """Verifica se o SLA está em risco"""
    return percentual_consumido >= percentual_risco

def eh_vencido(percentual_consumido: float) -> bool:
    """Verifica se o SLA foi vencido"""
    return percentual_consumido >= 100.0
