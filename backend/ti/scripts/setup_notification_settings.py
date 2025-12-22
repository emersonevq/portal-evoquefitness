#!/usr/bin/env python3
"""
Script para criar a tabela notification_settings no banco de dados.
Pode ser executado via: python -m backend.ti.scripts.setup_notification_settings
"""

import sys
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from core.db import engine, Base, get_db
from backend.ti.models.notification_settings import NotificationSettings

def create_notification_settings_table():
    """
    Cria a tabela notification_settings se ela não existir.
    Também insere a configuração padrão.
    """
    try:
        print("=" * 60)
        print("Criando tabela notification_settings...")
        print("=" * 60)
        
        # Verificar se a tabela já existe
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'notification_settings' in tables:
            print("✓ Tabela 'notification_settings' já existe!")
        else:
            print("➜ Criando tabela 'notification_settings'...")
            # Criar a tabela usando o Base.metadata
            Base.metadata.create_all(bind=engine, tables=[NotificationSettings.__table__])
            print("✓ Tabela 'notification_settings' criada com sucesso!")
        
        # Inserir configuração padrão se não existir
        print("\n➜ Verificando configuração padrão...")
        db = next(get_db())
        
        existing_settings = db.query(NotificationSettings).first()
        if existing_settings:
            print(f"✓ Configuração padrão já existe (ID: {existing_settings.id})")
        else:
            print("➜ Inserindo configuração padrão...")
            default_settings = NotificationSettings()
            db.add(default_settings)
            db.commit()
            db.refresh(default_settings)
            print(f"✓ Configuração padrão inserida com sucesso (ID: {default_settings.id})")
        
        db.close()
        
        print("\n" + "=" * 60)
        print("✅ Setup completo! Tabela pronta para usar.")
        print("=" * 60)
        
        # Exibir informações
        print("\nEndpoints disponíveis:")
        print("  GET  /api/notification-settings          - Obter configurações")
        print("  PUT  /api/notification-settings          - Atualizar configurações")
        print("  POST /api/notification-settings/reset    - Resetar para padrão")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"\n✗ Erro de banco de dados: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_notification_settings_table()
    sys.exit(0 if success else 1)
