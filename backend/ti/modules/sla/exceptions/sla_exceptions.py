"""
Exceções customizadas do módulo SLA.
"""

class SlaException(Exception):
    """Exceção base do módulo SLA"""
    pass

class ConfiguracaoSlaNotFound(SlaException):
    """Configuração de SLA não encontrada"""
    pass

class ChamadoNotFound(SlaException):
    """Chamado não encontrado"""
    pass

class PausaNotFound(SlaException):
    """Pausa não encontrada"""
    pass

class HorarioComercialNotFound(SlaException):
    """Horário comercial não encontrado"""
    pass

class InvalidStatusTransition(SlaException):
    """Transição de status inválida"""
    pass

class SlaAlreadyFinalized(SlaException):
    """SLA já foi finalizado e não pode ser modificado"""
    pass
