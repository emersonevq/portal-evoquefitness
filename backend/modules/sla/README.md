# Sistema de Gerenciamento de SLA

Sistema completo de Service Level Agreement para gerenciamento de chamados com cálculo automático de horas úteis, pausas e alertas.

## Características

✅ Cálculo automático de SLA em horas úteis  
✅ Suporte a feriados e horário comercial (08:00-18:00)  
✅ Pausa de SLA quando chamado está "Em análise"  
✅ Dashboard com métricas e alertas  
✅ Recálculo automático a cada 5 minutos  
✅ Cache de feriados e configurações  
✅ Persistência completa de pausas no banco de dados  
✅ Logs detalhados de todos os cálculos  

## Instalação

### 1. Backend

As dependências já foram adicionadas ao `requirements.txt`:
- apscheduler==3.10.4

As tabelas serão criadas automaticamente na inicialização da aplicação.

### 2. Frontend

Os componentes React já foram criados em `src/components/sla/`:
- `SlaDashboard.tsx` - Dashboard principal
- `SlaMetricsCard.tsx` - Card de métricas
- `SlaAlertsList.tsx` - Lista de alertas

## Configuração

### Horário Comercial

Edite em `modules/sla/config.py`:

```python
BUSINESS_HOUR_START: int = 8       # Hora de início (padrão: 8:00)
BUSINESS_HOUR_END: int = 18        # Hora de término (padrão: 18:00)
BUSINESS_DAYS: List[int] = [0, 1, 2, 3, 4]  # Dias úteis (seg-sex)
```

### SLA por Prioridade

As configurações padrão são criadas automaticamente:
- **Alta**: Resposta 2h, Resolução 8h
- **Média**: Resposta 4h, Resolução 24h
- **Baixa**: Resposta 8h, Resolução 48h

Para adicionar/modificar:

```bash
curl -X POST http://localhost:8000/api/sla/config \
  -H "Content-Type: application/json" \
  -d '{
    "prioridade": "critica",
    "tempo_resposta_horas": 1,
    "tempo_resolucao_horas": 4,
    "descricao": "Crítica"
  }'
```

### Feriados

Para adicionar feriados:

```bash
curl -X POST http://localhost:8000/api/sla/feriados \
  -H "Content-Type: application/json" \
  -d '{
    "data": "2024-12-25T00:00:00",
    "nome": "Natal",
    "descricao": "Feriado Nacional"
  }'
```

## Endpoints da API

### Dashboard

```
GET /api/sla/dashboard
GET /api/sla/dashboard/resumo
```

### Chamados

```
GET /api/sla/chamado/{id}
GET /api/sla/chamado/{id}/pausas
POST /api/sla/chamado/mudanca-status
```

**Exemplo - Registrar mudança de status:**

```bash
curl -X POST http://localhost:8000/api/sla/chamado/mudanca-status \
  -H "Content-Type: application/json" \
  -d '{
    "chamado_id": 123,
    "status_anterior": "aberto",
    "status_novo": "em_analise",
    "usuario_id": 1
  }'
```

### Configurações

```
GET /api/sla/config
POST /api/sla/config
PATCH /api/sla/config/{id}
DELETE /api/sla/config/{id}
```

### Feriados

```
GET /api/sla/feriados
POST /api/sla/feriados
DELETE /api/sla/feriados/{id}
```

### Scheduler

```
GET /api/sla/scheduler/status
POST /api/sla/scheduler/executar
POST /api/sla/scheduler/reset-falhas
```

### Cache

```
GET /api/sla/cache/status
POST /api/sla/cache/invalidar
```

## Status do Chamado e SLA

| Status | SLA |
|--------|-----|
| Aberto | ✅ Conta |
| Em andamento | ✅ Conta |
| Em análise | ⏸️ Pausado |
| Concluído | ⏹️ Finalizado |
| Cancelado | ⏹️ Finalizado |

## Integração com Frontend

### 1. Importar Componente

```tsx
import { SlaDashboard } from '@/components/sla';

export default function Page() {
  return <SlaDashboard />;
}
```

### 2. Usar Serviço

```tsx
import { slaService } from '@/services/slaService';

// Obter resumo
const metrics = await slaService.getDashboardResumo();

// Obter dashboard completo
const dashboard = await slaService.getDashboard();

// Obter SLA de um chamado específico
const slaStatus = await slaService.getSlaAlturaStatus(123);
```

### 3. Variáveis de Ambiente

Configure em `.env`:

```
VITE_API_URL=http://localhost:8000
```

## Estrutura de Pastas

```
backend/modules/sla/
├── __init__.py              # Exports
├── config.py                # Configurações
├── models.py                # Modelos SQLAlchemy
├── schemas.py               # Schemas Pydantic
├── calculator.py            # Cálculo de horas úteis
├── repository.py            # Acesso a dados
├── service.py               # Lógica de negócio
├── scheduler.py             # Scheduler APScheduler
├── router.py                # Endpoints FastAPI
├── cache.py                 # Cache em memória
├── constants.py             # Constantes e funções
├── exceptions.py            # Exceções customizadas
├── migrations.sql           # SQL para criação de tabelas
├── setup_sla_tables.py      # Setup das tabelas
└── README.md                # Este arquivo
```

## Logs

Os logs do SLA estão em `sla.scheduler` e `sla.service`. Configure em sua aplicação:

```python
import logging

logging.getLogger('sla.scheduler').setLevel(logging.INFO)
logging.getLogger('sla.service').setLevel(logging.INFO)
```

## Troubleshooting

### Scheduler não está rodando

```bash
# Verificar status
curl http://localhost:8000/api/sla/scheduler/status

# Reset de falhas
curl -X POST http://localhost:8000/api/sla/scheduler/reset-falhas
```

### Cache desatualizado

```bash
# Invalidar cache
curl -X POST http://localhost:8000/api/sla/cache/invalidar
```

### Recalcular manualmente

```bash
# Executar recálculo imediato
curl -X POST http://localhost:8000/api/sla/scheduler/executar
```

## Performance

- Cache de 60 minutos para feriados e configurações
- Índices de banco de dados para busca rápida
- Pool de conexões configurado para concorrência
- Recálculo assíncrono a cada 5 minutos

## Desenvolvimento

### Rodar Testes

```bash
cd code/backend
python -m pytest modules/sla/ -v
```

### Verificar Migrations

```bash
# Backup do banco antes de rodar
mysqldump -u user -p database > backup.sql

# Executar migrations
mysql -u user -p database < modules/sla/migrations.sql
```

## Contato & Suporte

Para problemas ou sugestões, abra uma issue no repositório.
