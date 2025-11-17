"""
Script para sincronizar todos os chamados existentes com a tabela de histórico de SLA.
Este script deve ser executado uma vez para popular a tabela de SLA com dados históricos.

Uso:
    python -m ti.scripts.sync_chamados_sla
"""

from sqlalchemy.orm import Session
from core.db import SessionLocal, engine
from ti.models.chamado import Chamado
from ti.models.sla_config import HistoricoSLA
from ti.services.sla import SLACalculator
from core.utils import now_brazil_naive


def sync_chamados_to_sla(db: Session) -> dict:
    """
    Sincroniza todos os chamados com a tabela de histórico de SLA.
    
    Retorna:
        dict: Estatísticas da sincronização
    """
    try:
        HistoricoSLA.__table__.create(bind=engine, checkfirst=True)
    except Exception:
        pass

    stats = {
        "total_chamados": 0,
        "sincronizados": 0,
        "erros": 0,
        "detalhes": [],
    }

    try:
        chamados = db.query(Chamado).all()
        stats["total_chamados"] = len(chamados)

        for chamado in chamados:
            try:
                # Verifica se já existe histórico para este chamado
                existing = db.query(HistoricoSLA).filter(
                    HistoricoSLA.chamado_id == chamado.id
                ).first()

                if existing:
                    stats["detalhes"].append({
                        "chamado_id": chamado.id,
                        "status": "já_sincronizado",
                        "mensagem": f"Chamado {chamado.codigo} já possui histórico de SLA"
                    })
                    continue

                # Calcula o status de SLA atual
                sla_status = SLACalculator.get_sla_status(db, chamado)

                # Cria o registro histórico inicial
                historico = HistoricoSLA(
                    chamado_id=chamado.id,
                    usuario_id=None,
                    acao="sincronizacao_inicial",
                    status_anterior=None,
                    status_novo=chamado.status,
                    tempo_resolucao_horas=sla_status.get("tempo_resolucao_horas"),
                    limite_sla_horas=sla_status.get("tempo_resolucao_limite_horas"),
                    status_sla=sla_status.get("tempo_resolucao_status"),
                    criado_em=chamado.data_abertura or now_brazil_naive(),
                )
                db.add(historico)
                db.commit()

                stats["sincronizados"] += 1
                stats["detalhes"].append({
                    "chamado_id": chamado.id,
                    "codigo": chamado.codigo,
                    "status": "sincronizado",
                    "tempo_resolucao": sla_status.get("tempo_resolucao_horas"),
                })

            except Exception as e:
                stats["erros"] += 1
                stats["detalhes"].append({
                    "chamado_id": chamado.id,
                    "status": "erro",
                    "erro": str(e),
                })
                db.rollback()

        return stats

    except Exception as e:
        stats["erros"] += 1
        stats["detalhes"].append({
            "status": "erro_geral",
            "erro": str(e),
        })
        return stats


def main():
    """Executa a sincronização"""
    print("🔄 Iniciando sincronização de chamados com SLA...")
    print("-" * 60)

    db = SessionLocal()
    try:
        stats = sync_chamados_to_sla(db)

        print(f"✅ Sincronização concluída!")
        print(f"   Total de chamados: {stats['total_chamados']}")
        print(f"   Sincronizados: {stats['sincronizados']}")
        print(f"   Erros: {stats['erros']}")
        print("-" * 60)

        if stats["detalhes"]:
            print("\n📋 Detalhes da sincronização (primeiros 10):")
            for detalhe in stats["detalhes"][:10]:
                print(f"   • {detalhe}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
