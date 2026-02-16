"""
Routes para gerenciar feriados.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from sqlalchemy.orm import Session
from ti.models import Feriado
from ti.schemas.sla_feriados import (
    FeriadoCreate,
    FeriadoUpdate,
    FeriadoResponse,
)
from core.db import get_db

router = APIRouter(prefix="/sla/feriados", tags=["SLA - Feriados"])

@router.get("/", response_model=list[FeriadoResponse])
def listar_feriados(
    ativo: bool | None = Query(None),
    tipo: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """Lista feriados"""
    query = db.query(Feriado)
    
    if ativo is not None:
        query = query.filter(Feriado.ativo == ativo)
    
    if tipo:
        query = query.filter(Feriado.tipo == tipo)
    
    return query.all()

@router.get("/{feriado_id}", response_model=FeriadoResponse)
def obter_feriado(feriado_id: int, db: Session = Depends(get_db)):
    """Obtém um feriado"""
    feriado = db.query(Feriado).filter(Feriado.id == feriado_id).first()
    
    if not feriado:
        raise HTTPException(status_code=404, detail="Feriado não encontrado")
    
    return feriado

@router.post("/", response_model=FeriadoResponse)
def criar_feriado(
    dados: FeriadoCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo feriado"""
    # Verifica se já existe feriado nesta data
    existente = db.query(Feriado).filter(Feriado.data == dados.data).first()
    
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"Já existe feriado em {dados.data}"
        )
    
    feriado = Feriado(**dados.dict())
    db.add(feriado)
    db.commit()
    db.refresh(feriado)
    
    return feriado

@router.put("/{feriado_id}", response_model=FeriadoResponse)
def atualizar_feriado(
    feriado_id: int,
    dados: FeriadoUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza um feriado"""
    feriado = db.query(Feriado).filter(Feriado.id == feriado_id).first()
    
    if not feriado:
        raise HTTPException(status_code=404, detail="Feriado não encontrado")
    
    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(feriado, campo, valor)
    
    db.commit()
    db.refresh(feriado)
    
    return feriado

@router.delete("/{feriado_id}")
def deletar_feriado(feriado_id: int, db: Session = Depends(get_db)):
    """Deleta um feriado"""
    feriado = db.query(Feriado).filter(Feriado.id == feriado_id).first()
    
    if not feriado:
        raise HTTPException(status_code=404, detail="Feriado não encontrado")
    
    db.delete(feriado)
    db.commit()
    
    return {"message": "Feriado deletado com sucesso"}

@router.get("/verificar/{data_str}")
def verificar_feriado(data_str: str, db: Session = Depends(get_db)):
    """Verifica se uma data é feriado"""
    try:
        data = date.fromisoformat(data_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida")
    
    feriado = db.query(Feriado).filter(
        Feriado.data == data,
        Feriado.ativo == True
    ).first()
    
    return {"data": data, "eh_feriado": feriado is not None, "feriado": feriado}
