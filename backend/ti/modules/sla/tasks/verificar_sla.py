"""
Task periódica: Verificar SLA a cada 5 minutos.

MOMENTO 2 - MONITORAMENTO:
- Busca chamados ativos (Aberto, Em Atendimento)
- Atualiza tempo decorrido
- Marca em risco ou vencido
- Escalona automaticamente se necessário
- Tratamento robusto de erros com logging
"""

import logging
from sqlalchemy.orm import Session
from ti.models import Chamado
from ti.modules.sla.services import SlaTracker, EscalonamentoService, NotificacaoService
from ti.modules.sla.utils import STATUS_ABERTO, STATUS_EM_ATENDIMENTO

logger = logging.getLogger("sla.tasks")

def verificar_sla_tarefa(db: Session) -> None:
    """
    Verifica SLA de todos os chamados ativos.

    Chamados ATIVOS são aqueles com status:
    - Aberto
    - Em atendimento

    Para cada um, calcula o percentual consumido e marca se está em risco/vencido.

    Erros por chamado são capturados para não interromper o processamento de outros.
    """
    tracker = SlaTracker(db)
    escalonamento = EscalonamentoService(db)
    notificacao = NotificacaoService(db)

    try:
        # Busca chamados ativos
        chamados_ativos = db.query(Chamado).filter(
            Chamado.status.in_([STATUS_ABERTO, STATUS_EM_ATENDIMENTO]),
            Chamado.deletado_em == None
        ).all()

        logger.info(f"[TASK verificar_sla] Verificando {len(chamados_ativos)} chamados ativos")

        processados = 0
        erros = 0
        escalados = 0
        em_risco = 0

        for chamado in chamados_ativos:
            try:
                # Atualiza monitoramento
                tracker.atualizar_monitoramento(chamado)
                processados += 1

                # Se vencido e não foi escalado, escalona
                if chamado.sla_vencido and not escalonamento.ja_foi_escalado(chamado):
                    try:
                        escalonamento.escalar(chamado, "SLA vencido na verificação periódica")
                        notificacao.notificar_vencido(chamado)
                        escalados += 1
                        logger.warning(
                            f"[TASK verificar_sla] Chamado {chamado.codigo} escalado - SLA vencido ({chamado.sla_percentual_consumido:.1f}%)"
                        )
                    except Exception as e:
                        logger.error(
                            f"[TASK verificar_sla] Erro ao escalar chamado {chamado.codigo}: {e}",
                            exc_info=True
                        )
                        erros += 1

                # Se em risco e não foi notificado
                elif chamado.sla_em_risco and not chamado.sla_ultimo_escalonamento:
                    try:
                        notificacao.notificar_em_risco(chamado)
                        em_risco += 1
                        logger.warning(
                            f"[TASK verificar_sla] Chamado {chamado.codigo} em risco ({chamado.sla_percentual_consumido:.1f}%)"
                        )
                    except Exception as e:
                        logger.error(
                            f"[TASK verificar_sla] Erro ao notificar risco para {chamado.codigo}: {e}",
                            exc_info=True
                        )
                        erros += 1

            except Exception as e:
                logger.error(
                    f"[TASK verificar_sla] Erro ao processar chamado {chamado.codigo if hasattr(chamado, 'codigo') else chamado.id}: {e}",
                    exc_info=True
                )
                erros += 1
                continue

        logger.info(
            f"[TASK verificar_sla] Concluído: {processados} processados, "
            f"{escalados} escalados, {em_risco} em risco, {erros} erros"
        )

    except Exception as e:
        logger.error(
            f"[TASK verificar_sla] Erro fatal na verificação de SLA: {e}",
            exc_info=True
        )
