# 📋 Implementação: Filtro de 30 Dias para SLA

## Problema Original
- Muitos chamados abertos com >30 dias estavam distorcendo o cálculo de SLA
- O tempo médio de resposta e resolução ficava muito longo
- Necessidade de considerar apenas chamados recentes nas métricas de SLA

## Solução Implementada

### 1. **Filtro de 30 Dias nas Métricas Agregadas** ✅
**Arquivo modificado:** `backend/ti/services/sla_metrics_unified.py`

#### Mudanças:
- Adicionada constante `SLA_AGE_LIMIT_DAYS = 30`
- Modificado método `calculate_sla_distribution_period()` para filtrar apenas chamados com ≤30 dias
- Método `get_sla_compliance_24h()` já tinha o filtro (mantido como está)

#### Impacto:
- **Dashboard/Resumo de SLA** agora mostra métricas apenas de chamados recentes (≤30 dias)
- **Chamados com >30 dias** não contam para:
  - Percentual de SLA (resposta e resolução)
  - Tempo médio de resposta
  - Tempo médio de resolução
  - Listagem de chamados em risco/vencidos

#### Nota Importante:
- Cada chamado AINDA TEM seu SLA calculado individualmente
- O filtro é apenas para as **MÉTRICAS AGREGADAS** (dashboard, resumo)
- Chamados antigos continuam recebendo suporte/acompanhamento

### 2. **Lógica de Pausa de SLA** ✅ (Já existente, validada)
**Status:** Implementado e funcionando
**Arquivo:** `backend/ti/services/sla.py`

#### Como funciona:
```
Status "Em análise" ou "Aguardando" → ⏸️ SLA PAUSA
Qualquer outro status → ▶️ SLA RETOMA
```

#### Detalhes técnicos:
- Quando status muda para "Em análise" ou "Aguardando":
  - Uma pausa SLA é criada automaticamente (`SLAPausa`)
  - O tempo PARA de contar
  
- Quando status sai de "Em análise" ou "Aguardando":
  - A pausa é finalizada
  - O tempo VOLTA a contar

- Método `calculate_business_hours_excluding_paused()` desconta automaticamente o tempo pausado

### 3. **Recálculo de SLAs** ✅

#### Opção 1: Usar endpoint existente
```bash
POST /api/sla/recalcular/painel
```
- Recalcula todos os SLAs automaticamente
- Usa a nova lógica com filtro de 30 dias
- Invalida caches automaticamente

#### Opção 2: Executar script de migração (desenvolvimento/testes)
```bash
cd /app
python backend/scripts/recalculate_sla_with_30day_filter.py
```

Outputs:
- Validação de código
- Contagem de chamados por intervalo de idade
- Recálculo de métricas de SLA
- Invalidação de caches

#### Opção 3: Executar testes de validação
```bash
cd /app
python backend/scripts/test_sla_30day_filter.py
```

Testes incluem:
1. Validação do filtro de 30 dias
2. Validação da lógica de pausa
3. Validação do cálculo de status de SLA

## Comportamento Esperado

### Cenário 1: Chamado com 15 dias de idade
```
- Contado nas métricas de SLA ✅
- Contado no percentual de compliance
- Contado no tempo médio de resposta
```

### Cenário 2: Chamado com 45 dias de idade
```
- NÃO contado nas métricas agregadas de SLA ❌
- Mas ainda tem seu próprio SLA calculado individualmente
- Não aparece no dashboard de resumo
```

### Cenário 3: Chamado em "Em análise"
```
- SLA está PAUSADO ⏸️
- Tempo não corre enquanto espera análise
- Quando sai de "Em análise", SLA retoma automaticamente ▶️
```

## Métricas Afetadas

### Dashboard/Resumo de SLA agora mostra:
- ✅ Percentual de SLA de resposta (apenas chamados ≤30d)
- ✅ Percentual de SLA de resolução (apenas chamados ≤30d)
- ✅ Tempo médio de resposta (apenas chamados ≤30d)
- ✅ Tempo médio de resolução (apenas chamados ≤30d)
- ✅ Chamados em risco (apenas chamados ≤30d)
- ✅ Chamados vencidos (apenas chamados ≤30d)
- ✅ Chamados pausados (apenas chamados ≤30d)

### Não são afetados:
- ❌ Cálculo individual de SLA por chamado (continua igual)
- ❌ Histórico de SLA (registra tudo normalmente)
- ❌ Resposta/resolução individual de um chamado

## Testes Executados

### ✅ Teste 1: Filtro de 30 Dias
- Valida que apenas chamados ≤30 dias são contados nas métricas
- Verifica que chamados >30 dias são excluídos

### ✅ Teste 2: Lógica de Pausa
- Valida que pausa é criada ao mudar para "Em análise"
- Valida que pausa é finalizada ao sair de "Em análise"

### ✅ Teste 3: Cálculo de SLA
- Valida que o status de SLA é calculado corretamente
- Verifica resposta e resolução métricas

## Como Usar em Produção

### Passo 1: Deploy do código
```bash
# As mudanças já estão no código
# Fazer deploy normalmente
```

### Passo 2: Recalcular SLAs
```bash
# Via UI (recomendado)
POST http://seu-dominio/api/sla/recalcular/painel

# Via script (se necessário)
python backend/scripts/recalculate_sla_with_30day_filter.py
```

### Passo 3: Validar resultados
```bash
# Verificar se as métricas fizeram sentido
# Observar se o SLA médio ficou mais saudável
# Confirmar que chamados antigos não aparecem mais no dashboard
```

## Rollback (se necessário)

Se precisar reverter:
1. Remover o filtro de 30 dias em `sla_metrics_unified.py`
2. Remover as 2 linhas adicionadas:
   ```python
   agora = now_brazil_naive()
   data_limite_30d = agora - timedelta(days=self.SLA_AGE_LIMIT_DAYS)
   ```
3. Remover o filtro da query:
   ```python
   Chamado.data_abertura >= data_limite_30d,  # ← REMOVER
   ```
4. Recalcular SLAs novamente

## Performance

### Impacto esperado:
- ✅ Queries MAIS RÁPIDAS (menos chamados para processar)
- ✅ Cálculos MAIS RÁPIDOS (menos linhas nas métricas)
- ✅ Dashboard MAIS RESPONSIVO
- ✅ Sem impacto em chamados antigos (continuam recebendo suporte)

## Próximos Passos Opcionais

1. **Limpeza de dados históricos** (opcional)
   - Arquivar chamados muito antigos para melhorar performance

2. **Automação de recálculos**
   - Configurar scheduler para recalcular SLA periodicamente

3. **Alertas inteligentes**
   - Notificar quando um chamado dentro de 30 dias se aproxima do vencimento

4. **Análise de SLA histórico**
   - Manter histórico de SLA antes/depois da mudança

---

## Resumo Executivo

| Métrica | Antes | Depois |
|---------|-------|--------|
| Chamados contados | TODOS | ≤30 dias |
| Tempo médio de resposta | ⬆️ Muito alto | ⬇️ Mais realista |
| Percentual de SLA | ❌ Baixo | ✅ Mais justo |
| Experiência de usuário | Métricas deprimente | Motivadora |

**Status: PRONTO PARA PRODUÇÃO** ✅

Todas as alterações foram testadas e validadas. O sistema está pronto para uso em produção.
