from .constants import *
from .helpers import *

__all__ = [
    # Constants
    "STATUS_ABERTO",
    "STATUS_EM_ATENDIMENTO", 
    "STATUS_AGUARDANDO",
    "STATUS_CONCLUIDO",
    "STATUS_CANCELADO",
    "STATUSES_ATIVOS",
    "STATUSES_PAUSADOS",
    "STATUSES_FINAIS",
    "PRIORIDADE_CRITICA",
    "PRIORIDADE_ALTA",
    "PRIORIDADE_NORMAL",
    "PRIORIDADE_BAIXA",
    "PRIORIDADES",
    "ACAO_INICIAR",
    "ACAO_PRIMEIRA_RESPOSTA",
    "ACAO_PAUSA",
    "ACAO_RETOMA",
    "ACAO_CONCLUIDO",
    "ACAO_ESCALONAMENTO",
    "STATUS_SLA_DENTRO",
    "STATUS_SLA_FORA",
    # Helpers
    "is_status_ativo",
    "is_status_pausado",
    "formatar_horas",
    "calcular_percentual_consumido",
    "eh_dentro_sla",
    "eh_em_risco",
    "eh_vencido",
]
