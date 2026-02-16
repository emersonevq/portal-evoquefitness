"""
Serviço de métricas de SLA.

Calcula:
- Taxa de cumprimento geral
- Tempo médio de resposta
- Tempo médio de resolução
- Métricas por prioridade
"""

from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from ti.models import Chamado, HistoricoSla, ConfiguracesSla

class MetricasService:
    def __init__(self, db: Session):
        self.db = db
    
    def obter_metricas_periodo(self, data_inicio: date, data_fim: date) -> dict:
        """
        Obtém métricas de SLA para um período.
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final
        
        Returns:
            Dicionário com métricas agregadas
        """
        # Chamados concluídos no período
        chamados = self.db.query(Chamado).filter(
            Chamado.data_conclusao >= datetime.combine(data_inicio, datetime.min.time()),
            Chamado.data_conclusao <= datetime.combine(data_fim, datetime.max.time()),
            Chamado.data_conclusao != None,
            Chamado.retroativo == False  # Ignora retroativos
        ).all()
        
        if not chamados:
            return {
                "total_chamados": 0,
                "chamados_dentro_sla": 0,
                "chamados_fora_sla": 0,
                "taxa_cumprimento": 0.0,
                "tempo_resposta_medio": 0.0,
                "tempo_resolucao_medio": 0.0,
                "tempo_pausa_total": 0.0,
            }
        
        # Conta cumprimento
        dentro_sla = sum(1 for c in chamados if c.sla_percentual_consumido <= 100)
        fora_sla = len(chamados) - dentro_sla
        
        # Calcula tempos médios
        tempo_resposta_total = 0
        tempo_resolucao_total = 0
        tempo_pausa_total = 0
        
        for chamado in chamados:
            if chamado.data_primeira_resposta:
                tempo_resposta = (
                    chamado.data_primeira_resposta - chamado.data_abertura
                ).total_seconds() / 3600
                tempo_resposta_total += tempo_resposta
            
            if chamado.sla_tempo_decorrido_horas:
                tempo_resolucao_total += chamado.sla_tempo_decorrido_horas
            
            if chamado.sla_tempo_pausado_horas:
                tempo_pausa_total += chamado.sla_tempo_pausado_horas
        
        tempo_resposta_medio = tempo_resposta_total / len(chamados) if chamados else 0
        tempo_resolucao_medio = tempo_resolucao_total / len(chamados) if chamados else 0
        
        taxa_cumprimento = (dentro_sla / len(chamados) * 100) if chamados else 0
        
        return {
            "total_chamados": len(chamados),
            "chamados_dentro_sla": dentro_sla,
            "chamados_fora_sla": fora_sla,
            "taxa_cumprimento": taxa_cumprimento,
            "tempo_resposta_medio": tempo_resposta_medio,
            "tempo_resolucao_medio": tempo_resolucao_medio,
            "tempo_pausa_total": tempo_pausa_total,
        }
    
    def obter_metricas_por_prioridade(self, data_inicio: date, data_fim: date) -> dict:
        """
        Obtém métricas de SLA por prioridade.
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final
        
        Returns:
            Dicionário com métricas por prioridade
        """
        prioridades = self.db.query(ConfiguracesSla).filter(
            ConfiguracesSla.ativo == True
        ).all()
        
        resultado = {}
        
        for config in prioridades:
            chamados = self.db.query(Chamado).filter(
                Chamado.prioridade == config.prioridade,
                Chamado.data_conclusao >= datetime.combine(data_inicio, datetime.min.time()),
                Chamado.data_conclusao <= datetime.combine(data_fim, datetime.max.time()),
                Chamado.data_conclusao != None,
                Chamado.retroativo == False
            ).all()
            
            if not chamados:
                resultado[config.prioridade] = {
                    "total": 0,
                    "dentro_sla": 0,
                    "fora_sla": 0,
                    "taxa_cumprimento": 0.0
                }
                continue
            
            dentro_sla = sum(1 for c in chamados if c.sla_percentual_consumido <= 100)
            fora_sla = len(chamados) - dentro_sla
            taxa = (dentro_sla / len(chamados) * 100) if chamados else 0
            
            resultado[config.prioridade] = {
                "total": len(chamados),
                "dentro_sla": dentro_sla,
                "fora_sla": fora_sla,
                "taxa_cumprimento": taxa
            }
        
        return resultado
    
    def obter_indicadores_agora(self) -> dict:
        """
        Obtém indicadores em tempo real (agora).
        
        Returns:
            Dicionário com contadores de status
        """
        return {
            "abertos": self.db.query(Chamado).filter(
                Chamado.status == "Aberto",
                Chamado.deletado_em == None
            ).count(),
            "em_atendimento": self.db.query(Chamado).filter(
                Chamado.status == "Em atendimento",
                Chamado.deletado_em == None
            ).count(),
            "aguardando": self.db.query(Chamado).filter(
                Chamado.status == "Aguardando",
                Chamado.deletado_em == None
            ).count(),
            "em_risco": self.db.query(Chamado).filter(
                Chamado.sla_em_risco == True,
                Chamado.deletado_em == None
            ).count(),
            "vencidos": self.db.query(Chamado).filter(
                Chamado.sla_vencido == True,
                Chamado.deletado_em == None
            ).count(),
        }
