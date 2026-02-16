"""
Router principal do módulo SLA.

Agrupa todos os sub-routers do sistema de SLA.
"""

from fastapi import APIRouter
from ti.modules.sla.routes import (
    configuracoes,
    pausas,
    horario,
    feriados,
    dashboard,
)

router = APIRouter(prefix="/api/sla", tags=["SLA"])

# Inclui todos os sub-routers
router.include_router(configuracoes.router)
router.include_router(pausas.router)
router.include_router(horario.router)
router.include_router(feriados.router)
router.include_router(dashboard.router)

__all__ = ["router"]
