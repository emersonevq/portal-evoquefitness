from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base

class HistoricoSla(Base):
    __tablename__ = "historico_sla"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chamado_id: Mapped[int] = mapped_column(Integer, ForeignKey("chamado.id"), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    acao: Mapped[str] = mapped_column(String(100), nullable=False)  # 'iniciar_sla', 'primeira_resposta', 'pausa', 'retoma', 'concluido'
    status_anterior: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status_novo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_conclusao_anterior: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_conclusao_nova: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tempo_resposta_horas: Mapped[float | None] = mapped_column(Float, nullable=True)
    limite_sla_resposta_horas: Mapped[float | None] = mapped_column(Float, nullable=True)
    tempo_resolucao_horas: Mapped[float | None] = mapped_column(Float, nullable=True)
    limite_sla_horas: Mapped[float | None] = mapped_column(Float, nullable=True)
    status_sla: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'dentro', 'fora'
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    session_revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
