from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base

class SlaPausa(Base):
    __tablename__ = "sla_pausas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chamado_id: Mapped[int] = mapped_column(Integer, ForeignKey("chamado.id"), nullable=False)
    pausado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    retomado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duracao_minutos: Mapped[float | None] = mapped_column(Float, nullable=True)
    criado_por_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
