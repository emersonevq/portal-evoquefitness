"""
Serviço de métricas e estatísticas de SLA
Fornece dashboards e relatórios agregados
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case
import logging

from .models import (
    Chamado, ConfiguracaoSLA, InfoSLAChamado, PausaSLA,
    StatusChamado
)
from .calculator import CalculadorSLA, STATUS_PAUSA, STATUS_CONTA, STATUS_FINAL

logger = logging.getLogger("sla.metrics")


class ServicoMetricasSLA:
    """Serviço para cálculo de métricas e dashboard de SLA"""
    
    def __init__(self, db: Session):
        self.db = db
        self.calculator = CalculadorSLA(db)
    
    # ==================== Métricas Gerais ====================
    
    def obter_metricas_gerais(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> Dict:
        """
        Obtém métricas gerais de SLA para um período
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
        
        Returns:
            Dicionário com métricas agregadas
        """
        if not data_fim:
            data_fim = date.today()
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        
        logger.info(f"Calculando métricas: {data_inicio} a {data_fim}")
        
        # Query base
        query = self.db.query(Chamado).filter(
            and_(
                Chamado.data_abertura >= datetime.combine(data_inicio, __import__('datetime').time(0, 0)),
                Chamado.data_abertura <= datetime.combine(data_fim, __import__('datetime').time(23, 59, 59)),
                Chamado.deletado_em.is_(None)
            )
        )
        
        total_chamados = query.count()
        
        if total_chamados == 0:
            return self._metricas_vazio()
        
        # Estatísticas por status
        abertos = query.filter(Chamado.status.in_(STATUS_CONTA)).count()
        pausados = query.filter(Chamado.status.in_(STATUS_PAUSA)).count()
        concluidos = query.filter(
            and_(
                Chamado.status.in_(STATUS_FINAL),
                Chamado.data_conclusao.isnot(None)
            )
        ).count()
        
        # Processa cada chamado para cálculos
        chamados = query.all()
        
        em_risco = 0
        vencidos = 0
        tempos_resposta = []
        tempos_resolucao = []
        
        for chamado in chamados:
            sla = self.calculator.calcular_sla(chamado)
            
            if sla.get("resolucao_em_risco"):
                em_risco += 1
            if sla.get("resolucao_vencida"):
                vencidos += 1
            
            # Coleta tempos para cálculo de média
            if chamado.data_primeira_resposta:
                tempo_resp = (chamado.data_primeira_resposta - chamado.data_abertura).total_seconds() / 3600
                tempos_resposta.append(tempo_resp)
            
            if chamado.data_conclusao:
                tempo_resol = (chamado.data_conclusao - chamado.data_abertura).total_seconds() / 3600
                tempos_resolucao.append(tempo_resol)
        
        # Calcula médias
        tempo_medio_resposta = sum(tempos_resposta) / len(tempos_resposta) if tempos_resposta else 0
        tempo_medio_resolucao = sum(tempos_resolucao) / len(tempos_resolucao) if tempos_resolucao else 0
        
        # Percentuais
        pct_em_risco = (em_risco / total_chamados * 100) if total_chamados > 0 else 0
        pct_vencidos = (vencidos / total_chamados * 100) if total_chamados > 0 else 0
        pct_cumprimento = 100 - pct_vencidos
        
        return {
            "periodo_inicio": data_inicio,
            "periodo_fim": data_fim,
            "total_chamados": total_chamados,
            "chamados_abertos": abertos,
            "chamados_em_risco": em_risco,
            "chamados_vencidos": vencidos,
            "chamados_pausados": pausados,
            "chamados_concluidos": concluidos,
            "percentual_em_risco": round(pct_em_risco, 2),
            "percentual_vencidos": round(pct_vencidos, 2),
            "percentual_cumprimento": round(pct_cumprimento, 2),
            "tempo_medio_resposta_horas": round(tempo_medio_resposta, 2),
            "tempo_medio_resolucao_horas": round(tempo_medio_resolucao, 2)
        }
    
    def _metricas_vazio(self) -> Dict:
        """Retorna métricas vazias"""
        return {
            "total_chamados": 0,
            "chamados_abertos": 0,
            "chamados_em_risco": 0,
            "chamados_vencidos": 0,
            "chamados_pausados": 0,
            "chamados_concluidos": 0,
            "percentual_em_risco": 0.0,
            "percentual_vencidos": 0.0,
            "percentual_cumprimento": 100.0,
            "tempo_medio_resposta_horas": 0.0,
            "tempo_medio_resolucao_horas": 0.0
        }
    
    # ==================== Métricas por Prioridade ====================
    
    def obter_metricas_por_prioridade(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> List[Dict]:
        """
        Obtém métricas agrupadas por prioridade
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final
        
        Returns:
            Lista de dicts com métricas por prioridade
        """
        if not data_fim:
            data_fim = date.today()
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        
        # Busca prioridades configuradas
        prioridades = self.db.query(
            ConfiguracaoSLA.prioridade
        ).filter(ConfiguracaoSLA.ativo == True).all()
        
        resultado = []
        
        for (prioridade,) in prioridades:
            query = self.db.query(Chamado).filter(
                and_(
                    Chamado.prioridade == prioridade,
                    Chamado.data_abertura >= datetime.combine(data_inicio, __import__('datetime').time(0, 0)),
                    Chamado.data_abertura <= datetime.combine(data_fim, __import__('datetime').time(23, 59, 59)),
                    Chamado.deletado_em.is_(None)
                )
            )
            
            total = query.count()
            
            if total == 0:
                continue
            
            chamados = query.all()
            
            em_risco = 0
            vencidos = 0
            tempos_resposta = []
            tempos_resolucao = []
            
            for chamado in chamados:
                sla = self.calculator.calcular_sla(chamado)
                
                if sla.get("resolucao_em_risco"):
                    em_risco += 1
                if sla.get("resolucao_vencida"):
                    vencidos += 1
                
                if chamado.data_primeira_resposta:
                    tempo = (chamado.data_primeira_resposta - chamado.data_abertura).total_seconds() / 3600
                    tempos_resposta.append(tempo)
                
                if chamado.data_conclusao:
                    tempo = (chamado.data_conclusao - chamado.data_abertura).total_seconds() / 3600
                    tempos_resolucao.append(tempo)
            
            tempo_medio_resposta = sum(tempos_resposta) / len(tempos_resposta) if tempos_resposta else 0
            tempo_medio_resolucao = sum(tempos_resolucao) / len(tempos_resolucao) if tempos_resolucao else 0
            
            resultado.append({
                "prioridade": prioridade,
                "total": total,
                "em_risco": em_risco,
                "vencidos": vencidos,
                "pausados": query.filter(Chamado.status.in_(STATUS_PAUSA)).count(),
                "percentual_em_risco": round((em_risco / total * 100) if total > 0 else 0, 2),
                "percentual_vencidos": round((vencidos / total * 100) if total > 0 else 0, 2),
                "tempo_medio_resposta_horas": round(tempo_medio_resposta, 2),
                "tempo_medio_resolucao_horas": round(tempo_medio_resolucao, 2)
            })
        
        return resultado
    
    # ==================== Chamados em Risco/Vencidos ====================
    
    def obter_chamados_em_risco(
        self,
        prioridade: Optional[str] = None,
        limite: int = 50
    ) -> List[Dict]:
        """Obtém chamados com SLA em risco (80%+)"""
        query = self.db.query(Chamado).filter(
            and_(
                Chamado.status.notin_(STATUS_FINAL),
                Chamado.deletado_em.is_(None)
            )
        )
        
        if prioridade:
            query = query.filter(Chamado.prioridade == prioridade)
        
        chamados = query.all()
        em_risco = []
        
        for chamado in chamados:
            sla = self.calculator.calcular_sla(chamado)
            
            if sla.get("resolucao_em_risco"):
                em_risco.append({
                    "id": chamado.id,
                    "codigo": chamado.codigo,
                    "prioridade": chamado.prioridade,
                    "status": chamado.status,
                    "percentual_resolucao": sla.get("percentual_resolucao", 0),
                    "tempo_decorrido_horas": sla.get("tempo_resolucao_decorrido_horas", 0),
                    "tempo_limite_horas": sla.get("tempo_resolucao_limite_horas", 0),
                    "data_abertura": chamado.data_abertura
                })
        
        # Ordena por percentual consumido (maior primeiro)
        em_risco.sort(key=lambda x: x["percentual_resolucao"], reverse=True)
        
        return em_risco[:limite]
    
    def obter_chamados_vencidos(
        self,
        prioridade: Optional[str] = None,
        limite: int = 50
    ) -> List[Dict]:
        """Obtém chamados com SLA vencido (100%+)"""
        query = self.db.query(Chamado).filter(
            and_(
                Chamado.status.notin_(STATUS_FINAL),
                Chamado.deletado_em.is_(None)
            )
        )
        
        if prioridade:
            query = query.filter(Chamado.prioridade == prioridade)
        
        chamados = query.all()
        vencidos = []
        
        for chamado in chamados:
            sla = self.calculator.calcular_sla(chamado)
            
            if sla.get("resolucao_vencida"):
                vencidos.append({
                    "id": chamado.id,
                    "codigo": chamado.codigo,
                    "prioridade": chamado.prioridade,
                    "status": chamado.status,
                    "percentual_resolucao": sla.get("percentual_resolucao", 0),
                    "tempo_decorrido_horas": sla.get("tempo_resolucao_decorrido_horas", 0),
                    "tempo_limite_horas": sla.get("tempo_resolucao_limite_horas", 0),
                    "tempo_vencimento_horas": (sla.get("tempo_resolucao_decorrido_horas", 0) - sla.get("tempo_resolucao_limite_horas", 0)),
                    "data_abertura": chamado.data_abertura
                })
        
        # Ordena por tempo de vencimento (mais tempo vencido primeiro)
        vencidos.sort(key=lambda x: x["tempo_vencimento_horas"], reverse=True)
        
        return vencidos[:limite]
    
    # ==================== Dashboard Executivo ====================
    
    def obter_dashboard_executivo(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> Dict:
        """
        Obtém dashboard completo para executivos
        Inclui métricas, gráficos e alertas
        """
        metricas_gerais = self.obter_metricas_gerais(data_inicio, data_fim)
        metricas_prioridade = self.obter_metricas_por_prioridade(data_inicio, data_fim)
        em_risco = self.obter_chamados_em_risco(limite=10)
        vencidos = self.obter_chamados_vencidos(limite=10)
        
        return {
            "timestamp": datetime.utcnow(),
            "metricas_gerais": metricas_gerais,
            "metricas_por_prioridade": metricas_prioridade,
            "alertas": {
                "chamados_em_risco": em_risco,
                "chamados_vencidos": vencidos,
                "total_alertas": len(em_risco) + len(vencidos)
            },
            "observacoes": self._gerar_observacoes(metricas_gerais)
        }
    
    def _gerar_observacoes(self, metricas: Dict) -> List[str]:
        """Gera observações baseadas nas métricas"""
        obs = []
        
        if metricas["percentual_vencidos"] > 20:
            obs.append(f"⚠️ Alto índice de SLAs vencidos ({metricas['percentual_vencidos']}%)")
        
        if metricas["percentual_em_risco"] > 30:
            obs.append(f"⚠️ Muitos chamados em risco ({metricas['percentual_em_risco']}%)")
        
        if metricas["chamados_pausados"] > 0:
            obs.append(f"⏸️ Existem {metricas['chamados_pausados']} chamados pausados")
        
        if metricas["percentual_cumprimento"] >= 95:
            obs.append("✅ Excelente taxa de cumprimento de SLA")
        
        if metricas["percentual_cumprimento"] < 70:
            obs.append("🔴 Taxa de cumprimento abaixo do esperado")
        
        return obs
    
    # ==================== Histórico de Pausas ====================
    
    def obter_historico_pausas_chamado(self, chamado_id: int) -> List[Dict]:
        """Obtém histórico completo de pausas de um chamado"""
        pausas = self.db.query(PausaSLA).filter(
            PausaSLA.chamado_id == chamado_id
        ).order_by(PausaSLA.inicio).all()
        
        resultado = []
        
        for pausa in pausas:
            resultado.append({
                "id": pausa.id,
                "inicio": pausa.inicio,
                "fim": pausa.fim,
                "status": "ativo" if pausa.fim is None else "finalizado",
                "duracao_horas": pausa.duracao_horas,
                "motivo": pausa.motivo,
                "tipo": pausa.tipo
            })
        
        return resultado
    
    # ==================== Estatísticas de Horário ====================
    
    def obter_estatisticas_por_horario(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> Dict:
        """
        Analisa quando os chamados têm mais risco de vencer
        (por hora do dia, dia da semana, etc)
        """
        if not data_fim:
            data_fim = date.today()
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        
        query = self.db.query(Chamado).filter(
            and_(
                Chamado.data_abertura >= datetime.combine(data_inicio, __import__('datetime').time(0, 0)),
                Chamado.data_abertura <= datetime.combine(data_fim, __import__('datetime').time(23, 59, 59)),
                Chamado.deletado_em.is_(None)
            )
        ).all()
        
        # Agrupa por hora de abertura
        por_hora = {}
        for chamado in query:
            hora = chamado.data_abertura.hour
            if hora not in por_hora:
                por_hora[hora] = {"total": 0, "vencidos": 0}
            
            por_hora[hora]["total"] += 1
            
            sla = self.calculator.calcular_sla(chamado)
            if sla.get("resolucao_vencida"):
                por_hora[hora]["vencidos"] += 1
        
        return {
            "por_hora": por_hora,
            "periodo_inicio": data_inicio,
            "periodo_fim": data_fim
        }
