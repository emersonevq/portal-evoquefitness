"""
Serviço de notificações de SLA.

Gerencia:
- Notificações de SLA em risco
- Notificações de SLA vencido
"""

from datetime import datetime
from sqlalchemy.orm import Session
from ti.models import Chamado

class NotificacaoService:
    def __init__(self, db: Session):
        self.db = db
    
    def notificar_em_risco(self, chamado: Chamado) -> bool:
        """
        Envia notificação de SLA em risco.
        
        TODO: Integrar com sistema de notificações real
        
        Returns:
            True se notificação foi enviada
        """
        print(f"[SLA NOTIFICACAO] Chamado {chamado.codigo} em risco. "
              f"Consumido: {chamado.sla_percentual_consumido:.1f}%")
        return True
    
    def notificar_vencido(self, chamado: Chamado) -> bool:
        """
        Envia notificação de SLA vencido.
        
        TODO: Integrar com sistema de notificações real
        
        Returns:
            True se notificação foi enviada
        """
        print(f"[SLA NOTIFICACAO] Chamado {chamado.codigo} com SLA VENCIDO. "
              f"Consumido: {chamado.sla_percentual_consumido:.1f}%")
        return True
    
    def notificar_concluido_dentro_sla(self, chamado: Chamado) -> bool:
        """Envia notificação de conclusão dentro do SLA"""
        print(f"[SLA NOTIFICACAO] Chamado {chamado.codigo} concluído DENTRO do SLA.")
        return True
    
    def notificar_concluido_fora_sla(self, chamado: Chamado) -> bool:
        """Envia notificação de conclusão fora do SLA"""
        print(f"[SLA NOTIFICACAO] Chamado {chamado.codigo} concluído FORA do SLA.")
        return True
