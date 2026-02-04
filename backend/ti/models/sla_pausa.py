from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base


class SLAPausa(Base):
    __tablename__ = "sla_pausas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chamado_id: Mapped[int] = mapped_column(Integer, ForeignKey("chamado.id"), nullable=False)
    pausado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    retomado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    motivo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    criado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    atualizado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    chamado: Mapped["Chamado"] = relationship("Chamado", back_populates="pausas_sla")
