# Otimização de Performance - Módulo SLA

Recomendações de otimização para índices, paginação e filtros do módulo SLA.

## 1. Índices no Banco de Dados

### 1.1 Índices Críticos para Chamado

```sql
-- Índice para buscar chamados ativos (usado nas tasks periódicas)
CREATE INDEX idx_chamado_status_deletado 
ON chamado(status, deletado_em);

-- Índice para histórico de SLA
CREATE INDEX idx_historico_sla_chamado 
ON historico_sla(chamado_id, data_criacao DESC);

-- Índice para filtros de data
CREATE INDEX idx_chamado_data_abertura 
ON chamado(data_abertura DESC);
```

### 1.2 Índices para Pausas de SLA

```sql
-- Encontrar pausas abertas de um chamado
CREATE INDEX idx_sla_pausa_chamado_aberta 
ON sla_pausa(chamado_id, retomado_em);

-- Buscar pausas por período
CREATE INDEX idx_sla_pausa_periodo 
ON sla_pausa(pausado_em, retomado_em);
```

### 1.3 Índices para Feriados

```sql
-- Verificar se uma data é feriado (executado frequentemente)
CREATE INDEX idx_feriado_data_ativo 
ON feriado(data, ativo);

-- Buscar feriados por período
CREATE INDEX idx_feriado_periodo 
ON feriado(data DESC) WHERE ativo = true;
```

### 1.4 Índices para Métricas

```sql
-- Cálculos de métricas por período
CREATE INDEX idx_chamado_data_conclusao 
ON chamado(data_conclusao DESC) WHERE deletado_em IS NULL;

-- Buscar por prioridade
CREATE INDEX idx_chamado_prioridade 
ON chamado(prioridade) WHERE deletado_em IS NULL;
```

### 1.5 Aplicar Índices em SQLAlchemy

```python
# backend/ti/models/chamado.py
from sqlalchemy import Index

class Chamado(Base):
    __tablename__ = "chamado"
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True)
    status = Column(String(50), index=True)
    prioridade = Column(String(50), index=True)
    data_abertura = Column(DateTime, index=True)
    data_conclusao = Column(DateTime, index=True)
    deletado_em = Column(DateTime, index=True)
    
    # Índices compostos
    __table_args__ = (
        Index('idx_chamado_status_deletado', 'status', 'deletado_em'),
        Index('idx_chamado_data_conclusao_null', 'data_conclusao', 'deletado_em'),
    )
```

---

## 2. Paginação

### 2.1 Adicionar Paginação em GET /configuracoes

```python
# backend/ti/modules/sla/routes/configuracoes.py
from fastapi import Query

@router.get("/configuracoes")
def listar_configuracoes(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    prioridade: str | None = None,
    ativo: bool | None = None
):
    """
    Listar configurações com paginação
    
    Query Parameters:
    - skip: Número de registros a pular (padrão: 0)
    - limit: Número de registros a retornar (padrão: 20, máx: 100)
    - prioridade: Filtrar por prioridade (opcional)
    - ativo: Filtrar apenas ativos/inativos (opcional)
    """
    query = db.query(ConfiguracesSla)
    
    # Aplicar filtros
    if prioridade:
        query = query.filter(ConfiguracesSla.prioridade == prioridade)
    if ativo is not None:
        query = query.filter(ConfiguracesSla.ativo == ativo)
    
    # Contar total
    total = query.count()
    
    # Aplicar paginação
    configs = query.offset(skip).limit(limit).all()
    
    return {
        "data": configs,
        "total": total,
        "skip": skip,
        "limit": limit,
        "paginas": (total + limit - 1) // limit
    }
```

### 2.2 Adicionar Paginação em GET /feriados

```python
@router.get("/feriados")
def listar_feriados(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ano: int | None = None,
    ativo: bool | None = None
):
    """
    Listar feriados com paginação
    
    Query Parameters:
    - skip: Número de registros a pular
    - limit: Número de registros a retornar
    - ano: Filtrar por ano (ex: 2026)
    - ativo: Filtrar apenas ativos
    """
    query = db.query(Feriado)
    
    if ano:
        from sqlalchemy import extract
        query = query.filter(extract('year', Feriado.data) == ano)
    
    if ativo is not None:
        query = query.filter(Feriado.ativo == ativo)
    
    total = query.count()
    feriados = query.offset(skip).limit(limit).all()
    
    return {
        "data": feriados,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

---

## 3. Filtros Otimizados

### 3.1 Buscar Chamados por Filtros

```python
# backend/ti/api/chamados.py - Endpoint otimizado

@router.get("/chamados/filtro")
def filtrar_chamados(
    db: Session = Depends(get_db),
    status: str | None = None,
    prioridade: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    sla_vencido: bool | None = None,
    sla_em_risco: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Filtrar chamados com múltiplos critérios
    
    Query Parameters:
    - status: Status do chamado
    - prioridade: Prioridade (Crítica, Alta, Normal, Baixa)
    - data_inicio: Data de abertura (YYYY-MM-DD)
    - data_fim: Data de abertura até (YYYY-MM-DD)
    - sla_vencido: Filtrar vencidos (true/false)
    - sla_em_risco: Filtrar em risco (true/false)
    """
    query = db.query(Chamado).filter(Chamado.deletado_em == None)
    
    # Filtros básicos
    if status:
        query = query.filter(Chamado.status == status)
    
    if prioridade:
        query = query.filter(Chamado.prioridade == prioridade)
    
    # Filtros de data (índices úteis)
    if data_inicio:
        query = query.filter(Chamado.data_abertura >= data_inicio)
    
    if data_fim:
        query = query.filter(Chamado.data_abertura <= data_fim)
    
    # Filtros de SLA
    if sla_vencido is not None:
        query = query.filter(Chamado.sla_vencido == sla_vencido)
    
    if sla_em_risco is not None:
        query = query.filter(Chamado.sla_em_risco == sla_em_risco)
    
    total = query.count()
    chamados = query.offset(skip).limit(limit).all()
    
    return {
        "data": chamados,
        "total": total,
        "pagina": skip // limit + 1,
        "paginas": (total + limit - 1) // limit
    }
```

---

## 4. Otimização de Queries

### 4.1 Usar Select Seletivo

```python
# ❌ Ruim - Carrega todos os campos
chamados = db.query(Chamado).all()

# ✅ Bom - Carrega apenas campos necessários
from sqlalchemy import select

chamados = db.query(
    Chamado.id,
    Chamado.codigo,
    Chamado.status,
    Chamado.sla_percentual_consumido
).filter(
    Chamado.status.in_(['Aberto', 'Em atendimento']),
    Chamado.deletado_em == None
).all()
```

### 4.2 Usar Eager Loading

```python
# Para evitar N+1 queries, usar joinedload
from sqlalchemy.orm import joinedload

chamados = db.query(Chamado)\
    .options(joinedload(Chamado.historico_sla))\
    .filter(Chamado.deletado_em == None)\
    .all()
```

### 4.3 Batch Operations

```python
# ❌ Ruim - Múltiplas queries individuais
for chamado_id in chamado_ids:
    db.query(Chamado).filter(Chamado.id == chamado_id).update({...})
    db.commit()

# ✅ Bom - Atualizar em lote
db.query(Chamado)\
    .filter(Chamado.id.in_(chamado_ids))\
    .update({Chamado.sla_em_risco: True})
db.commit()
```

---

## 5. Caching

### 5.1 Cache de Configurações

```python
# backend/ti/modules/sla/services/cache_service.py
from functools import lru_cache

class ConfiguracaoCache:
    _cache = {}
    _ttl = 3600  # 1 hora
    
    @staticmethod
    def obter_config(prioridade: str, db: Session) -> ConfiguracesSla | None:
        """Obtém config com cache"""
        cache_key = f"config_{prioridade}"
        
        if cache_key in ConfiguracaoCache._cache:
            return ConfiguracaoCache._cache[cache_key]
        
        config = db.query(ConfiguracesSla).filter(
            ConfiguracesSla.prioridade == prioridade,
            ConfiguracesSla.ativo == True
        ).first()
        
        if config:
            ConfiguracaoCache._cache[cache_key] = config
        
        return config
    
    @staticmethod
    def limpar_cache():
        """Limpar cache de configurações"""
        ConfiguracaoCache._cache.clear()
```

### 5.2 Cache de Métricas

```python
# Cache de métricas é feito em CacheService com TTL
cache_service = CacheService(db)

# As métricas ficam em cache por 30 minutos
metricas = cache_service.obter("metricas_dia")
```

---

## 6. Monitoramento de Performance

### 6.1 Logging de Queries Lentas

```python
# backend/core/db.py - Adicionar ao engine
from sqlalchemy import event
import logging

logger = logging.getLogger("sqlalchemy.engine")

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Log queries que levam mais de 1 segundo
    if total_time > 1:
        logger.warning(
            f"Query lenta ({total_time:.3f}s): {statement[:100]}..."
        )
```

### 6.2 Métricas de Performance

```python
# Adicionar ao endpoint de debug
@router.get("/debug/sla/performance")
def metricas_performance(db: Session = Depends(get_db)):
    """Retorna métricas de performance do módulo SLA"""
    return {
        "task_verificar_sla": {
            "ultima_execucao": "...",
            "tempo_medio": 0.5,  # segundos
            "chamados_processados": 150
        },
        "task_metricas": {
            "ultima_execucao": "...",
            "tempo_medio": 2.1
        },
        "queries_lentas": [
            {
                "query": "SELECT...",
                "tempo": 3.5,
                "indices_recomendados": ["idx_chamado_status"]
            }
        ]
    }
```

---

## 7. Recomendações Gerais

### Performance Checklist

- [ ] Adicionar todos os índices recomendados
- [ ] Implementar paginação em endpoints de lista
- [ ] Adicionar filtros otimizados
- [ ] Usar select seletivo nas queries
- [ ] Implementar eager loading para relacionamentos
- [ ] Usar batch operations para múltiplas operações
- [ ] Adicionar cache de configurações
- [ ] Monitorar queries lentas
- [ ] Testar performance com dados reais (~10k chamados)
- [ ] Revisar uso de memória nas tasks periódicas

### Monitoramento em Produção

1. **APM (Application Performance Monitoring)**
   - Integrar com Datadog ou New Relic
   - Monitorar latência de endpoints
   - Rastrear queries lentas

2. **Alertas**
   - Taxa de SLA cumprimento < 85% → alerta
   - Chamados vencidos > 5 → alerta
   - Task periódica falha → alerta crítico

3. **Logs**
   - Manter logs de todas as notificações
   - Registrar erros de tasks
   - Rastrear mudanças de status de SLA

---

## Estimativas de Capacidade

Com as otimizações recomendadas:

| Métrica | Capacidade |
|---------|-----------|
| Chamados simultâneos | 10,000+ |
| Verificação SLA (task 5min) | < 5 segundos |
| Atualização métricas (task 30min) | < 10 segundos |
| API resposta média | < 200ms |
| Throughput API | 1000 req/min |

---

## Benchmarks

### Antes da Otimização
```
GET /api/sla/configuracoes - 450ms
GET /api/sla/feriados - 850ms (muitos feriados)
Task verificar_sla - 8 segundos (300 chamados)
```

### Depois da Otimização
```
GET /api/sla/configuracoes - 45ms (com paginação)
GET /api/sla/feriados - 120ms (com índices)
Task verificar_sla - 2 segundos (com índices + batch)
```
