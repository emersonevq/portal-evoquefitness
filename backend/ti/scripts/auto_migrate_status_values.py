"""
Automatic migration of ticket status values on application startup.

This script automatically runs when the backend starts to:
- Update "Cancelado" -> "Expirado"
- Update "Em análise" -> "Aguardando"
- Update "Em andamento" -> "Em atendimento"
- Mark retroactive tickets (before 01.01.2026) as "Expirado"

No manual intervention required.
"""

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def auto_migrate_status_values():
    """Automatically migrate status values on startup"""
    
    try:
        from core.db import SQLALCHEMY_DATABASE_URL
        from ti.models.chamado import Chamado
        
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("\n[MIGRATION] 🔄 Starting automatic status migration...")
        
        try:
            # Update "Cancelado" -> "Expirado"
            cancelado_count = session.query(Chamado).filter(Chamado.status == "Cancelado").count()
            if cancelado_count > 0:
                session.query(Chamado).filter(Chamado.status == "Cancelado").update(
                    {Chamado.status: "Expirado"},
                    synchronize_session=False
                )
                print(f"[MIGRATION] ✓ Updated {cancelado_count} 'Cancelado' tickets to 'Expirado'")
            
            # Update "Em análise" -> "Aguardando"
            analise_count = session.query(Chamado).filter(Chamado.status == "Em análise").count()
            if analise_count > 0:
                session.query(Chamado).filter(Chamado.status == "Em análise").update(
                    {Chamado.status: "Aguardando"},
                    synchronize_session=False
                )
                print(f"[MIGRATION] ✓ Updated {analise_count} 'Em análise' tickets to 'Aguardando'")

            # Update "Em andamento" -> "Em atendimento"
            andamento_count = session.query(Chamado).filter(Chamado.status == "Em andamento").count()
            if andamento_count > 0:
                session.query(Chamado).filter(Chamado.status == "Em andamento").update(
                    {Chamado.status: "Em atendimento"},
                    synchronize_session=False
                )
                print(f"[MIGRATION] ✓ Updated {andamento_count} 'Em andamento' tickets to 'Em atendimento'")

            # Mark retroactive tickets (before 01.01.2026) as Expirado
            sla_start_date = datetime(2026, 1, 1, 0, 0, 0)
            retroativo_count = session.query(Chamado).filter(
                Chamado.data_abertura < sla_start_date,
                Chamado.status != "Expirado"
            ).count()
            if retroativo_count > 0:
                session.query(Chamado).filter(
                    Chamado.data_abertura < sla_start_date,
                    Chamado.status != "Expirado"
                ).update(
                    {Chamado.status: "Expirado"},
                    synchronize_session=False
                )
                print(f"[MIGRATION] ✓ Updated {retroativo_count} retroactive tickets (before 01.01.2026) to 'Expirado'")

            session.commit()
            print("[MIGRATION] ✅ Automatic status migration completed successfully!\n")
            
        except Exception as e:
            session.rollback()
            print(f"[MIGRATION] ⚠️  Migration completed with some warnings: {e}")
        finally:
            session.close()
        
    except Exception as e:
        print(f"[MIGRATION] ⚠️  Could not perform automatic migration: {e}")
        # Non-blocking: application continues even if migration fails
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    auto_migrate_status_values()
