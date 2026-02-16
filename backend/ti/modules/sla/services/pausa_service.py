"""
Serviço de pausas de SLA.

Gerencia:
- Pausar SLA (quando status = Aguardando)
- Retomar SLA (quando status = Em atendimento novamente)
- Calcular duração da pausa
"""

from datetime import datetime
from sqlalchemy.orm import Session
from ti.models import Chamado, SlaPausa, HistoricoSla

class PausaService:
    def __init__(self, db: Session):
        self.db = db
    
    def iniciar_pausa(self, chamado_id: int, motivo: str = None, usuario_id: int = None) -> SlaPausa:
        """
        Inicia uma pausa no SLA (transição para Aguardando).
        
        Args:
            chamado_id: ID do chamado
            motivo: Motivo da pausa
            usuario_id: ID do usuário que pausou
        
        Returns:
            Registro de pausa criado
        """
        pausa = SlaPausa(
            chamado_id=chamado_id,
            pausado_em=datetime.utcnow(),
            motivo=motivo,
            criado_por_id=usuario_id
        )
        self.db.add(pausa)
        self.db.commit()
        self.db.refresh(pausa)
        
        # Registra no histórico
        historico = HistoricoSla(
            chamado_id=chamado_id,
            acao="pausa",
            observacoes=f"SLA pausado. Motivo: {motivo or 'Não informado'}"
        )
        self.db.add(historico)
        self.db.commit()
        
        return pausa
    
    def retomar_pausa(self, pausa_id: int) -> SlaPausa:
        """
        Retoma uma pausa (transição de Aguardando para Em atendimento).
        
        Args:
            pausa_id: ID da pausa
        
        Returns:
            Registro de pausa atualizado
        """
        pausa = self.db.query(SlaPausa).filter(SlaPausa.id == pausa_id).first()
        if not pausa:
            raise ValueError(f"Pausa {pausa_id} não encontrada")
        
        agora = datetime.utcnow()
        pausa.retomado_em = agora
        
        # Calcula duração em minutos
        duracao = (agora - pausa.pausado_em).total_seconds() / 60
        pausa.duracao_minutos = duracao
        
        self.db.commit()
        self.db.refresh(pausa)
        
        # Registra no histórico
        historico = HistoricoSla(
            chamado_id=pausa.chamado_id,
            acao="retoma",
            observacoes=f"SLA retomado. Duração da pausa: {duracao:.2f} minutos"
        )
        self.db.add(historico)
        self.db.commit()
        
        return pausa
    
    def retomar_pausa_aberta(self, chamado_id: int) -> SlaPausa | None:
        """
        Retoma a pausa aberta (não finalizada) de um chamado, se houver.
        
        Args:
            chamado_id: ID do chamado
        
        Returns:
            Pausa retomada ou None se não houver pausa aberta
        """
        pausa = self.db.query(SlaPausa).filter(
            SlaPausa.chamado_id == chamado_id,
            SlaPausa.retomado_em == None
        ).first()
        
        if pausa:
            return self.retomar_pausa(pausa.id)
        
        return None
    
    def obter_pausas_ativas(self, chamado_id: int) -> list[SlaPausa]:
        """Obtém as pausas ativas (não finalizadas) de um chamado"""
        return self.db.query(SlaPausa).filter(
            SlaPausa.chamado_id == chamado_id,
            SlaPausa.retomado_em == None
        ).all()
    
    def obter_tempo_pausa_total(self, chamado_id: int) -> float:
        """
        Obtém o tempo total em pausa de um chamado em minutos.
        
        Inclui apenas pausas finalizadas (com retomado_em preenchido).
        """
        pausas = self.db.query(SlaPausa).filter(
            SlaPausa.chamado_id == chamado_id,
            SlaPausa.retomado_em != None,
            SlaPausa.duracao_minutos != None
        ).all()
        
        return sum(p.duracao_minutos or 0 for p in pausas)
