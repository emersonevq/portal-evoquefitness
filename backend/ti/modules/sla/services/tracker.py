"""
Rastreador de SLA - Gerencia o ciclo de vida do SLA do chamado.

Coordena:
- Inicialização do SLA (abertura do chamado)
- Registro de primeira resposta
- Conclusão do SLA
- Histórico de mudanças
"""

from datetime import datetime
from sqlalchemy.orm import Session
from ti.models import Chamado, ConfiguracesSla, HistoricoSla
from .calculator import SlaCalculator

class SlaTracker:
    def __init__(self, db: Session):
        self.db = db
        self.calculator = SlaCalculator(db)
    
    def obter_config_por_prioridade(self, prioridade: str) -> ConfiguracesSla | None:
        """Obtém a configuração de SLA pela prioridade"""
        return self.db.query(ConfiguracesSla).filter(
            ConfiguracesSla.prioridade == prioridade,
            ConfiguracesSla.ativo == True
        ).first()
    
    def iniciar_sla(self, chamado: Chamado) -> None:
        """
        Inicia o SLA de um chamado.
        
        MOMENTO 1 - EVENTO: Chamado criado
        - Define limites de primeira resposta e resolução
        - Salva no histórico
        """
        # Busca configuração pela prioridade
        config = self.obter_config_por_prioridade(chamado.prioridade)
        if not config:
            return  # Sem configuração, não há SLA
        
        # Define a data de abertura se não estiver preenchida
        if not chamado.data_abertura:
            chamado.data_abertura = datetime.utcnow()
        
        # Registra no histórico
        historico = HistoricoSla(
            chamado_id=chamado.id,
            acao="iniciar_sla",
            observacoes=f"SLA iniciado. Limite resposta: {config.tempo_primeira_resposta}h, Limite resolução: {config.tempo_resolucao}h"
        )
        self.db.add(historico)
        self.db.commit()
    
    def registrar_primeira_resposta(self, chamado: Chamado) -> float:
        """
        Registra a primeira resposta (transição de Aberto para Em Atendimento/Aguardando).
        
        MOMENTO 1 - EVENTO: Primeira resposta
        - Calcula tempo desde abertura até agora
        - Salva data_primeira_resposta
        - Registra no histórico
        
        Returns:
            Tempo decorrido em horas
        """
        config = self.obter_config_por_prioridade(chamado.prioridade)
        if not config:
            return 0.0
        
        # Se já foi registrada, não recalcula
        if chamado.data_primeira_resposta:
            return 0.0
        
        agora = datetime.utcnow()
        tempo_decorrido = self.calculator.calcular_tempo_com_pausas(
            chamado.data_abertura,
            agora,
            chamado.id,
            considera_horario_comercial=config.considera_horario_comercial,
            considera_feriados=config.considera_feriados
        )
        
        # Define data de primeira resposta
        chamado.data_primeira_resposta = agora
        
        # Determina se cumpriu SLA
        cumpriu = tempo_decorrido <= config.tempo_primeira_resposta
        
        # Registra no histórico
        historico = HistoricoSla(
            chamado_id=chamado.id,
            acao="primeira_resposta",
            tempo_resposta_horas=tempo_decorrido,
            limite_sla_resposta_horas=config.tempo_primeira_resposta,
            status_sla="dentro" if cumpriu else "fora",
            observacoes=f"Tempo resposta: {tempo_decorrido:.2f}h / {config.tempo_primeira_resposta}h"
        )
        self.db.add(historico)
        self.db.commit()
        
        return tempo_decorrido
    
    def concluir_sla(self, chamado: Chamado) -> dict:
        """
        Conclui o SLA (transição para Concluído).
        
        MOMENTO 1 - EVENTO: Conclusão
        - Calcula tempo total de resolução
        - Desconta pausas
        - Calcula percentual consumido
        - Determina status SLA (dentro/fora)
        - Registra no histórico (NUNCA MAIS SERÁ RECALCULADO)
        
        Returns:
            Dicionário com dados finais do SLA
        """
        config = self.obter_config_por_prioridade(chamado.prioridade)
        if not config:
            return {}
        
        agora = datetime.utcnow()
        
        # Calcula tempo de primeira resposta se ainda não foi calculado
        if not chamado.data_primeira_resposta:
            self.registrar_primeira_resposta(chamado)
        
        # Calcula tempo total de resolução
        tempo_resolucao = self.calculator.calcular_tempo_com_pausas(
            chamado.data_abertura,
            agora,
            chamado.id,
            considera_horario_comercial=config.considera_horario_comercial,
            considera_feriados=config.considera_feriados
        )
        
        # Calcula tempo de pausa
        tempo_pausa = self.calculator.calcular_horas_pausas(chamado.id)
        
        # Percentual consumido
        percentual_consumido = (tempo_resolucao / config.tempo_resolucao * 100) if config.tempo_resolucao > 0 else 0
        
        # Determina status
        cumpriu = tempo_resolucao <= config.tempo_resolucao
        
        # Atualiza chamado
        chamado.data_conclusao = agora
        chamado.sla_tempo_decorrido_horas = tempo_resolucao
        chamado.sla_tempo_pausado_horas = tempo_pausa
        chamado.sla_percentual_consumido = percentual_consumido
        chamado.sla_atualizado_em = agora
        
        # Registra no histórico (CONGELADO - nunca mais muda)
        historico = HistoricoSla(
            chamado_id=chamado.id,
            acao="concluido",
            tempo_resolucao_horas=tempo_resolucao,
            limite_sla_horas=config.tempo_resolucao,
            status_sla="dentro" if cumpriu else "fora",
            observacoes=f"Tempo resolução: {tempo_resolucao:.2f}h / {config.tempo_resolucao}h. Pausa: {tempo_pausa:.2f}h"
        )
        self.db.add(historico)
        self.db.commit()
        
        return {
            "tempo_resolucao": tempo_resolucao,
            "tempo_pausa": tempo_pausa,
            "percentual_consumido": percentual_consumido,
            "cumpriu_sla": cumpriu,
            "status_sla": "dentro" if cumpriu else "fora"
        }
    
    def atualizar_monitoramento(self, chamado: Chamado) -> None:
        """
        Atualiza campos de monitoramento de SLA (executado pela task periódica).
        
        MOMENTO 2 - MONITORAMENTO: Task a cada 5 minutos
        - Calcula tempo decorrido até agora
        - Atualiza percentual consumido
        - Marca em risco ou vencido
        
        Apenas para chamados ATIVOS (Aberto, Em Atendimento)
        """
        if chamado.status not in ["Aberto", "Em atendimento"]:
            return
        
        config = self.obter_config_por_prioridade(chamado.prioridade)
        if not config:
            return
        
        agora = datetime.utcnow()
        
        # Calcula tempo decorrido
        tempo_decorrido = self.calculator.calcular_tempo_com_pausas(
            chamado.data_abertura,
            agora,
            chamado.id,
            considera_horario_comercial=config.considera_horario_comercial,
            considera_feriados=config.considera_feriados
        )
        
        # Tempo de pausa
        tempo_pausa = self.calculator.calcular_horas_pausas(chamado.id)
        
        # Calcula qual limite usar (resposta ou resolução)
        if not chamado.data_primeira_resposta:
            limite = config.tempo_primeira_resposta
        else:
            limite = config.tempo_resolucao
        
        # Percentual consumido
        percentual_consumido = (tempo_decorrido / limite * 100) if limite > 0 else 0
        
        # Atualiza campos
        chamado.sla_tempo_decorrido_horas = tempo_decorrido
        chamado.sla_tempo_pausado_horas = tempo_pausa
        chamado.sla_percentual_consumido = percentual_consumido
        chamado.sla_atualizado_em = agora
        
        # Verifica status
        if percentual_consumido >= 100:
            chamado.sla_vencido = True
            chamado.sla_em_risco = False
        elif percentual_consumido >= config.percentual_risco:
            chamado.sla_em_risco = True
        else:
            chamado.sla_em_risco = False
            chamado.sla_vencido = False
        
        self.db.commit()
