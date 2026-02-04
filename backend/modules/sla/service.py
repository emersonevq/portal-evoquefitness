"""Camada de negócio para SLA"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from core.db import SessionLocal
from .models import SlaPausa, SlaFeriado, SlaCalculationLog
from .repository import SlaRepository
from .calculator import SlaCalculator
from .cache import SlaCache
from .schemas import SlaDashboard, SlaChamadoStatus, SlaDashboardResumo
from .config import SLA_COUNTING_STATUSES, SLA_PAUSED_STATUSES, SLA_FINISHED_STATUSES

logger = logging.getLogger("sla.service")


class SlaService:
    """Serviço de SLA - Orquestra cálculos e atualizações"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.repo = SlaRepository(self.db)
        self.cache = SlaCache()
    
    def _obter_feriados_para_calc(self) -> List[datetime]:
        """Obtém lista de feriados para cálculo"""
        # Tenta obter do cache
        feriados = self.cache.get_feriados()
        if feriados is not None:
            return feriados
        
        # Busca do banco
        feriados = self.repo.obter_feriados_ativo()
        feriados_list = [f.data for f in feriados]
        
        # Armazena no cache
        self.cache.set_feriados(feriados_list)
        
        return feriados_list
    
    def _obter_calculador(self) -> SlaCalculator:
        """Obtém calculador com feriados atualizados"""
        feriados = self._obter_feriados_para_calc()
        return SlaCalculator(feriados=feriados)
    
    def obter_config_chamado(self, prioridade: str) -> Optional[Dict]:
        """Obtém configuração de SLA para uma prioridade"""
        config = self.repo.obter_config_por_prioridade(prioridade)
        if config:
            return {
                "prioridade": config.prioridade,
                "tempo_resposta_horas": config.tempo_resposta_horas,
                "tempo_resolucao_horas": config.tempo_resolucao_horas
            }
        return None
    
    def calcular_sla_chamado(
        self,
        chamado_id: int,
        data_abertura: datetime,
        data_primeira_resposta: Optional[datetime],
        data_conclusao: Optional[datetime],
        status: str,
        prioridade: str
    ) -> SlaChamadoStatus:
        """
        Calcula SLA de um chamado específico
        
        Returns:
            SlaChamadoStatus com todos os dados
        """
        # Obter configuração
        config = self.obter_config_chamado(prioridade)
        if not config:
            logger.warning(f"Configuração SLA não encontrada para {prioridade}")
            return None
        
        # Obter pausas
        pausas = self.repo.obter_pausas_chamado(chamado_id)
        pausas_list = [(p.pausado_em, p.retomado_em) for p in pausas if p.retomado_em]
        
        # Obter calculador
        calc = self._obter_calculador()
        
        # Data de referência
        data_ref = data_conclusao or datetime.now()
        
        # Calcular resposta
        resposta_trabalhada, resposta_pausada = 0.0, 0.0
        resposta_em_dia = resposta_em_risco = resposta_vencida = False
        percentual_resposta = 0.0
        
        if data_primeira_resposta:
            resposta_trabalhada, resposta_pausada = calc.calcular_horas_uteis_com_pausas(
                data_abertura, data_primeira_resposta, pausas_list
            )
            percentual_resposta = calc.calcular_percentual_sla(
                resposta_trabalhada, config["tempo_resposta_horas"]
            )
            resposta_vencida = calc.eh_vencido(resposta_trabalhada, config["tempo_resposta_horas"])
            resposta_em_risco = calc.eh_em_risco(resposta_trabalhada, config["tempo_resposta_horas"])
            resposta_em_dia = not resposta_vencida and not resposta_em_risco
        
        # Calcular resolução
        resolucao_trabalhada, resolucao_pausada = calc.calcular_horas_uteis_com_pausas(
            data_abertura, data_ref, pausas_list
        )
        percentual_resolucao = calc.calcular_percentual_sla(
            resolucao_trabalhada, config["tempo_resolucao_horas"]
        )
        resolucao_vencida = calc.eh_vencido(resolucao_trabalhada, config["tempo_resolucao_horas"])
        resolucao_em_risco = calc.eh_em_risco(resolucao_trabalhada, config["tempo_resolucao_horas"])
        resolucao_em_dia = not resolucao_vencida and not resolucao_em_risco
        
        # Verificar se está pausado
        pausado = status.lower() == "em análise"
        ativo = status.lower() in [s.lower() for s in SLA_COUNTING_STATUSES]
        
        return SlaChamadoStatus(
            chamado_id=chamado_id,
            codigo=f"#{chamado_id}",
            prioridade=prioridade,
            status=status,
            tempo_decorrido_horas=resolucao_trabalhada,
            tempo_pausado_horas=resolucao_pausada,
            tempo_limite_resposta_horas=config["tempo_resposta_horas"],
            tempo_limite_resolucao_horas=config["tempo_resolucao_horas"],
            resposta_em_dia=resposta_em_dia,
            resposta_em_risco=resposta_em_risco,
            resposta_vencida=resposta_vencida,
            resolucao_em_dia=resolucao_em_dia,
            resolucao_em_risco=resolucao_em_risco,
            resolucao_vencida=resolucao_vencida,
            percentual_resposta=percentual_resposta,
            percentual_resolucao=percentual_resolucao,
            pausado=pausado,
            ativo=ativo
        )
    
    def obter_dashboard(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> SlaDashboard:
        """
        Obtém dashboard completo de SLA
        
        Calcula métricas para os últimos 30 dias por padrão
        """
        if not data_fim:
            data_fim = datetime.now()
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        
        logger.info(f"[SLA] Calculando dashboard: {data_inicio} a {data_fim}")
        
        try:
            # Buscar chamados no período
            from ti.models.chamado import Chamado
            
            chamados = self.db.query(Chamado).filter(
                Chamado.data_abertura >= data_inicio
            ).all()
            
            logger.info(f"[SLA] Encontrados {len(chamados)} chamados para processar")
            
            # Calcular SLA de cada chamado
            chamados_sla = []
            em_risco = []
            vencidos = []
            pausados = []
            
            for chamado in chamados:
                try:
                    sla_status = self.calcular_sla_chamado(
                        chamado.id,
                        chamado.data_abertura,
                        chamado.data_primeira_resposta,
                        chamado.data_conclusao,
                        chamado.status,
                        chamado.prioridade
                    )
                    
                    if sla_status:
                        chamados_sla.append(sla_status)
                        
                        if sla_status.pausado:
                            pausados.append(sla_status)
                        elif sla_status.resolucao_vencida:
                            vencidos.append(sla_status)
                        elif sla_status.resolucao_em_risco:
                            em_risco.append(sla_status)
                
                except Exception as e:
                    logger.error(f"Erro ao calcular SLA do chamado {chamado.id}: {e}")
                    continue
            
            # Calcular percentuais
            total = len(chamados_sla)
            
            # Resposta
            resposta_ok = sum(1 for s in chamados_sla if s.resposta_em_dia)
            resposta_risco = sum(1 for s in chamados_sla if s.resposta_em_risco)
            resposta_vencido = sum(1 for s in chamados_sla if s.resposta_vencida)
            percentual_resposta = (resposta_ok / total * 100) if total > 0 else 0
            tempo_medio_resposta = sum(s.percentual_resposta for s in chamados_sla) / total if total > 0 else 0
            
            # Resolução
            resolucao_ok = sum(1 for s in chamados_sla if s.resolucao_em_dia)
            resolucao_risco = sum(1 for s in chamados_sla if s.resolucao_em_risco)
            resolucao_vencido = sum(1 for s in chamados_sla if s.resolucao_vencida)
            percentual_resolucao = (resolucao_ok / total * 100) if total > 0 else 0
            tempo_medio_resolucao = sum(s.percentual_resolucao for s in chamados_sla) / total if total > 0 else 0
            
            return SlaDashboard(
                periodo_inicio=data_inicio,
                periodo_fim=data_fim,
                total_chamados=len(chamados),
                chamados_ativos=sum(1 for c in chamados if c.status.lower() in [s.lower() for s in SLA_COUNTING_STATUSES]),
                chamados_concluidos=sum(1 for c in chamados if c.status.lower() in [s.lower() for s in SLA_FINISHED_STATUSES]),
                chamados_resposta_ok=resposta_ok,
                chamados_resposta_risco=resposta_risco,
                chamados_resposta_vencido=resposta_vencido,
                percentual_resposta_ok=percentual_resposta,
                tempo_medio_resposta_horas=tempo_medio_resposta,
                chamados_resolucao_ok=resolucao_ok,
                chamados_resolucao_risco=resolucao_risco,
                chamados_resolucao_vencido=resolucao_vencido,
                percentual_resolucao_ok=percentual_resolucao,
                tempo_medio_resolucao_horas=tempo_medio_resolucao,
                chamados_em_risco=len(em_risco),
                chamados_vencidos=len(vencidos),
                chamados_pausados=len(pausados),
                lista_em_risco=em_risco[:50],  # Top 50
                lista_vencidos=vencidos[:50],
                lista_pausados=pausados[:50],
                ultima_atualizacao=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Erro ao gerar dashboard SLA: {e}", exc_info=True)
            raise
