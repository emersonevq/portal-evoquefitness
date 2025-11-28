from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Text, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base

class Alert(Base):
    __tablename__ = "alert"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)  # info|warning|danger
    start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    media_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("media.id"), nullable=True)
    imagem_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    imagem_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.utcnow)
    usuario_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
