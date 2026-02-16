"""
Task periódica: Verificar feriados diariamente às 00:01.

- Verifica se hoje é feriado
- Se for, pausa todos os chamados ativos
- No dia útil seguinte, retoma automaticamente
"""

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from ti.models import Chamado, Feriado
from ti.modules.sla.services import PausaService
from ti.modules.sla.utils import STATUS_ABERTO, STATUS_EM_ATENDIMENTO

def verificar_feriados_tarefa(db: Session) -> None:
    """
    Verifica feriados e pausa SLA automaticamente.
    
    Se hoje for feriado:
    - Pausa todos os chamados ativos
    - Registra no histórico
    
    Se hoje for primeiro dia útil após feriado:
    - Retoma pausas que foram abertas para feriado
    """
    pausa_service = PausaService(db)
    
    hoje = date.today()
    
    # Verifica se hoje é feriado
    eh_feriado = db.query(Feriado).filter(
        Feriado.data == hoje,
        Feriado.ativo == True
    ).first() is not None
    
    if eh_feriado:
        print(f"[TASK] Hoje ({hoje}) é feriado. Pausando chamados ativos...")
        
        # Busca todos os chamados ativos
        chamados_ativos = db.query(Chamado).filter(
            Chamado.status.in_([STATUS_ABERTO, STATUS_EM_ATENDIMENTO]),
            Chamado.deletado_em == None
        ).all()
        
        # Pausa cada um
        for chamado in chamados_ativos:
            pausa_service.iniciar_pausa(
                chamado_id=chamado.id,
                motivo=f"Feriado: {hoje}"
            )
        
        print(f"[TASK] {len(chamados_ativos)} chamados pausados")
    else:
        # Verifica se ontem era feriado (para retomar)
        ontem = hoje - timedelta(days=1)
        eh_feriado_ontem = db.query(Feriado).filter(
            Feriado.data == ontem,
            Feriado.ativo == True
        ).first() is not None
        
        if eh_feriado_ontem:
            print(f"[TASK] Ontem ({ontem}) era feriado. Retomando chamados...")
            
            # Busca chamados com pausas abertas para feriado
            chamados_com_pausa = db.query(Chamado).filter(
                Chamado.deletado_em == None
            ).all()
            
            retomados = 0
            for chamado in chamados_com_pausa:
                pausa = pausa_service.retomar_pausa_aberta(chamado.id)
                if pausa:
                    retomados += 1
            
            print(f"[TASK] {retomados} chamados retomados")
        else:
            print(f"[TASK] Nenhuma ação de feriado necessária para {hoje}")
