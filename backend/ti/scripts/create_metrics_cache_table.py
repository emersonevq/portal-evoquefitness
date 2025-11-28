from sqlalchemy import inspect
from ...core.db import engine
from ..models.metrics_cache import MetricsCacheDB

if __name__ == "__main__":
    insp = inspect(engine)
    table_name = MetricsCacheDB.__tablename__
    exists = insp.has_table(table_name)
    if not exists:
        MetricsCacheDB.__table__.create(bind=engine, checkfirst=True)
        print({"ok": True, "action": "created", "table": table_name})
    else:
        MetricsCacheDB.__table__.create(bind=engine, checkfirst=True)
        print({"ok": True, "action": "exists", "table": table_name})
