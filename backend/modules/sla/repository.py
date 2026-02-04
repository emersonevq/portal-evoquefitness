from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any

from .models import (
    SlaConfiguration, SlaFeriado, SlaBusinessHours,
    SlaCalculationLog, SlaPausa
)
from .constants import STATUS_FINALIZADOS, normalizar_status
from ti.models.chamado import Chamado


class SlaRepository:
    """Repositório de acesso a dados do SLA"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Configurações ====================
    
    def get_all_configs(self, apenas_ativos: bool = True) -> List[SlaConfiguration]:
        query = self.db.query(SlaConfiguration)
        if apenas_ativos:
            query = query.filter(SlaConfiguration.ativo)
        return query.order_by(SlaConfiguration.prioridade).all()
    
    def get_config_by_prioridade(self, prioridade: str) -> Optional[SlaConfiguration]:
        prioridade_norm = prioridade.lower().strip() if prioridade else ""
        return self.db.query(SlaConfiguration).filter(
            and_(
                func.lower(SlaConfiguration.prioridade) == prioridade_norm,
                SlaConfiguration.ativo
            )
        ).first()
    
    def get_configs_map(self) -> Dict[str, SlaConfiguration]:
        configs = self.get_all_configs()
        return {c.prioridade.lower(): c for c in configs}
    
    def config_exists(self, prioridade: str) -> bool:
        """Verifica se já existe config para a prioridade"""
        return self.get_config_by_prioridade(prioridade) is not None
    
    def create_config(self, data: Dict[str, Any]) -> SlaConfiguration:
        config = SlaConfiguration(**data)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def update_config(self, config_id: int, data: Dict[str, Any]) -> Optional[SlaConfiguration]:
        config = self.db.query(SlaConfiguration).filter(
            SlaConfiguration.id == config_id
        ).first()
        
        if config:
            for key, value in data.items():
                if value is not None:
                    setattr(config, key, value)
            config.atualizado_em = datetime.now()
            self.db.commit()
            self.db.refresh(config)
        
        return config
    
    def delete_config(self, config_id: int) -> bool:
        config = self.db.query(SlaConfiguration).filter(
            SlaConfiguration.id == config_id
        ).first()
        if config:
            config.ativo = False
            config.atualizado_em = datetime.now()
            self.db.commit()
            return True
        return False
    
    # ==================== Feriados ====================
    
    def get_feriados(self, ano: int = None, apenas_ativos: bool = True) -> List[SlaFeriado]:
        query = self.db.query(SlaFeriado)
        if apenas_ativos:
            query = query.filter(SlaFeriado.ativo)
        if ano:
            query = query.filter(func.year(SlaFeriado.data) == ano)
        return query.order_by(SlaFeriado.data).all()
    
    def get_feriados_between(self, start: datetime, end: datetime) -> List[date]:
        feriados = self.db.query(SlaFeriado).filter(
            and_(
                SlaFeriado.ativo,
                SlaFeriado.data.between(start, end)
            )
        ).all()
        
        resultado = []
        for f in feriados:
            if isinstance(f.data, datetime):
                resultado.append(f.data.date())
            else:
                resultado.append(f.data)
        return resultado
    
    def feriado_exists(self, data: datetime) -> bool:
        """Verifica se já existe feriado na data"""
        return self.db.query(SlaFeriado).filter(
            and_(
                SlaFeriado.data == data,
                SlaFeriado.ativo
            )
        ).first() is not None
    
    def create_feriado(self, data: Dict[str, Any]) -> SlaFeriado:
        feriado = SlaFeriado(**data)
        self.db.add(feriado)
        self.db.commit()
        self.db.refresh(feriado)
        return feriado
    
    def delete_feriado(self, feriado_id: int) -> bool:
        feriado = self.db.query(SlaFeriado).filter(
            SlaFeriado.id == feriado_id
        ).first()
        if feriado:
            self.db.delete(feriado)
            self.db.commit()
            return True
        return False
    
    # ==================== Pausas ====================
    
    def criar_pausa(
        self,
        chamado_id: int,
        motivo: str = "Em análise",
        usuario_id: int = None
    ) -> SlaPausa:
        """Cria nova pausa. Se já houver ativa, retorna a existente."""
        pausa_ativa = self.get_pausa_ativa(chamado_id)
        if pausa_ativa:
            return pausa_ativa
        
        pausa = SlaPausa(
            chamado_id=chamado_id,
            pausado_em=datetime.now(),
            motivo=motivo,
            ativa=True,
            criado_por_id=usuario_id
        )
        self.db.add(pausa)
        self.db.commit()
        self.db.refresh(pausa)
        return pausa
    
    def finalizar_pausa(self, chamado_id: int) -> Optional[SlaPausa]:
        """Finaliza a pausa ativa de um chamado"""
        pausa = self.get_pausa_ativa(chamado_id)
        
        if pausa:
            pausa.retomado_em = datetime.now()
            pausa.ativa = False
            pausa.duracao_minutos = int(
                (pausa.retomado_em - pausa.pausado_em).total_seconds() / 60
            )
            pausa.atualizado_em = datetime.now()
            self.db.commit()
            self.db.refresh(pausa)
        
        return pausa
    
    def finalizar_todas_pausas(self, chamado_id: int) -> int:
        """Finaliza TODAS as pausas ativas de um chamado"""
        pausas_ativas = self.get_pausas_ativas_chamado(chamado_id)
        count = 0
        
        for pausa in pausas_ativas:
            pausa.retomado_em = datetime.now()
            pausa.ativa = False
            pausa.duracao_minutos = int(
                (pausa.retomado_em - pausa.pausado_em).total_seconds() / 60
            )
            pausa.atualizado_em = datetime.now()
            count += 1
        
        if count > 0:
            self.db.commit()
        
        return count
    
    def get_pausas_chamado(self, chamado_id: int) -> List[SlaPausa]:
        """Retorna TODAS as pausas de um chamado"""
        return self.db.query(SlaPausa).filter(
            SlaPausa.chamado_id == chamado_id
        ).order_by(SlaPausa.pausado_em).all()
    
    def get_pausas_ativas_chamado(self, chamado_id: int) -> List[SlaPausa]:
        """Retorna apenas pausas ATIVAS"""
        return self.db.query(SlaPausa).filter(
            and_(
                SlaPausa.chamado_id == chamado_id,
                SlaPausa.ativa
            )
        ).all()
    
    def get_pausa_ativa(self, chamado_id: int) -> Optional[SlaPausa]:
        """Retorna a pausa ativa atual"""
        return self.db.query(SlaPausa).filter(
            and_(
                SlaPausa.chamado_id == chamado_id,
                SlaPausa.ativa
            )
        ).first()
    
    def get_tempo_total_pausado(self, chamado_id: int) -> int:
        """Retorna minutos totais pausados"""
        pausas = self.get_pausas_chamado(chamado_id)
        
        total = 0
        for pausa in pausas:
            if pausa.duracao_minutos:
                total += pausa.duracao_minutos
            elif pausa.ativa:
                total += int((datetime.now() - pausa.pausado_em).total_seconds() / 60)
        
        return total
    
    def get_pausas_para_calculo(self, chamado_id: int) -> List[Dict]:
        """Retorna pausas no formato do calculator"""
        pausas = self.get_pausas_chamado(chamado_id)
        return [
            {
                "pausado_em": p.pausado_em,
                "retomado_em": p.retomado_em
            }
            for p in pausas
        ]
    
    # ==================== Chamados ====================
    
    def get_chamados_ativos(self, dias_atras: int = 30) -> List[Chamado]:
        """
        Retorna chamados não finalizados abertos nos últimos N dias (padrão: 30)

        Args:
            dias_atras: Número de dias para considerar (padrão 30)
        """
        status_finalizados = list(STATUS_FINALIZADOS)
        data_inicio = datetime.now() - timedelta(days=dias_atras)

        return self.db.query(Chamado).filter(
            and_(
                ~func.lower(Chamado.status).in_(status_finalizados),
                Chamado.data_abertura >= data_inicio
            )
        ).all()
    
    def get_chamados_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        prioridade: str = None,
        status: str = None,
        apenas_ativos: bool = False
    ) -> List[Chamado]:
        """Retorna chamados em um período"""
        if data_inicio > data_fim:
            data_inicio, data_fim = data_fim, data_inicio
        
        query = self.db.query(Chamado).filter(
            Chamado.data_abertura.between(data_inicio, data_fim)
        )
        
        if prioridade:
            query = query.filter(func.lower(Chamado.prioridade) == prioridade.lower())
        
        if status:
            query = query.filter(func.lower(Chamado.status) == status.lower())
        
        if apenas_ativos:
            status_finalizados = list(STATUS_FINALIZADOS)
            query = query.filter(~func.lower(Chamado.status).in_(status_finalizados))
        
        return query.order_by(desc(Chamado.data_abertura)).all()
    
    def get_chamado_by_id(self, chamado_id: int) -> Optional[Chamado]:
        return self.db.query(Chamado).filter(
            Chamado.id == chamado_id
        ).first()
    
    def update_chamado_sla(
        self,
        chamado_id: int,
        em_risco: bool,
        vencido: bool,
        tempo_decorrido: float = None,
        tempo_pausado: float = None,
        percentual: float = None
    ) -> bool:
        """Atualiza campos de SLA do chamado"""
        chamado = self.get_chamado_by_id(chamado_id)
        
        if not chamado:
            return False
        
        chamado.sla_em_risco = em_risco
        chamado.sla_vencido = vencido
        chamado.sla_atualizado_em = datetime.now()
        
        if tempo_decorrido is not None:
            chamado.sla_tempo_decorrido_horas = tempo_decorrido
        if tempo_pausado is not None:
            chamado.sla_tempo_pausado_horas = tempo_pausado
        if percentual is not None:
            chamado.sla_percentual_consumido = percentual
        
        if vencido and not chamado.sla_ultimo_escalonamento:
            chamado.sla_ultimo_escalonamento = datetime.now()
        
        self.db.commit()
        return True
    
    # ==================== Logs ====================
    
    def log_calculation(
        self,
        calc_type: str,
        chamados_count: int,
        em_risco: int = 0,
        vencidos: int = 0,
        pausados: int = 0,
        execution_time: float = 0,
        success: bool = True,
        error_message: str = None,
        last_chamado_id: int = None
    ) -> SlaCalculationLog:
        log = SlaCalculationLog(
            calculation_type=calc_type,
            last_calculated_at=datetime.now(),
            last_calculated_chamado_id=last_chamado_id,
            chamados_count=chamados_count,
            chamados_em_risco=em_risco,
            chamados_vencidos=vencidos,
            chamados_pausados=pausados,
            execution_time_ms=execution_time,
            success=success,
            error_message=error_message
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_ultimo_calculo(self) -> Optional[SlaCalculationLog]:
        return self.db.query(SlaCalculationLog).filter(
            SlaCalculationLog.success
        ).order_by(desc(SlaCalculationLog.last_calculated_at)).first()
    
    def get_logs_recentes(self, limite: int = 10) -> List[SlaCalculationLog]:
        return self.db.query(SlaCalculationLog).order_by(
            desc(SlaCalculationLog.last_calculated_at)
        ).limit(limite).all()
