"""Constantes e funções auxiliares para normalização de status"""

from typing import Set

# Status que CONTAM no SLA (relógio rodando)
STATUS_SLA_ATIVO: Set[str] = {
    "aberto",
    "em_andamento",
}

# Status que PAUSAM o SLA (aguardando terceiros)
STATUS_SLA_PAUSADO: Set[str] = {
    "em_analise",
}

# Status FINALIZADOS (SLA encerrado)
STATUS_FINALIZADOS: Set[str] = {
    "concluido",
    "cancelado",
}

# Mapeamento para normalização
_STATUS_MAP = {
    # Aberto
    "aberto": "aberto",
    "Aberto": "aberto",
    "ABERTO": "aberto",
    
    # Em andamento
    "em andamento": "em_andamento",
    "Em andamento": "em_andamento",
    "EM ANDAMENTO": "em_andamento",
    "em_andamento": "em_andamento",
    "Em Andamento": "em_andamento",
    
    # Em análise
    "em análise": "em_analise",
    "Em análise": "em_analise",
    "EM ANÁLISE": "em_analise",
    "em_analise": "em_analise",
    "Em Análise": "em_analise",
    "em analise": "em_analise",
    
    # Concluído
    "concluído": "concluido",
    "Concluído": "concluido",
    "CONCLUÍDO": "concluido",
    "concluido": "concluido",
    "Concluido": "concluido",
    
    # Cancelado
    "cancelado": "cancelado",
    "Cancelado": "cancelado",
    "CANCELADO": "cancelado",
}


def normalizar_status(status: str) -> str:
    """
    Normaliza o status para comparação consistente.
    
    Exemplos:
        "Em andamento" -> "em_andamento"
        "EM ANÁLISE" -> "em_analise"
    """
    if not status:
        return ""
    
    status = status.strip()
    
    # Tenta mapeamento direto
    if status in _STATUS_MAP:
        return _STATUS_MAP[status]
    
    # Fallback: lowercase + underscore + remove acentos
    resultado = status.lower().replace(" ", "_")
    resultado = resultado.replace("á", "a").replace("í", "i").replace("ó", "o")
    resultado = resultado.replace("ã", "a").replace("õ", "o")
    resultado = resultado.replace("é", "e").replace("ê", "e")
    resultado = resultado.replace("ú", "u").replace("ç", "c")
    
    return resultado


def is_status_sla_ativo(status: str) -> bool:
    """Verifica se o status conta no SLA (relógio rodando)"""
    return normalizar_status(status) in STATUS_SLA_ATIVO


def is_status_pausado(status: str) -> bool:
    """Verifica se o status pausa o SLA"""
    return normalizar_status(status) in STATUS_SLA_PAUSADO


def is_status_finalizado(status: str) -> bool:
    """Verifica se o status é finalizado"""
    return normalizar_status(status) in STATUS_FINALIZADOS
