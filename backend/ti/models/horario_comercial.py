from __future__ import annotations
from datetime import datetime, time
from sqlalchemy import Integer, String, DateTime, Boolean, Time
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base

class HorarioComercial(Base):
    __tablename__ = "horario_comercial"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Horário comercial principal
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)  # ex: 08:00
    hora_fim: Mapped[time] = mapped_column(Time, nullable=False)      # ex: 18:00
    
    # Dias da semana
    segunda: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    terca: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quarta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quinta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sexta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sabado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    domingo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Pausa de almoço (opcional)
    considera_almoco: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    almoco_inicio: Mapped[time | None] = mapped_column(Time, nullable=True)
    almoco_fim: Mapped[time | None] = mapped_column(Time, nullable=True)
    
    # Emergência (fora do horário comercial)
    emergencia_ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    emergencia_inicio: Mapped[time | None] = mapped_column(Time, nullable=True)
    emergencia_fim: Mapped[time | None] = mapped_column(Time, nullable=True)
    emergencia_dias_semana: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'seg,ter,qua,qui,sex,sab,dom'
    
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="America/Sao_Paulo")
    considera_feriados: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    padrao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_criacao: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usuario_atualizacao: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
