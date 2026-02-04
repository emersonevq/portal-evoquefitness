"""Modelos SQLAlchemy para tabelas SLA"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float, Text,
    Index, ForeignKey, DECIMAL
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
    prioridade = Column(String(50), nullable=False, unique=True, index=True)
    tempo_resposta_horas = Column(Float, nullable=False)
    tempo_resolucao_horas = Column(Float, nullable=False)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True, index=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    ultimo_reset_em = Column(DateTime)

    def __repr__(self):
        return f"<SlaConfig {self.prioridade}: {self.tempo_resolucao_horas}h>"


class SlaFeriado(Base):
    """Feriados que não contam no SLA"""
    __tablename__ = "sla_feriados"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    data = Column(DateTime, nullable=False, unique=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True, index=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Feriado {self.nome}: {self.data.strftime('%d/%m/%Y')}>"


class SlaBusinessHours(Base):
    """Horário comercial por dia da semana"""
    __tablename__ = "sla_business_hours"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    dia_semana = Column(Integer, nullable=False)  # 0=segunda, 6=domingo
    hora_inicio = Column(String(5), nullable=False, default="08:00")
    hora_fim = Column(String(5), nullable=False, default="18:00")
    ativo = Column(Boolean, default=True)

    def __repr__(self):
        dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
        return f"<BusinessHours {dias[self.dia_semana]}: {self.hora_inicio}-{self.hora_fim}>"


class SlaCalculationLog(Base):
    """Log de cálculos de SLA"""
    __tablename__ = "sla_calculation_log"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    calculation_type = Column(String(50), nullable=False, index=True)  # 'recalculo_automatico', 'manual'
    last_calculated_at = Column(DateTime, server_default=func.now())
    last_calculated_chamado_id = Column(Integer)
    chamados_count = Column(Integer, default=0)
    execution_time_ms = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        status = "✅" if self.success else "❌"
        return f"<CalcLog {status} {self.calculation_type}: {self.chamados_count} chamados>"


class SlaPausa(Base):
    """Registro de pausas do SLA"""
    __tablename__ = "sla_pausas"
    __table_args__ = (
        Index("idx_sla_pausa_chamado", "chamado_id"),
        Index("idx_sla_pausa_ativa", "ativa"),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    chamado_id = Column(Integer, nullable=False, index=True)  # FK para chamado
    pausado_em = Column(DateTime, nullable=False, default=datetime.now)
    retomado_em = Column(DateTime, nullable=True)
    motivo = Column(String(100), default="Em análise")
    duracao_minutos = Column(Integer, nullable=True)
    ativa = Column(Boolean, default=True, index=True)
    criado_por_id = Column(Integer, nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def calcular_duracao(self) -> int:
        """Calcula duração em minutos"""
        if not self.pausado_em:
            return 0
        fim = self.retomado_em or datetime.now()
        return int((fim - self.pausado_em).total_seconds() / 60)

    def __repr__(self):
        status = "⏸️" if self.ativa else "▶️"
        return f"<SlaPausa {status} chamado#{self.chamado_id}>"
