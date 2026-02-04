from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    Float, Text, Index, ForeignKey, DECIMAL
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from core.db import Base


class SlaConfiguration(Base):
    """Configuração de SLA por prioridade"""
    __tablename__ = "sla_configuration"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    prioridade = Column(String(50), nullable=False, unique=True)
    tempo_resposta_horas = Column(Float, nullable=False)
    tempo_resolucao_horas = Column(Float, nullable=False)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, onupdate=func.now())
    ultimo_reset_em = Column(DateTime)
    
    def __repr__(self):
        return f"<SlaConfig {self.prioridade}: {self.tempo_resolucao_horas}h>"


class SlaFeriado(Base):
    """Feriados que não contam no SLA"""
    __tablename__ = "sla_feriados"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    data = Column(DateTime, nullable=False, unique=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<Feriado {self.nome}: {self.data}>"


class SlaBusinessHours(Base):
    """Horário comercial por dia da semana"""
    __tablename__ = "sla_business_hours"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    dia_semana = Column(Integer, nullable=False)
    hora_inicio = Column(String(5), nullable=False, default="08:00")
    hora_fim = Column(String(5), nullable=False, default="18:00")
    ativo = Column(Boolean, default=True)


class SlaCalculationLog(Base):
    """Log de cálculos de SLA"""
    __tablename__ = "sla_calculation_log"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    calculation_type = Column(String(50), nullable=False)
    last_calculated_at = Column(DateTime, server_default=func.now())
    last_calculated_chamado_id = Column(Integer)
    chamados_count = Column(Integer, default=0)
    chamados_em_risco = Column(Integer, default=0)
    chamados_vencidos = Column(Integer, default=0)
    chamados_pausados = Column(Integer, default=0)
    execution_time_ms = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)


class SlaPausa(Base):
    """Registro de pausas do SLA"""
    __tablename__ = "sla_pausas"
    __table_args__ = (
        Index("idx_sla_pausa_chamado", "chamado_id"),
        Index("idx_sla_pausa_ativa", "chamado_id", "ativa"),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    chamado_id = Column(Integer, ForeignKey("chamado.id", ondelete="CASCADE"), nullable=False, index=True)
    pausado_em = Column(DateTime, nullable=False, default=datetime.now)
    retomado_em = Column(DateTime, nullable=True)
    motivo = Column(String(100), default="Em análise")
    duracao_minutos = Column(Integer, nullable=True)
    ativa = Column(Boolean, default=True, index=True)
    criado_por_id = Column(Integer, nullable=True)
    criado_em = Column(DateTime, default=datetime.now)
    atualizado_em = Column(DateTime, onupdate=datetime.now)
    
    def calcular_duracao(self) -> int:
        """Calcula duração em minutos"""
        if not self.pausado_em:
            return 0
        fim = self.retomado_em or datetime.now()
        return int((fim - self.pausado_em).total_seconds() / 60)
