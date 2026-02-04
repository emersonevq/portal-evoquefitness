# Sistema de Gerenciamento de SLA

Sistema completo de Service Level Agreement (SLA) para gerenciamento de chamados com cálculo automático de horas úteis, pausas e alertas.

## Características

✅ Cálculo automático de SLA em horas úteis  
✅ Suporte a feriados e horário comercial (08:00-18:00)  
✅ Pausa de SLA quando chamado está "Em análise"  
✅ Dashboard com métricas e alertas  
✅ Recálculo automático a cada 5 minutos  
✅ Cache de feriados e configurações  
✅ Persistência completa de pausas no banco de dados  
✅ Logs detalhados de todos os cálculos

## Status do Chamado e SLA

| Status       | SLA           |
| ------------ | ------------- |
| Aberto       | ✅ Conta      |
| Em andamento | ✅ Conta      |
| Em análise   | ⏸️ Pausado    |
| Concluído    | ⏹️ Finalizado |
| Cancelado    | ⏹️ Finalizado |

## Instalação

### 1. Backend

As tabelas serão criadas automaticamente na inicialização da aplicação.

### 2. Frontend

Os componentes React já foram criados em `src/components/sla/`:

- `SlaDashboard.tsx` - Dashboard principal
- `src/services/slaService.ts` - Serviço para API
- `src/hooks/useSLA.ts` - Hooks para state management

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
├── setup_sla_tables.py      # Setup das tabelas
└── README.md                # Este arquivo
```

## API Endpoints

### Dashboard

```
GET /api/sla/dashboard
GET /api/sla/dashboard/resumo
```

### Configurações

```
GET /api/sla/config
POST /api/sla/config
```

### Feriados

```
GET /api/sla/feriados
POST /api/sla/feriados
DELETE /api/sla/feriados/{id}
```

### Chamados

```
GET /api/sla/chamado/{id}
```

### Scheduler

```
GET /api/sla/scheduler/status
POST /api/sla/scheduler/executar
```

### Cache

```
GET /api/sla/cache/status
POST /api/sla/cache/invalidar
```

## Uso Frontend

### Importar Componente

```tsx
import SlaDashboard from "@/components/sla/SlaDashboard";

export default function Page() {
  return <SlaDashboard />;
}
```

### Usar Service

```tsx
import { slaService } from "@/services/slaService";

// Obter resumo
const metrics = await slaService.getDashboardResumo();

// Obter dashboard completo
const dashboard = await slaService.getDashboard();

// Obter SLA de um chamado específico
const slaStatus = await slaService.getSlaAlturaStatus(123);
```

### Usar Hooks

```tsx
import { useSLADashboard, useSLAChamado } from "@/hooks/useSLA";

export function MyComponent() {
  const { dashboard, isLoading, error } = useSLADashboard();
  const { slaStatus, formatTempo } = useSLAChamado(123);

  return (
    <div>
      <p>
        Tempo resposta: {formatTempo(slaStatus?.tempo_decorrido_horas || 0)}
      </p>
    </div>
  );
}
```

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

### Adicionar Feriados

```bash
curl -X POST http://localhost:3001/api/sla/feriados \
  -H "Content-Type: application/json" \
  -d '{
    "data": "2024-12-25T00:00:00",
    "nome": "Natal",
    "descricao": "Feriado Nacional"
  }'
```

## Cálculo de SLA

### Algoritmo

1. **Horas Úteis**: Apenas seg-sex, 8h-18h, excluindo feriados
2. **Pausas**: Deduzidas quando chamado está "Em análise"
3. **Status**:
   - OK: Dentro do limite
   - Em Risco: 80% do limite consumido
   - Vencido: 100% do limite consumido

### Exemplo

- Chamado aberto: segunda 16h
- Limite resposta: 2 horas (SLA alta)
- Tempo útil até terça 10h = 2 horas
- Status: ✅ Dentro do SLA

## WebSocket Events

O módulo emite eventos em tempo real:

```javascript
socket.on("sla:updated", () => {
  // Dashboard foi atualizado
  // Refetch dos dados
});
```

## Performance

- Cache de 60 minutos para feriados e configurações
- Índices de banco de dados para busca rápida
- Pool de conexões configurado para concorrência
- Recálculo assíncrono a cada 5 minutos

## Logs

Os logs estão em `sla.scheduler`, `sla.service` e `sla.calculator`:

```python
import logging
logging.getLogger('sla.scheduler').setLevel(logging.INFO)
logging.getLogger('sla.service').setLevel(logging.INFO)
logging.getLogger('sla.calculator').setLevel(logging.DEBUG)
```

## Troubleshooting

### Scheduler não está rodando

```bash
curl http://localhost:3001/api/sla/scheduler/status
```

### Cache desatualizado

```bash
curl -X POST http://localhost:3001/api/sla/cache/invalidar
```

### Recalcular manualmente

```bash
curl -X POST http://localhost:3001/api/sla/scheduler/executar
```

## Contato & Suporte

Para problemas ou sugestões, abra uma issue no repositório.
