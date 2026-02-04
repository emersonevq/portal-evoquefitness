"""
Script para adicionar colunas de timestamp à tabela sla_pausas
"""

from sqlalchemy import text
from core.db import engine

def migrate_add_timestamps():
    """Adiciona colunas criado_em e atualizado_em à tabela sla_pausas"""
    
    with engine.begin() as conn:
        # Verificar se as colunas já existem
        try:
            conn.execute(text("DESCRIBE sla_pausas criado_em"))
            print("✓ Coluna 'criado_em' já existe em 'sla_pausas'")
        except:
            print("⚠️  Adicionando coluna 'criado_em' à tabela 'sla_pausas'...")
            conn.execute(text("""
                ALTER TABLE sla_pausas 
                ADD COLUMN criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            """))
            print("✅ Coluna 'criado_em' adicionada com sucesso")
        
        try:
            conn.execute(text("DESCRIBE sla_pausas atualizado_em"))
            print("✓ Coluna 'atualizado_em' já existe em 'sla_pausas'")
        except:
            print("⚠️  Adicionando coluna 'atualizado_em' à tabela 'sla_pausas'...")
            conn.execute(text("""
                ALTER TABLE sla_pausas 
                ADD COLUMN atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            """))
            print("✅ Coluna 'atualizado_em' adicionada com sucesso")

if __name__ == "__main__":
    migrate_add_timestamps()
    print("\n✅ Migração concluída com sucesso!")
