"""Repositório para acesso a dados de SLA"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import SlaConfiguration, SlaFeriado, SlaCalculationLog, SlaPausa, SlaBusinessHours
from .schemas import SlaPausaCreate


class SlaRepository:
    """Repositório para operações de SLA"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== Configurações ==========
    
    def obter_config_por_prioridade(self, prioridade: str) -> Optional[SlaConfiguration]:
        """Obtém configuração de SLA por prioridade"""
        return self.db.query(SlaConfiguration).filter(
            SlaConfiguration.prioridade == prioridade.lower(),
            SlaConfiguration.ativo == True
        ).first()
    
    def obter_todas_configs(self) -> List[SlaConfiguration]:
        """Obtém todas as configurações ativas"""
        return self.db.query(SlaConfiguration).filter(
            SlaConfiguration.ativo == True
        ).all()
    
    def criar_config(self, prioridade: str, tempo_resposta: float, tempo_resolucao: float) -> SlaConfiguration:
        """Cria uma nova configuração de SLA"""
        config = SlaConfiguration(
            prioridade=prioridade.lower(),
            tempo_resposta_horas=tempo_resposta,
            tempo_resolucao_horas=tempo_resolucao
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    # ========== Feriados ==========
    
    def obter_feriados_ativo(self) -> List[SlaFeriado]:
        """Obtém todos os feriados ativos"""
        return self.db.query(SlaFeriado).filter(
            SlaFeriado.ativo == True
        ).all()
    
    def obter_feriados_entre(self, data_inicio: datetime, data_fim: datetime) -> List[SlaFeriado]:
        """Obtém feriados entre duas datas"""
        return self.db.query(SlaFeriado).filter(
            and_(
                SlaFeriado.data >= data_inicio,
                SlaFeriado.data <= data_fim,
                SlaFeriado.ativo == True
            )
        ).all()
    
    def criar_feriado(self, data: datetime, nome: str, descricao: str = None) -> SlaFeriado:
        """Cria um novo feriado"""
        feriado = SlaFeriado(
            data=data,
            nome=nome,
            descricao=descricao
        )
        self.db.add(feriado)
        self.db.commit()
        self.db.refresh(feriado)
        return feriado
    
    # ========== Pausas ==========
    
    def obter_pausas_chamado(self, chamado_id: int) -> List[SlaPausa]:
        """Obtém todas as pausas de um chamado"""
        return self.db.query(SlaPausa).filter(
            SlaPausa.chamado_id == chamado_id
        ).order_by(SlaPausa.pausado_em).all()
    
    def obter_pausas_ativas_chamado(self, chamado_id: int) -> List[SlaPausa]:
        """Obtém pausas ativas de um chamado"""
        return self.db.query(SlaPausa).filter(
            and_(
                SlaPausa.chamado_id == chamado_id,
                SlaPausa.ativa == True
            )
        ).all()
    
    def criar_pausa(self, pausa_data: SlaPausaCreate, usuario_id: Optional[int] = None) -> SlaPausa:
        """Cria uma nova pausa de SLA"""
        pausa = SlaPausa(
            chamado_id=pausa_data.chamado_id,
            pausado_em=pausa_data.pausado_em,
            motivo=pausa_data.motivo,
            criado_por_id=usuario_id
        )
        self.db.add(pausa)
        self.db.commit()
        self.db.refresh(pausa)
        return pausa
    
    def retiomar_pausa(self, pausa_id: int, retomado_em: datetime = None) -> Optional[SlaPausa]:
        """Retoma uma pausa (marcando como finalizada)"""
        pausa = self.db.query(SlaPausa).filter(SlaPausa.id == pausa_id).first()
        if pausa:
            pausa.retomado_em = retomado_em or datetime.now()
            pausa.ativa = False
            pausa.duracao_minutos = pausa.calcular_duracao()
            self.db.commit()
            self.db.refresh(pausa)
        return pausa
    
    def pausar_automaticamente_se_necessario(self, chamado_id: int, status: str) -> Optional[SlaPausa]:
        """Pausa automaticamente se status é 'Em análise'"""
        if status.lower() != "em análise":
            return None
        
        # Verifica se já tem pausa ativa
        pausas_ativas = self.obter_pausas_ativas_chamado(chamado_id)
        if pausas_ativas:
            return pausas_ativas[0]  # Já tem pausa ativa
        
        # Cria nova pausa
        pausa_data = SlaPausaCreate(
            chamado_id=chamado_id,
            pausado_em=datetime.now(),
            motivo="Em análise"
        )
        return self.criar_pausa(pausa_data)
    
    def retomar_pausas_se_necessario(self, chamado_id: int, status: str) -> List[SlaPausa]:
        """Retoma pausas se status mudou de 'Em análise'"""
        if status.lower() == "em análise":
            return []
        
        pausas_ativas = self.obter_pausas_ativas_chamado(chamado_id)
        retomadas = []
        
        for pausa in pausas_ativas:
            self.retiomar_pausa(pausa.id)
            retomadas.append(pausa)
        
        return retomadas
    
    # ========== Logs ==========
    
    def registrar_calculo(
        self,
        calculation_type: str,
        chamados_count: int,
        execution_time_ms: float,
        success: bool = True,
        error_message: str = None
    ) -> SlaCalculationLog:
        """Registra um cálculo de SLA"""
        log = SlaCalculationLog(
            calculation_type=calculation_type,
            chamados_count=chamados_count,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def obter_ultimos_logs(self, limit: int = 10) -> List[SlaCalculationLog]:
        """Obtém últimos logs de cálculo"""
        return self.db.query(SlaCalculationLog).order_by(
            SlaCalculationLog.created_at.desc()
        ).limit(limit).all()
