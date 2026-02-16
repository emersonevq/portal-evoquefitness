"""
Task periódica: Verificar SLA a cada 5 minutos.

MOMENTO 2 - MONITORAMENTO:
- Busca chamados ativos (Aberto, Em Atendimento)
- Atualiza tempo decorrido
- Marca em risco ou vencido
- Escalona automaticamente se necessário
"""

from sqlalchemy.orm import Session
from ti.models import Chamado
from ti.modules.sla.services import SlaTracker, EscalonamentoService, NotificacaoService
from ti.modules.sla.utils import STATUS_ABERTO, STATUS_EM_ATENDIMENTO

def verificar_sla_tarefa(db: Session) -> None:
    """
    Verifica SLA de todos os chamados ativos.
    
    Chamados ATIVOS são aqueles com status:
    - Aberto
    - Em atendimento
    
    Para cada um, calcula o percentual consumido e marca se está em risco/vencido.
    """
    tracker = SlaTracker(db)
    escalonamento = EscalonamentoService(db)
    notificacao = NotificacaoService(db)
    
    # Busca chamados ativos
    chamados_ativos = db.query(Chamado).filter(
        Chamado.status.in_([STATUS_ABERTO, STATUS_EM_ATENDIMENTO]),
        Chamado.deletado_em == None
    ).all()
    
    print(f"[TASK] Verificando {len(chamados_ativos)} chamados ativos...")
    
    for chamado in chamados_ativos:
        # Atualiza monitoramento
        tracker.atualizar_monitoramento(chamado)
        
        # Se vencido e não foi escalado, escalona
        if chamado.sla_vencido and not escalonamento.ja_foi_escalado(chamado):
            escalonamento.escalar(chamado, "SLA vencido na verificação periódica")
            notificacao.notificar_vencido(chamado)
            print(f"[TASK] Escalado: {chamado.codigo}")
        
        # Se em risco e não foi notificado
        elif chamado.sla_em_risco and not chamado.sla_ultimo_escalonamento:
            notificacao.notificar_em_risco(chamado)
            print(f"[TASK] Em risco: {chamado.codigo} ({chamado.sla_percentual_consumido:.1f}%)")
    
    print("[TASK] Verificação de SLA concluída")
