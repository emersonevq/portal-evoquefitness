"""
Script para criar a tabela sla_pausas no banco de dados.
Executado na inicialização da aplicação.
"""

from core.db import engine
from ti.models.sla_pausa import SLAPausa


def create_sla_pausa_table():
    """
    Cria a tabela sla_pausas se ela não existir.
    """
    try:
        SLAPausa.__table__.create(bind=engine, checkfirst=True)
        print("✅ Tabela sla_pausas criada ou já existe com sucesso")
    except Exception as e:
        print(f"⚠️  Erro ao criar tabela sla_pausas: {e}")
        raise


if __name__ == "__main__":
    create_sla_pausa_table()
