"""
Sistema de Atualização Incremental de SLA

Comportamento:
1. Na inicialização: Calcula SLA de TODOS os chamados uma só vez
2. Preenche cache completo
3. Quando um chamado muda de status: Recalcula SÓ aquele chamado
4. Atualiza cache incrementalmente

Uso:
    # Na startup
    from ti.services.sla_incremental_updater import init_sla_system
    init_sla_system()
    
    # Quando chamado muda de status (em endpoint de atualização)
    from ti.services.sla_incremental_updater import recalculate_chamado_sla
    recalculate_chamado_sla(db, chamado_id)
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from core.db import SessionLocal
from core.utils import now_brazil_naive
from ti.services.sla_cache import SLACacheManager
from ti.scripts.recalculate_sla_complete import SLARecalculator
from ti.services.sla import SLACalculator
from ti.models.chamado import Chamado

logger = logging.getLogger(__name__)


def init_sla_system():
    """
    Inicializa o sistema de SLA na startup.
    
    Calcula SLA de TODOS os chamados uma só vez e preenche o cache.
    Depois, o sistema só recalculará quando um chamado for modificado.
    """
    db = SessionLocal()
    try:
        logger.info("=" * 80)
        logger.info("🚀 INICIALIZANDO SISTEMA DE SLA")
        logger.info("=" * 80)
        logger.info("📊 Calculando SLA de TODOS os chamados (uma única vez)...")
        
        # Recalcula todos uma só vez
        recalculator = SLARecalculator(db)
        stats = recalculator.recalculate_all(verbose=False)
        
        # Log dos resultados
        logger.info(f"✅ SLA Inicial Calculado:")
        logger.info(f"   - Total de chamados: {stats['total_chamados']}")
        logger.info(f"   - Recalculados: {stats['recalculados']}")
        logger.info(f"   - Com erro: {stats['com_erro']}")
        logger.info(f"   - Tempo médio resposta: {stats['tempo_medio_resposta_horas']:.2f}h")
        logger.info(f"   - Tempo médio resolução: {stats['tempo_medio_resolucao_horas']:.2f}h")
        
        # Aquece o cache
        _warmup_cache(db)
        
        db.commit()
        
        logger.info("=" * 80)
        logger.info("✅ SISTEMA DE SLA INICIALIZADO")
        logger.info("=" * 80)
        logger.info("📌 Modo de Operação:")
        logger.info("   - Cache: PREENCHIDO (todos os chamados calculados)")
        logger.info("   - Atualizações: INCREMENTAIS (apenas quando status muda)")
        logger.info("   - Recálculo: SÓ para chamados modificados")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar sistema de SLA: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def recalculate_chamado_sla(db: Session, chamado_id: int):
    """
    Recalcula SLA de um chamado específico (quando seu status muda).
    
    Uso:
        # Em um endpoint de atualização de chamado
        @router.put("/chamados/{chamado_id}/status")
        def atualizar_status(chamado_id: int, novo_status: str, db: Session = Depends(get_db)):
            chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
            chamado.status = novo_status
            db.add(chamado)
            db.flush()
            
            # Recalcula SLA deste chamado
            recalculate_chamado_sla(db, chamado_id)
            
            db.commit()
            return chamado
    """
    try:
        # Busca o chamado
        chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
        
        if not chamado:
            logger.warning(f"⚠️  Chamado {chamado_id} não encontrado")
            return
        
        logger.debug(f"🔄 Recalculando SLA do chamado {chamado.codigo} (ID: {chamado_id})...")
        
        # Calcula o SLA deste chamado
        sla_status = SLACalculator.get_sla_status(db, chamado)
        
        # Log
        resposta_metric = sla_status.get("resposta_metric")
        resolucao_metric = sla_status.get("resolucao_metric")
        
        tempo_resposta = resposta_metric.get("tempo_decorrido_horas") if resposta_metric else 0
        tempo_resolucao = resolucao_metric.get("tempo_decorrido_horas") if resolucao_metric else 0
        
        logger.debug(
            f"✅ SLA Recalculado: "
            f"Resposta={tempo_resposta:.2f}h, "
            f"Resolução={tempo_resolucao:.2f}h, "
            f"Status={sla_status.get('status_geral')}"
        )
        
        # Invalida cache de métricas (forçar recalcular na próxima requisição)
        # Isso garante que o dashboard sempre mostre dados corretos
        SLACacheManager.invalidate_all_sla(db)
        
        logger.debug(f"✅ Cache invalidado para chamado {chamado_id}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao recalcular SLA do chamado {chamado_id}: {e}", exc_info=True)


def _warmup_cache(db: Session):
    """Pré-aquece o cache com as métricas principais"""
    try:
        from ti.services.metrics import MetricsCalculator
        
        logger.debug("🔥 Aquecendo cache com métricas principais...")
        
        # Calcula e cacheia as métricas principais
        MetricsCalculator.get_sla_compliance_24h(db)
        MetricsCalculator.get_sla_compliance_mes(db)
        MetricsCalculator.get_sla_distribution(db)
        MetricsCalculator.get_tempo_medio_resposta_24h(db)
        MetricsCalculator.get_tempo_medio_resposta_mes(db)
        
        logger.debug("✅ Cache aquecido com sucesso")
    except Exception as e:
        logger.warning(f"⚠️  Erro ao aquecer cache: {e}", exc_info=True)
