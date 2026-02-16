from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base

class ConfiguracesSla(Base):
    __tablename__ = "configuracoes_sla"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prioridade: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    tempo_primeira_resposta: Mapped[float] = mapped_column(Float, nullable=False)  # em horas
    tempo_resolucao: Mapped[float] = mapped_column(Float, nullable=False)  # em horas
    considera_horario_comercial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    considera_feriados: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    escalar_automaticamente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notificar_em_risco: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    percentual_risco: Mapped[float] = mapped_column(Float, nullable=False, default=75.0)  # percentual
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_atualizacao: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
