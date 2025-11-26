#!/usr/bin/env python3
"""
Script para criar as tabelas de cache de métricas para otimização de performance.

Executa:
- CREATE TABLE metrics_cache_db: Cache persistente para métricas calculadas
- CREATE TABLE sla_calculation_log: Log de execução de cálculos SLA
"""

import sys
from sqlalchemy import text
from core.db import engine

def create_tables():
    """Cria as tabelas de cache de métricas"""
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS metrics_cache_db (
            id INT PRIMARY KEY AUTO_INCREMENT,
            cache_key VARCHAR(100) UNIQUE NOT NULL,
            cache_value JSON NOT NULL,
            calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            INDEX idx_cache_key (cache_key),
            INDEX idx_expires_at (expires_at)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sla_calculation_log (
            id INT PRIMARY KEY AUTO_INCREMENT,
            calculation_type VARCHAR(50) NOT NULL,
            last_calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_calculated_chamado_id INT,
            chamados_count INT DEFAULT 0,
            execution_time_ms FLOAT DEFAULT 0,
            INDEX idx_calculation_type (calculation_type)
        )
        """
    ]

    try:
        with engine.connect() as connection:
            for sql_command in sql_commands:
                print(f"Executando: {sql_command.strip()[:80]}...")
                connection.execute(text(sql_command))
            connection.commit()
            print("✓ Tabelas de cache de métricas criadas com sucesso!")
            
    except Exception as e:
        print(f"✗ Erro ao criar tabelas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Criando tabelas de cache de métricas...")
    create_tables()
    print("Migração concluída!")
