from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from io import BytesIO
from datetime import datetime
import base64
import json
from core.db import get_db, engine

try:
    from ti.models.alert import Alert, AlertView
    from ti.schemas.alert import AlertOut, AlertCreate, AlertUpdate
except ImportError:
    from ..models.alert import Alert, AlertView
    from ..schemas.alert import AlertOut, AlertCreate, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["TI - Alerts"])


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None)
) -> List[Dict[str, Any]]:
    """
    Lista todos os alertas do sistema, opcionalmente filtrando por módulos do usuário
    Se user_id for fornecido, marca quais alertas o usuário já viu
    """
    try:
        Alert.__table__.create(bind=engine, checkfirst=True)
        AlertView.__table__.create(bind=engine, checkfirst=True)
    except Exception:
        pass

    try:
        alerts = db.query(Alert).filter(Alert.ativo == True).order_by(Alert.created_at.desc()).all()
        
        # Buscar views do usuário se user_id for fornecido
        user_views = set()
        if user_id:
            views = db.query(AlertView.alert_id).filter(AlertView.user_id == user_id).all()
            user_views = {v[0] for v in views}

        result = []
        for alert in alerts:
            alert_dict = {
                "id": alert.id,
                "title": alert.title or "",
                "message": alert.message or "",
                "description": alert.description or "",
                "severity": alert.severity or "low",
                "pages": alert.pages or [],
                "show_on_home": alert.show_on_home or False,
                "created_by": alert.created_by,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
                "ativo": alert.ativo,
                "viewed": alert.id in user_views,
                "imagem_mime_type": alert.imagem_mime_type,
                "imagem_blob": None
            }

            if alert.imagem_blob:
                try:
                    alert_dict["imagem_blob"] = base64.b64encode(alert.imagem_blob).decode('utf-8')
                except Exception as e:
                    print(f"[ALERTS] Erro ao converter imagem para base64: {e}")
                    alert_dict["imagem_blob"] = None

            result.append(alert_dict)

        return result

    except Exception as e:
        print(f"[ALERTS] Erro ao listar alertas: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao listar alertas: {str(e)}")


@router.post("")
async def create_alert(
    title: str = Form(...),
    message: str = Form(""),
    description: Optional[str] = Form(None),
    severity: str = Form("low"),
    pages_json: Optional[str] = Form(None),
    show_on_home: bool = Form(False),
    imagem: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None)
) -> Dict[str, Any]:
    """
    Cria um novo alerta com suporte a múltiplos módulos/páginas e opção home
    """
    try:
        print(f"[ALERTS] Criando alerta: {title}")

        valid_severities = ["low", "medium", "high", "critical"]
        if severity not in valid_severities:
            severity = "low"

        # Parsear páginas
        pages = []
        if pages_json:
            try:
                pages = json.loads(pages_json) if isinstance(pages_json, str) else pages_json
                if not isinstance(pages, list):
                    pages = []
            except Exception as e:
                print(f"[ALERTS] Erro ao parsear páginas: {e}")
                pages = []

        # Processar imagem se fornecida
        imagem_blob = None
        imagem_mime_type = None

        if imagem:
            try:
                print(f"[ALERTS] Processando imagem: {imagem.filename}")
                imagem_blob = await imagem.read()
                imagem_mime_type = imagem.content_type or "image/jpeg"
                print(f"[ALERTS] Imagem processada: {len(imagem_blob)} bytes")
            except Exception as e:
                print(f"[ALERTS] Erro ao processar imagem: {e}")
                imagem_blob = None
                imagem_mime_type = None

        # Criar alerta
        new_alert = Alert(
            title=title,
            message=message or "",
            description=description,
            severity=severity,
            pages=pages,
            show_on_home=show_on_home,
            created_by=user_id,
            imagem_blob=imagem_blob,
            imagem_mime_type=imagem_mime_type,
            ativo=True
        )

        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)

        print(f"[ALERTS] Alerta criado com sucesso! ID: {new_alert.id}")

        response = {
            "id": new_alert.id,
            "title": new_alert.title,
            "message": new_alert.message,
            "description": new_alert.description,
            "severity": new_alert.severity,
            "pages": new_alert.pages or [],
            "show_on_home": new_alert.show_on_home,
            "created_by": new_alert.created_by,
            "created_at": new_alert.created_at.isoformat() if new_alert.created_at else None,
            "updated_at": new_alert.updated_at.isoformat() if new_alert.updated_at else None,
            "ativo": new_alert.ativo,
            "viewed": False,
            "imagem_mime_type": new_alert.imagem_mime_type,
            "imagem_blob": None
        }

        if new_alert.imagem_blob:
            try:
                response["imagem_blob"] = base64.b64encode(new_alert.imagem_blob).decode('utf-8')
            except:
                response["imagem_blob"] = None

        return response

    except Exception as e:
        db.rollback()
        print(f"[ALERTS] ERRO ao criar alerta: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao criar alerta: {str(e)}")


@router.put("/{alert_id}")
async def update_alert(
    alert_id: int,
    title: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    severity: Optional[str] = Form(None),
    pages_json: Optional[str] = Form(None),
    show_on_home: Optional[bool] = Form(None),
    ativo: Optional[bool] = Form(None),
    imagem: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Atualiza um alerta existente
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()

        if not alert:
            raise HTTPException(status_code=404, detail="Alerta não encontrado")

        if title is not None:
            alert.title = title
        if message is not None:
            alert.message = message
        if description is not None:
            alert.description = description
        if severity is not None and severity in ["low", "medium", "high", "critical"]:
            alert.severity = severity
        if pages_json is not None:
            try:
                alert.pages = json.loads(pages_json) if isinstance(pages_json, str) else pages_json
            except Exception:
                pass
        if show_on_home is not None:
            alert.show_on_home = show_on_home
        if ativo is not None:
            alert.ativo = ativo

        if imagem:
            try:
                alert.imagem_blob = await imagem.read()
                alert.imagem_mime_type = imagem.content_type or "image/jpeg"
            except Exception as e:
                print(f"[ALERTS] Erro ao processar imagem: {e}")

        db.commit()
        db.refresh(alert)

        response = {
            "id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "description": alert.description,
            "severity": alert.severity,
            "pages": alert.pages or [],
            "show_on_home": alert.show_on_home,
            "created_by": alert.created_by,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
            "ativo": alert.ativo,
            "imagem_mime_type": alert.imagem_mime_type,
            "imagem_blob": None
        }

        if alert.imagem_blob:
            try:
                response["imagem_blob"] = base64.b64encode(alert.imagem_blob).decode('utf-8')
            except:
                response["imagem_blob"] = None

        return response

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ALERTS] Erro ao atualizar alerta: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar alerta: {str(e)}")


@router.post("/{alert_id}/view")
def mark_alert_as_viewed(
    alert_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Marca um alerta como visto pelo usuário
    Impede que o alerta seja mostrado novamente para este usuário
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alerta não encontrado")

        # Verificar se já foi visto
        existing_view = db.query(AlertView).filter(
            AlertView.alert_id == alert_id,
            AlertView.user_id == user_id
        ).first()

        if not existing_view:
            view = AlertView(alert_id=alert_id, user_id=user_id)
            db.add(view)
            db.commit()
            print(f"[ALERTS] Usuário {user_id} marcou alerta {alert_id} como visto")

        return {"ok": True, "message": "Alerta marcado como visto"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ALERTS] Erro ao marcar alerta como visto: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao marcar como visto: {str(e)}")


@router.get("/{alert_id}/imagem")
def get_alert_image(alert_id: int, db: Session = Depends(get_db)):
    """
    Retorna a imagem de um alerta específico
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()

        if not alert:
            raise HTTPException(status_code=404, detail="Alerta não encontrado")

        if not alert.imagem_blob:
            raise HTTPException(status_code=404, detail="Este alerta não possui imagem")

        mime_type = alert.imagem_mime_type or "image/jpeg"

        return StreamingResponse(
            BytesIO(alert.imagem_blob),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename=alerta_{alert_id}.jpg",
                "Cache-Control": "public, max-age=3600"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ALERTS] Erro ao buscar imagem: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar imagem: {str(e)}")


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Remove um alerta do sistema (soft delete)
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()

        if not alert:
            raise HTTPException(status_code=404, detail="Alerta não encontrado")

        print(f"[ALERTS] Removendo alerta ID: {alert_id}")

        alert.ativo = False
        db.commit()

        print(f"[ALERTS] Alerta {alert_id} removido com sucesso")

        return {"ok": True, "message": f"Alerta {alert_id} removido com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ALERTS] Erro ao remover alerta: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao remover alerta: {str(e)}")
