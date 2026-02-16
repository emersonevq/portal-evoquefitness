"""
Serviço de notificações de SLA.

Gerencia:
- Notificações de SLA em risco
- Notificações de SLA vencido
- Integração com email (Microsoft Graph)
- Integração com WebSocket (Socket.IO)
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from ti.models import Chamado

logger = logging.getLogger("sla.notifications")


class NotificacaoService:
    def __init__(self, db: Session):
        self.db = db

    def _criar_notificacao_no_banco(
        self,
        chamado: Chamado,
        titulo: str,
        mensagem: str,
        tipo: str
    ) -> None:
        """Cria registro de notificação no banco de dados"""
        try:
            from ti.models import Notification

            notification = Notification(
                tipo="sla",
                titulo=titulo,
                mensagem=mensagem,
                recurso="chamado",
                recurso_id=chamado.id,
                acao=tipo,
                criado_em=datetime.utcnow()
            )
            self.db.add(notification)
            self.db.commit()
        except Exception as e:
            logger.error(f"[SLA] Erro ao criar notificação no banco: {e}")

    def _enviar_email(
        self,
        para: str,
        assunto: str,
        titulo: str,
        corpo: str
    ) -> bool:
        """Envia email via Microsoft Graph"""
        try:
            from core.email_msgraph import _have_graph_config, send_notification_email

            if not _have_graph_config():
                logger.warning("[SLA] Configuração de email não disponível")
                return False

            # Envia email
            send_notification_email(
                destinatario=para,
                assunto=assunto,
                corpo=corpo
            )
            logger.info(f"[SLA] Email enviado para {para}: {assunto}")
            return True

        except Exception as e:
            logger.error(f"[SLA] Erro ao enviar email: {e}")
            return False

    def _emitir_websocket(self, evento: str, dados: dict) -> bool:
        """Emite evento via WebSocket (Socket.IO)"""
        try:
            from core.realtime import sio

            # Emitir para todos os clientes conectados
            sio.emit(
                f"sla:{evento}",
                dados,
                namespace="/"
            )
            logger.debug(f"[SLA] Evento WebSocket emitido: {evento}")
            return True

        except Exception as e:
            logger.warning(f"[SLA] WebSocket não disponível ou erro: {e}")
            return False

    def notificar_em_risco(self, chamado: Chamado) -> bool:
        """
        Envia notificação de SLA em risco.

        Integra:
        - Email ao responsável/atribuído
        - WebSocket em tempo real
        - Registro no banco de dados

        Returns:
            True se pelo menos uma forma de notificação foi enviada
        """
        try:
            titulo = f"⚠️ Chamado {chamado.codigo} em risco de SLA"
            mensagem = (
                f"O chamado está consumindo {chamado.sla_percentual_consumido:.1f}% do SLA.\n"
                f"Prioridade: {chamado.prioridade}\n"
                f"Ação necessária: revisar e acelerar resolução"
            )

            logger.warning(f"[SLA] {titulo}")

            # Criar notificação no banco
            self._criar_notificacao_no_banco(
                chamado,
                titulo,
                mensagem,
                "em_risco"
            )

            # Emitir via WebSocket
            self._emitir_websocket("em_risco", {
                "chamado_id": chamado.id,
                "codigo": chamado.codigo,
                "percentual": chamado.sla_percentual_consumido,
                "prioridade": chamado.prioridade,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Enviar email se tiver responsável
            if chamado.email:
                self._enviar_email(
                    para=chamado.email,
                    assunto=f"⚠️ SLA em Risco: {chamado.codigo}",
                    titulo=titulo,
                    corpo=mensagem
                )

            return True

        except Exception as e:
            logger.error(f"[SLA] Erro ao notificar em risco: {e}", exc_info=True)
            return False

    def notificar_vencido(self, chamado: Chamado) -> bool:
        """
        Envia notificação de SLA vencido.

        Integra:
        - Email ao responsável/atribuído
        - Email ao gerente
        - WebSocket em tempo real
        - Registro no banco de dados

        Returns:
            True se notificação foi enviada
        """
        try:
            titulo = f"❌ CRÍTICO: Chamado {chamado.codigo} com SLA VENCIDO"
            mensagem = (
                f"O chamado excedeu o limite de SLA.\n"
                f"Consumido: {chamado.sla_percentual_consumido:.1f}%\n"
                f"Prioridade: {chamado.prioridade}\n"
                f"AÇÃO IMEDIATA NECESSÁRIA"
            )

            logger.error(f"[SLA] {titulo}")

            # Criar notificação no banco
            self._criar_notificacao_no_banco(
                chamado,
                titulo,
                mensagem,
                "vencido"
            )

            # Emitir via WebSocket com prioridade alta
            self._emitir_websocket("vencido", {
                "chamado_id": chamado.id,
                "codigo": chamado.codigo,
                "percentual": chamado.sla_percentual_consumido,
                "prioridade": chamado.prioridade,
                "urgencia": "crítica",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Enviar email ao responsável
            if chamado.email:
                self._enviar_email(
                    para=chamado.email,
                    assunto=f"❌ CRÍTICO - SLA Vencido: {chamado.codigo}",
                    titulo=titulo,
                    corpo=mensagem
                )

            # TODO: Enviar para gerente também
            # if chamado.gerente_email:
            #     self._enviar_email(...)

            return True

        except Exception as e:
            logger.error(f"[SLA] Erro ao notificar vencido: {e}", exc_info=True)
            return False

    def notificar_concluido_dentro_sla(self, chamado: Chamado) -> bool:
        """Envia notificação de conclusão dentro do SLA"""
        try:
            titulo = f"✓ Chamado {chamado.codigo} concluído DENTRO do SLA"
            mensagem = (
                f"Tempo de resolução: {chamado.sla_tempo_decorrido_horas:.1f}h\n"
                f"Limite: 24h\n"
                f"Status: Cumprimento de SLA ✓"
            )

            logger.info(f"[SLA] {titulo}")

            self._criar_notificacao_no_banco(
                chamado,
                titulo,
                mensagem,
                "concluido_dentro"
            )

            self._emitir_websocket("concluido", {
                "chamado_id": chamado.id,
                "codigo": chamado.codigo,
                "status": "dentro",
                "tempo": chamado.sla_tempo_decorrido_horas,
                "timestamp": datetime.utcnow().isoformat()
            })

            return True

        except Exception as e:
            logger.error(f"[SLA] Erro ao notificar conclusão dentro: {e}")
            return False

    def notificar_concluido_fora_sla(self, chamado: Chamado) -> bool:
        """Envia notificação de conclusão fora do SLA"""
        try:
            titulo = f"⚠️ Chamado {chamado.codigo} concluído FORA do SLA"
            mensagem = (
                f"Tempo de resolução: {chamado.sla_tempo_decorrido_horas:.1f}h\n"
                f"Limite: 24h\n"
                f"Status: NÃO cumpriu SLA ✗\n"
                f"Excedimento: {chamado.sla_tempo_decorrido_horas - 24:.1f}h"
            )

            logger.warning(f"[SLA] {titulo}")

            self._criar_notificacao_no_banco(
                chamado,
                titulo,
                mensagem,
                "concluido_fora"
            )

            self._emitir_websocket("concluido", {
                "chamado_id": chamado.id,
                "codigo": chamado.codigo,
                "status": "fora",
                "tempo": chamado.sla_tempo_decorrido_horas,
                "timestamp": datetime.utcnow().isoformat()
            })

            if chamado.email:
                self._enviar_email(
                    para=chamado.email,
                    assunto=f"⚠️ Chamado concluído fora do SLA: {chamado.codigo}",
                    titulo=titulo,
                    corpo=mensagem
                )

            return True

        except Exception as e:
            logger.error(f"[SLA] Erro ao notificar conclusão fora: {e}")
            return False
