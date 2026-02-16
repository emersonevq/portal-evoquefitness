from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import Integer, String, Date, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base

class Chamado(Base):
    __tablename__ = "chamado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    protocolo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    solicitante: Mapped[str] = mapped_column(String(100), nullable=False)
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    unidade: Mapped[str] = mapped_column(String(100), nullable=False)
    problema: Mapped[str] = mapped_column(String(100), nullable=False)
    internet_item: Mapped[str | None] = mapped_column(String(50), nullable=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_visita: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_abertura: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_primeira_resposta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_conclusao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Aberto")
    prioridade: Mapped[str] = mapped_column(String(20), nullable=False, default="Normal")
    retroativo: Mapped[bool] = mapped_column(nullable=False, default=False)

    status_assumido_por_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    status_assumido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    concluido_por_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelado_por_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    cancelado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    usuario_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    deletado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # SLA-specific fields
    atribuido_por_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    agente_atual_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    chamado_origem_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("chamado.id"), nullable=True)
    reaberto: Mapped[bool] = mapped_column(nullable=False, default=False)
    numero_reaberturas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qtd_reaberturas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transferido: Mapped[bool] = mapped_column(nullable=False, default=False)
    numero_transferencias: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_ultima_transferencia: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadados_extras: Mapped[str | None] = mapped_column(Text, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # SLA monitoring fields
    sla_em_risco: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sla_vencido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sla_ultimo_escalonamento: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_tempo_decorrido_horas: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sla_tempo_pausado_horas: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sla_percentual_consumido: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sla_atualizado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    anexos: Mapped[list["ChamadoAnexo"]] = relationship("ChamadoAnexo", cascade="all, delete-orphan", back_populates="chamado")
    historicos_status: Mapped[list["HistoricoStatus"]] = relationship("HistoricoStatus", cascade="all, delete-orphan", back_populates="chamado")
    historicos_ticket: Mapped[list["HistoricoTicket"]] = relationship("HistoricoTicket", cascade="all, delete-orphan", back_populates="chamado")
    historicos_anexo: Mapped[list["HistoricoAnexo"]] = relationship("HistoricoAnexo", cascade="all, delete-orphan", back_populates="chamado")
