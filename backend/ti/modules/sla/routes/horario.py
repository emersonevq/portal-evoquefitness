"""
Routes para gerenciar horários comerciais.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ti.models import HorarioComercial
from ti.schemas.sla_horario import (
    HorarioComercialCreate,
    HorarioComercialUpdate,
    HorarioComercialResponse,
)
from core.db import get_db

router = APIRouter(prefix="/sla/horarios", tags=["SLA - Horários Comerciais"])

@router.get("/", response_model=list[HorarioComercialResponse])
def listar_horarios(
    ativo: bool | None = Query(None),
    padrao: bool | None = Query(None),
    db: Session = Depends(get_db)
):
    """Lista horários comerciais"""
    query = db.query(HorarioComercial)
    
    if ativo is not None:
        query = query.filter(HorarioComercial.ativo == ativo)
    
    if padrao is not None:
        query = query.filter(HorarioComercial.padrao == padrao)
    
    return query.all()

@router.get("/{horario_id}", response_model=HorarioComercialResponse)
def obter_horario(horario_id: int, db: Session = Depends(get_db)):
    """Obtém um horário comercial"""
    horario = db.query(HorarioComercial).filter(
        HorarioComercial.id == horario_id
    ).first()
    
    if not horario:
        raise HTTPException(status_code=404, detail="Horário não encontrado")
    
    return horario

@router.post("/", response_model=HorarioComercialResponse)
def criar_horario(
    dados: HorarioComercialCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo horário comercial"""
    horario = HorarioComercial(**dados.dict())
    db.add(horario)
    db.commit()
    db.refresh(horario)
    
    return horario

@router.put("/{horario_id}", response_model=HorarioComercialResponse)
def atualizar_horario(
    horario_id: int,
    dados: HorarioComercialUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza um horário comercial"""
    horario = db.query(HorarioComercial).filter(
        HorarioComercial.id == horario_id
    ).first()
    
    if not horario:
        raise HTTPException(status_code=404, detail="Horário não encontrado")
    
    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(horario, campo, valor)
    
    db.commit()
    db.refresh(horario)
    
    return horario

@router.delete("/{horario_id}")
def deletar_horario(horario_id: int, db: Session = Depends(get_db)):
    """Deleta um horário comercial"""
    horario = db.query(HorarioComercial).filter(
        HorarioComercial.id == horario_id
    ).first()
    
    if not horario:
        raise HTTPException(status_code=404, detail="Horário não encontrado")
    
    db.delete(horario)
    db.commit()
    
    return {"message": "Horário deletado com sucesso"}
