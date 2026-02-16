from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import Integer, String, DateTime, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base

class Feriado(Base):
    __tablename__ = "feriados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False, default="fixo")  # 'fixo', 'movel', 'pontual'
    recorrente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Se ano após ano
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    usuario_criacao: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
