"""Script para criar tabelas SLA no banco de dados"""

from sqlalchemy.orm import Session
from core.db import engine, SessionLocal
from .models import SlaConfiguration, SlaFeriado, SlaBusinessHours, SlaCalculationLog, SlaPausa
import logging

logger = logging.getLogger(__name__)


def create_sla_tables():
    """Cria as tabelas do módulo SLA"""
    try:
        # Criar todas as tabelas
        SlaConfiguration.__table__.create(bind=engine, checkfirst=True)
        SlaFeriado.__table__.create(bind=engine, checkfirst=True)
        SlaBusinessHours.__table__.create(bind=engine, checkfirst=True)
        SlaCalculationLog.__table__.create(bind=engine, checkfirst=True)
        SlaPausa.__table__.create(bind=engine, checkfirst=True)
        
        logger.info("[SLA] Tabelas criadas/verificadas com sucesso")
        
        # Inserir configurações padrão se não existirem
        db = SessionLocal()
        try:
            config_count = db.query(SlaConfiguration).count()
            if config_count == 0:
                db.add(SlaConfiguration(
                    prioridade="alta",
                    tempo_resposta_horas=2,
                    tempo_resolucao_horas=8,
                    descricao="Prioridade alta - resposta em 2h, resolução em 8h",
                    ativo=True
                ))
                db.add(SlaConfiguration(
                    prioridade="media",
                    tempo_resposta_horas=4,
                    tempo_resolucao_horas=24,
                    descricao="Prioridade média - resposta em 4h, resolução em 24h",
                    ativo=True
                ))
                db.add(SlaConfiguration(
                    prioridade="baixa",
                    tempo_resposta_horas=8,
                    tempo_resolucao_horas=48,
                    descricao="Prioridade baixa - resposta em 8h, resolução em 48h",
                    ativo=True
                ))
                db.commit()
                logger.info("[SLA] Configurações padrão criadas")
        finally:
            db.close()
        
        return True
    except Exception as e:
        logger.error(f"[SLA] Erro ao criar tabelas: {e}")
        return False
