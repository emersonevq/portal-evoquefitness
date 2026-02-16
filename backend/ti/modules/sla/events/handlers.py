"""
Handlers de eventos para o módulo SLA.

Gerencia:
- Mudanças de status de chamado
- Inicialização de SLA
- Transições de estados
- Validação de data de corte (13-02-2026)
"""

import logging
from datetime import date, datetime
from sqlalchemy.orm import Session
from ti.models import Chamado
from ti.modules.sla.services import (
    SlaCalculator,
    SlaTracker,
    PausaService,
    EscalonamentoService,
    NotificacaoService,
)
from ti.modules.sla.utils import (
    STATUS_ABERTO,
    STATUS_EM_ATENDIMENTO,
    STATUS_AGUARDANDO,
    STATUS_CONCLUIDO,
    is_status_ativo,
)

logger = logging.getLogger("sla.events")

# Data de corte para SLA: 13 de fevereiro de 2026
SLA_CUTOFF_DATE = date(2026, 2, 13)

class SlaEventHandlers:
    """Handlers de eventos de SLA"""
    
    def __init__(self, db: Session):
        self.db = db
        self.calculator = SlaCalculator(db)
        self.tracker = SlaTracker(db)
        self.pausa = PausaService(db)
        self.escalonamento = EscalonamentoService(db)
        self.notificacao = NotificacaoService(db)
    
    def on_chamado_created(self, chamado: Chamado) -> None:
        """
        Handler para criação de chamado.

        MOMENTO 1 - EVENTO:
        - Valida data de corte (01-01-2026)
        - Marca como retroativo se anterior à data de corte
        - Inicia SLA se não for retroativo
        """
        # Valida data de corte
        if chamado.data_abertura:
            data_abertura = chamado.data_abertura
            # Se for datetime, extrai a data
            if isinstance(data_abertura, datetime):
                data_abertura = data_abertura.date()

            if data_abertura < SLA_CUTOFF_DATE:
                logger.info(
                    f"[SLA] Chamado {chamado.codigo} anterior à data de corte ({SLA_CUTOFF_DATE}). "
                    f"Data de abertura: {data_abertura}. Marcado como retroativo."
                )
                chamado.retroativo = True
                self.db.add(chamado)
                self.db.commit()
                return  # Ignora SLA para retroativos

        # Se já estava marcado como retroativo, ignora
        if chamado.retroativo:
            logger.debug(
                f"[SLA] Chamado {chamado.codigo} marcado como retroativo. "
                f"SLA não será calculado."
            )
            return  # Ignora chamados retroativos

        logger.info(f"[SLA] Iniciando SLA para chamado {chamado.codigo}")
        self.tracker.iniciar_sla(chamado)
    
    def on_status_changed(
        self,
        chamado: Chamado,
        status_anterior: str,
        status_novo: str
    ) -> None:
        """
        Handler para mudança de status.
        
        MOMENTO 1 - EVENTO: Qualquer mudança de status
        - Registra primeira resposta se necessário
        - Pausa/retoma SLA
        - Conclui SLA se final
        """
        if chamado.retroativo:
            return  # Ignora chamados retroativos
        
        chamado.status = status_novo
        
        # Transição: Aberto → Em Atendimento ou Aberto → Aguardando
        if status_anterior == STATUS_ABERTO and status_novo in [STATUS_EM_ATENDIMENTO, STATUS_AGUARDANDO]:
            # Registra primeira resposta
            self.tracker.registrar_primeira_resposta(chamado)
            
            # Se foi para Aguardando, inicia pausa
            if status_novo == STATUS_AGUARDANDO:
                self.pausa.iniciar_pausa(
                    chamado_id=chamado.id,
                    motivo="Mudança de status"
                )
        
        # Transição: Em Atendimento → Aguardando
        elif status_anterior == STATUS_EM_ATENDIMENTO and status_novo == STATUS_AGUARDANDO:
            # Inicia pausa
            self.pausa.iniciar_pausa(
                chamado_id=chamado.id,
                motivo="Mudança de status"
            )
        
        # Transição: Aguardando → Em Atendimento
        elif status_anterior == STATUS_AGUARDANDO and status_novo == STATUS_EM_ATENDIMENTO:
            # Retoma pausa aberta
            self.pausa.retomar_pausa_aberta(chamado_id=chamado.id)
        
        # Transição: Aguardando → Concluído (sem passar por Em Atendimento)
        elif status_anterior == STATUS_AGUARDANDO and status_novo == STATUS_CONCLUIDO:
            # Fecha pausa aberta
            self.pausa.retomar_pausa_aberta(chamado_id=chamado.id)
            # Conclui SLA
            resultado = self.tracker.concluir_sla(chamado)
            # Notifica
            if resultado.get("cumpriu_sla"):
                self.notificacao.notificar_concluido_dentro_sla(chamado)
            else:
                self.notificacao.notificar_concluido_fora_sla(chamado)
        
        # Transição: Em Atendimento → Concluído
        elif status_anterior == STATUS_EM_ATENDIMENTO and status_novo == STATUS_CONCLUIDO:
            # Conclui SLA
            resultado = self.tracker.concluir_sla(chamado)
            # Notifica
            if resultado.get("cumpriu_sla"):
                self.notificacao.notificar_concluido_dentro_sla(chamado)
            else:
                self.notificacao.notificar_concluido_fora_sla(chamado)
        
        # Transição: Aberto → Concluído (direto)
        elif status_anterior == STATUS_ABERTO and status_novo == STATUS_CONCLUIDO:
            # Registra primeira resposta e conclui SLA
            self.tracker.registrar_primeira_resposta(chamado)
            resultado = self.tracker.concluir_sla(chamado)
            # Notifica
            if resultado.get("cumpriu_sla"):
                self.notificacao.notificar_concluido_dentro_sla(chamado)
            else:
                self.notificacao.notificar_concluido_fora_sla(chamado)
        
        self.db.commit()
