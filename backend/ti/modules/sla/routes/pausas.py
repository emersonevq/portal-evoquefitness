"""
Routes para gerenciar pausas de SLA.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ti.models import SlaPausa
from ti.schemas.sla_pausas import SlaPausaResponse, SlaPausaListResponse
from ti.modules.sla.services import PausaService
from core.db import get_db

router = APIRouter(prefix="/sla/pausas", tags=["SLA - Pausas"])

@router.get("/chamado/{chamado_id}", response_model=SlaPausaListResponse)
def listar_pausas_chamado(chamado_id: int, db: Session = Depends(get_db)):
    """Lista pausas de um chamado"""
    pausas = db.query(SlaPausa).filter(SlaPausa.chamado_id == chamado_id).all()
    
    resultado = []
    for pausa in pausas:
        resultado.append({
            "id": pausa.id,
            "chamado_id": pausa.chamado_id,
            "pausado_em": pausa.pausado_em,
            "retomado_em": pausa.retomado_em,
            "motivo": pausa.motivo,
            "duracao_minutos": pausa.duracao_minutos,
            "ativa": pausa.retomado_em is None
        })
    
    return SlaPausaListResponse(items=resultado)

@router.post("/{pausa_id}/retomar")
def retomar_pausa(pausa_id: int, db: Session = Depends(get_db)):
    """Retoma uma pausa de SLA"""
    pausa_service = PausaService(db)
    
    pausa = db.query(SlaPausa).filter(SlaPausa.id == pausa_id).first()
    if not pausa:
        raise HTTPException(status_code=404, detail="Pausa não encontrada")
    
    if pausa.retomado_em:
        raise HTTPException(status_code=400, detail="Pausa já foi retomada")
    
    pausa_retomada = pausa_service.retomar_pausa(pausa_id)
    
    return {
        "id": pausa_retomada.id,
        "duracao_minutos": pausa_retomada.duracao_minutos,
        "retomado_em": pausa_retomada.retomado_em
    }
