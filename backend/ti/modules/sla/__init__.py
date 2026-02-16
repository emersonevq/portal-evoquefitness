"""
Módulo de SLA (Service Level Agreement) para gerenciamento de chamados.

Este módulo implementa um sistema completo de rastreamento e cálculo de SLA
com suporte a:
- Cálculo de tempo útil (respeitando horário comercial, feriados, pausas)
- Monitoramento em tempo real
- Histórico de mudanças
- Notificações automáticas
- Escalonamento automático
- Métricas e relatórios
"""

from fastapi import APIRouter

# Importar routers quando disponível
# from .routes import router as sla_router

__all__ = [
    # "sla_router",
]
