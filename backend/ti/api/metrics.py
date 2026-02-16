from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.db import get_db
from core.utils import now_brazil_naive

# Metrics router - properly configured with /metrics prefix
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/health")
def metrics_health_check(db: Session = Depends(get_db)):
    """
    Endpoint de health check para monitorar saúde do sistema.

    Retorna:
    - banco_status: Se conexão com banco está OK
    - timestamp: Momento do check
    """
    try:
        health = {
            "status": "healthy",
            "checks": {}
        }

        # Check: Database connection
        try:
            db.execute("SELECT 1")
            health["checks"]["database"] = {
                "status": "ok",
                "message": "Database connected"
            }
        except Exception as db_error:
            health["checks"]["database"] = {
                "status": "critical",
                "message": str(db_error)
            }
            health["status"] = "unhealthy"

        health["timestamp"] = now_brazil_naive().isoformat()
        return health

    except Exception as e:
        print(f"Erro ao fazer health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": now_brazil_naive().isoformat()
        }
