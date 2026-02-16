"""
Serviço de escalonamento automático de SLA.

Gerencia:
- Escalar chamados com SLA vencido
- Rastrear escalonamentos
"""

from datetime import datetime
from sqlalchemy.orm import Session
from ti.models import Chamado, HistoricoSla

class EscalonamentoService:
    def __init__(self, db: Session):
        self.db = db
    
    def escalar(self, chamado: Chamado, motivo: str = "SLA vencido") -> None:
        """
        Escalona um chamado (marca como vencido e registra escalonamento).
        
        Args:
            chamado: Objeto do chamado
            motivo: Motivo do escalonamento
        """
        agora = datetime.utcnow()
        
        chamado.sla_vencido = True
        chamado.sla_ultimo_escalonamento = agora
        
        # Registra no histórico
        historico = HistoricoSla(
            chamado_id=chamado.id,
            acao="escalonamento",
            observacoes=f"Chamado escalado. {motivo}"
        )
        self.db.add(historico)
        self.db.commit()
    
    def ja_foi_escalado(self, chamado: Chamado) -> bool:
        """Verifica se o chamado já foi escalado"""
        return chamado.sla_ultimo_escalonamento is not None
