"""
Routes para gerenciar configurações de SLA.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ti.models import ConfiguracesSla
from ti.schemas.sla_configuracoes import (
    ConfiguracesSlaCreate,
    ConfiguracesSlaUpdate,
    ConfiguracesSlaResponse,
)
from core.db import get_db

router = APIRouter(prefix="/sla/configuracoes", tags=["SLA - Configurações"])

@router.get("/", response_model=list[ConfiguracesSlaResponse])
def listar_configuracoes(
    ativo: bool | None = Query(None),
    db: Session = Depends(get_db)
):
    """Lista todas as configurações de SLA"""
    query = db.query(ConfiguracesSla)
    
    if ativo is not None:
        query = query.filter(ConfiguracesSla.ativo == ativo)
    
    return query.all()

@router.get("/{config_id}", response_model=ConfiguracesSlaResponse)
def obter_configuracao(config_id: int, db: Session = Depends(get_db)):
    """Obtém uma configuração de SLA"""
    config = db.query(ConfiguracesSla).filter(
        ConfiguracesSla.id == config_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    return config

@router.post("/", response_model=ConfiguracesSlaResponse)
def criar_configuracao(
    dados: ConfiguracesSlaCreate,
    db: Session = Depends(get_db)
):
    """Cria uma nova configuração de SLA"""
    # Verifica se já existe configuração para esta prioridade
    existente = db.query(ConfiguracesSla).filter(
        ConfiguracesSla.prioridade == dados.prioridade
    ).first()
    
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"Configuração para prioridade '{dados.prioridade}' já existe"
        )
    
    config = ConfiguracesSla(**dados.dict())
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return config

@router.put("/{config_id}", response_model=ConfiguracesSlaResponse)
def atualizar_configuracao(
    config_id: int,
    dados: ConfiguracesSlaUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza uma configuração de SLA"""
    config = db.query(ConfiguracesSla).filter(
        ConfiguracesSla.id == config_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    # Atualiza apenas os campos fornecidos
    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(config, campo, valor)
    
    db.commit()
    db.refresh(config)
    
    return config

@router.delete("/{config_id}")
def deletar_configuracao(config_id: int, db: Session = Depends(get_db)):
    """Deleta uma configuração de SLA"""
    config = db.query(ConfiguracesSla).filter(
        ConfiguracesSla.id == config_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    db.delete(config)
    db.commit()
    
    return {"message": "Configuração deletada com sucesso"}
