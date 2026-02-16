# Documentação da API REST de SLA

Sistema integrado de gerenciamento de SLA (Service Level Agreement) para Portal Evoque.

## Visão Geral

O módulo SLA gerencia prazos de atendimento e resolução de chamados, com:
- Cálculo automático de tempo útil respeitando horário comercial e feriados
- Monitoramento contínuo de risco e vencimento
- Notificações em tempo real
- Métricas e relatórios

## Base URL

```
http://localhost:3001/api
```

## Autenticação

Todas as requisições requerem token JWT no header:

```bash
Authorization: Bearer <token>
```

---

## 1. Configurações de SLA

### 1.1 Listar Configurações

```http
GET /api/sla/configuracoes
```

**Resposta (200 OK):**
```json
[
  {
    "id": 1,
    "prioridade": "Crítica",
    "tempo_primeira_resposta": 1,
    "tempo_resolucao": 4,
    "considera_horario_comercial": true,
    "considera_feriados": true,
    "escalar_automaticamente": true,
    "notificar_em_risco": true,
    "percentual_risco": 75,
    "ativo": true,
    "criado_em": "2026-01-15T10:30:00Z"
  }
]
```

### 1.2 Obter Configuração Específica

```http
GET /api/sla/configuracoes/{id}
```

**Parâmetros:**
- `id` (integer, path) - ID da configuração

**Resposta (200 OK):**
```json
{
  "id": 1,
  "prioridade": "Crítica",
  "tempo_primeira_resposta": 1,
  "tempo_resolucao": 4,
  ...
}
```

**Erros:**
- `404 Not Found` - Configuração não encontrada

### 1.3 Criar Configuração

```http
POST /api/sla/configuracoes
```

**Body:**
```json
{
  "prioridade": "Alta",
  "tempo_primeira_resposta": 2,
  "tempo_resolucao": 8,
  "considera_horario_comercial": true,
  "considera_feriados": true,
  "escalar_automaticamente": true,
  "notificar_em_risco": true,
  "percentual_risco": 75,
  "ativo": true
}
```

**Resposta (201 Created):**
```json
{
  "id": 2,
  "prioridade": "Alta",
  "tempo_primeira_resposta": 2,
  "tempo_resolucao": 8,
  ...
}
```

**Erros:**
- `400 Bad Request` - Dados inválidos
- `409 Conflict` - Prioridade já existe

### 1.4 Atualizar Configuração

```http
PUT /api/sla/configuracoes/{id}
```

**Parâmetros:**
- `id` (integer, path) - ID da configuração

**Body (parcial):**
```json
{
  "tempo_primeira_resposta": 3,
  "tempo_resolucao": 12
}
```

**Resposta (200 OK):**
```json
{
  "id": 1,
  "prioridade": "Crítica",
  "tempo_primeira_resposta": 3,
  "tempo_resolucao": 12,
  ...
}
```

### 1.5 Deletar Configuração

```http
DELETE /api/sla/configuracoes/{id}
```

**Resposta (204 No Content)**

---

## 2. Pausas de SLA

### 2.1 Listar Pausas de um Chamado

```http
GET /api/sla/pausas/chamado/{chamado_id}
```

**Parâmetros:**
- `chamado_id` (integer, path) - ID do chamado

**Resposta (200 OK):**
```json
[
  {
    "id": 1,
    "chamado_id": 123,
    "pausado_em": "2026-01-15T14:30:00Z",
    "retomado_em": "2026-01-15T16:30:00Z",
    "duracao_minutos": 120,
    "motivo": "Aguardando cliente"
  }
]
```

### 2.2 Retomar Pausa

```http
POST /api/sla/pausas/{pausa_id}/retomar
```

**Parâmetros:**
- `pausa_id` (integer, path) - ID da pausa

**Resposta (200 OK):**
```json
{
  "id": 1,
  "chamado_id": 123,
  "pausado_em": "2026-01-15T14:30:00Z",
  "retomado_em": "2026-01-15T16:30:00Z",
  "duracao_minutos": 120
}
```

---

## 3. Horários Comerciais

### 3.1 Listar Horários

```http
GET /api/sla/horarios
```

**Resposta (200 OK):**
```json
[
  {
    "id": 1,
    "nome": "Comercial Padrão",
    "descricao": "Das 08h às 18h, segunda a sexta",
    "hora_inicio": "08:00:00",
    "hora_fim": "18:00:00",
    "segunda": true,
    "terca": true,
    "quarta": true,
    "quinta": true,
    "sexta": true,
    "sabado": false,
    "domingo": false,
    "timezone": "America/Sao_Paulo",
    "ativo": true,
    "padrao": true
  }
]
```

### 3.2 Criar Horário

```http
POST /api/sla/horarios
```

**Body:**
```json
{
  "nome": "Horário Estendido",
  "descricao": "Das 06h às 22h",
  "hora_inicio": "06:00:00",
  "hora_fim": "22:00:00",
  "segunda": true,
  "terca": true,
  "quarta": true,
  "quinta": true,
  "sexta": true,
  "sabado": true,
  "domingo": false,
  "timezone": "America/Sao_Paulo",
  "ativo": true,
  "padrao": false
}
```

**Resposta (201 Created):**
```json
{
  "id": 2,
  "nome": "Horário Estendido",
  ...
}
```

---

## 4. Feriados

### 4.1 Listar Feriados

```http
GET /api/sla/feriados
```

**Query Parameters:**
- `ativo` (boolean, optional) - Filtrar apenas feriados ativos
- `ano` (integer, optional) - Filtrar por ano

**Resposta (200 OK):**
```json
[
  {
    "id": 1,
    "data": "2026-01-01",
    "nome": "Ano Novo",
    "tipo": "fixo",
    "descricao": "Feriado Nacional - Ano Novo",
    "ativo": true
  },
  {
    "id": 2,
    "data": "2026-04-03",
    "nome": "Sexta-feira Santa",
    "tipo": "movel",
    "descricao": "Feriado Móvel - Sexta-feira Santa",
    "ativo": true
  }
]
```

### 4.2 Criar Feriado

```http
POST /api/sla/feriados
```

**Body:**
```json
{
  "data": "2026-11-20",
  "nome": "Consciência Negra",
  "tipo": "fixo",
  "descricao": "Feriado Nacional - Dia da Consciência Negra",
  "ativo": true
}
```

**Resposta (201 Created):**
```json
{
  "id": 3,
  "data": "2026-11-20",
  "nome": "Consciência Negra",
  ...
}
```

### 4.3 Verificar se Data é Feriado

```http
GET /api/sla/feriados/verificar/{data}
```

**Parâmetros:**
- `data` (string, path) - Data no formato YYYY-MM-DD

**Resposta (200 OK):**
```json
{
  "data": "2026-12-25",
  "eh_feriado": true,
  "feriado": {
    "id": 8,
    "nome": "Natal",
    "tipo": "fixo",
    "descricao": "Feriado Nacional - Natal"
  }
}
```

---

## 5. Dashboard e Indicadores

### 5.1 Indicadores em Tempo Real

```http
GET /api/sla/dashboard/indicadores
```

**Resposta (200 OK):**
```json
{
  "abertos": 15,
  "em_atendimento": 8,
  "em_risco": 3,
  "vencidos": 1,
  "concluidos_hoje": 12,
  "taxa_cumprimento": 91.5
}
```

### 5.2 Métricas por Período

```http
GET /api/sla/dashboard/metricas
```

**Query Parameters:**
- `periodo` (string, optional) - "dia", "semana", "mês" (padrão: "dia")

**Resposta (200 OK):**
```json
{
  "periodo": "dia",
  "data": "2026-01-15",
  "metricas": {
    "total_chamados": 20,
    "concluidos": 18,
    "dentro_sla": 17,
    "taxa_cumprimento": 85.0,
    "tempo_medio_resposta": 2.5,
    "tempo_medio_resolucao": 12.8
  },
  "por_prioridade": {
    "Crítica": {
      "total": 2,
      "dentro_sla": 2,
      "taxa": 100
    },
    "Alta": {
      "total": 5,
      "dentro_sla": 5,
      "taxa": 100
    },
    "Normal": {
      "total": 10,
      "dentro_sla": 8,
      "taxa": 80
    },
    "Baixa": {
      "total": 3,
      "dentro_sla": 2,
      "taxa": 66.7
    }
  }
}
```

### 5.3 Relatório Diário

```http
GET /api/sla/dashboard/relatorio-diario
```

**Resposta (200 OK):**
```json
{
  "data": "2026-01-15",
  "resumo_executivo": {
    "total_chamados": 20,
    "concluidos": 18,
    "taxa_cumprimento": 85.0,
    "criticos": 0
  },
  "indicadores": {
    "abertos": 2,
    "em_atendimento": 8,
    "em_risco": 3,
    "vencidos": 1
  },
  "top_prioridades_pendentes": [
    {
      "prioridade": "Crítica",
      "quantidade": 2,
      "percentual": 10
    },
    {
      "prioridade": "Alta",
      "quantidade": 5,
      "percentual": 25
    }
  ]
}
```

---

## Exemplos de Uso com cURL

### Criar Configuração

```bash
curl -X POST http://localhost:3001/api/sla/configuracoes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prioridade": "Alta",
    "tempo_primeira_resposta": 2,
    "tempo_resolucao": 8,
    "considera_horario_comercial": true,
    "considera_feriados": true,
    "escalar_automaticamente": true,
    "notificar_em_risco": true,
    "percentual_risco": 75,
    "ativo": true
  }'
```

### Obter Indicadores

```bash
curl -X GET http://localhost:3001/api/sla/dashboard/indicadores \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Verificar Feriado

```bash
curl -X GET "http://localhost:3001/api/sla/feriados/verificar/2026-12-25" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## WebSocket Events (Socket.IO)

Eventos emitidos pelo servidor em tempo real:

### Evento: SLA em Risco

```javascript
socket.on("sla:em_risco", (data) => {
  console.log(`Chamado ${data.codigo} em risco`);
  console.log(`Consumido: ${data.percentual}%`);
});
```

**Payload:**
```json
{
  "chamado_id": 123,
  "codigo": "TST-001",
  "percentual": 78.5,
  "prioridade": "Alta",
  "timestamp": "2026-01-15T14:30:00Z"
}
```

### Evento: SLA Vencido

```javascript
socket.on("sla:vencido", (data) => {
  console.log(`CRÍTICO: Chamado ${data.codigo} com SLA vencido`);
});
```

### Evento: Chamado Concluído

```javascript
socket.on("sla:concluido", (data) => {
  console.log(`Chamado ${data.codigo} concluído`);
  console.log(`Status: ${data.status}`); // "dentro" ou "fora"
});
```

---

## Códigos de Erro

| Código | Mensagem | Descrição |
|--------|----------|-----------|
| 400 | Bad Request | Dados inválidos na requisição |
| 401 | Unauthorized | Token ausente ou inválido |
| 403 | Forbidden | Sem permissão para acessar recurso |
| 404 | Not Found | Recurso não encontrado |
| 409 | Conflict | Prioridade/feriado já existe |
| 422 | Unprocessable Entity | Erro de validação |
| 500 | Internal Server Error | Erro no servidor |

---

## Fluxo Completo de SLA

### 1. Configuração Inicial

1. **POST** `/api/sla/configuracoes` - Criar configurações de SLA
2. **POST** `/api/sla/horarios` - Criar horário comercial
3. **POST** `/api/sla/feriados` - Inserir feriados

### 2. Criar Chamado

Ao criar um chamado, o SLA é automaticamente inicializado (se houver configuração):
- Calcula limite de primeira resposta
- Calcula limite de resolução
- Registra no histórico

### 3. Monitoramento Contínuo

A cada 5 minutos, task periódica:
- Atualiza tempo decorrido
- Marca como "em risco" (≥75%)
- Marca como "vencido" (≥100%)
- Escalona automaticamente se configurado

### 4. Notificações

Quando SLA entra em risco ou vence:
- **Email** ao responsável
- **WebSocket** notificação em tempo real
- **Banco de dados** registro da notificação

### 5. Conclusão

Ao concluir o chamado:
- Calcula tempo total de resolução
- Desconta pausas
- Registra resultado (dentro/fora)
- Envia notificação de conclusão

---

## Rate Limiting

Não há rate limit implementado atualmente, mas recomenda-se:
- Máximo 100 requisições por minuto por usuário
- Cache de resultados por 1-5 minutos

---

## Roadmap Futuro

- [ ] Suporte a múltiplos horários comerciais por departamento
- [ ] Escalonamento automático em cascata
- [ ] Relatórios PDF com gráficos
- [ ] Integração com Slack/Teams
- [ ] SLA por categoria de problema
- [ ] Análise de tendências
- [ ] Alertas customizáveis por usuário
- [ ] Export de dados para BI

---

## Suporte

Para dúvidas ou problemas com a API de SLA, contacte:
- Email: support@evoque.com.br
- Documentação: /docs/SLA_API.md
