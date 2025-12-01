# Documentação Completa do Sistema SLA

## Sumário
1. [Conceitos Básicos](#conceitos-básicos)
2. [Configurações do SLA](#configurações-do-sla)
3. [Como é Calculado o SLA](#como-é-calculado-o-sla)
4. [Regras de Negócio](#regras-de-negócio)
5. [Cálculo de P90](#cálculo-de-p90)
6. [Cache e Reset](#cache-e-reset)
7. [Métricas e Relatórios](#métricas-e-relatórios)
8. [Troubleshooting](#troubleshooting)

---

## Conceitos Básicos

### O que é SLA?
**SLA (Service Level Agreement)** é um contrato que define o tempo máximo para responder e resolver chamados de suporte.

No sistema TI, temos:
- **Tempo de Resposta**: quanto tempo leva para dar a primeira resposta a um chamado
- **Tempo de Resolução**: quanto tempo leva para fechar/resolver um chamado

### Prioridades e SLAs Padrão

| Prioridade | Tempo de Resposta | Tempo de Resolução |
|------------|-------------------|-------------------|
| Crítica    | 1 hora            | 4 horas           |
| Urgente    | 2 horas           | 8 horas           |
| Alta       | 4 horas           | 24 horas          |
| Normal     | 8 horas           | 48 horas          |

> Esses valores são padrão, mas podem ser ajustados via API.

---

## Configurações do SLA

### 1. Horário de Funcionamento (Business Hours)
Por padrão: **Segunda a Sexta, 08:00 às 18:00**

**Importante**: Apenas as horas de funcionamento contam para cálculos de SLA. Por exemplo:
- Uma chamada aberta à sexta 17:00 e respondida à segunda 09:00 conta apenas 1 hora (sexta: 1h + segunda: 1h)

### 2. Férias e Dias Não Úteis
O sistema reconhece:
- **Feriados brasileiros** (automaticamente configurados)
- **Férias personalizadas** (podem ser adicionadas via API)
- **Dias sem expediente** (sábados, domingos)

Esses dias NÃO contam para o cálculo de SLA.

### 3. Horas de Negócio por Dia (Configurável)
É possível configurar horários diferentes para cada dia da semana:
- Segunda: 08:00-18:00
- Terça: 08:00-18:00
- ... etc ...

---

## Como é Calculado o SLA

### Fórmula Geral

```
Tempo de SLA Decorrido = Horas de Negócio Utilizadas
```

### Exemplo Prático

**Chamado aberto**: sexta-feira, 16:00
**Chamado respondido**: segunda-feira, 10:00
**SLA Configurado**: 4 horas

```
Sexta-feira: 16:00 → 18:00 = 2 horas
Sábado: nenhum (fim de semana)
Domingo: nenhum (fim de semana)
Segunda-feira: 08:00 → 10:00 = 2 horas

Total: 4 horas
Status: ✅ DENTRO DO SLA (4h = 4h)
```

### Tempo de Resposta

**O que conta**: da abertura do chamado até a primeira mudança de status (resposta).

Fórmula:
```
Tempo Resposta = BusinessHours(data_abertura, data_primeira_resposta)
```

**O que NÃO conta**:
- Finais de semana
- Fora do horário comercial
- Períodos em que o chamado estava "Em Análise" (pausado)

### Tempo de Resolução

**O que conta**: da abertura do chamado até o fechamento (Concluído ou Cancelado).

Fórmula:
```
Tempo Resolução = BusinessHours(data_abertura, data_conclusao)
                  - Períodos_Em_Análise
```

**Períodos em Análise (descontados)**:
Quando um chamado tem status "Em Análise" ou "Aguardando Cliente", o tempo não conta.

Exemplo:
```
Abertura: segunda 09:00
Status Aguardando: segunda 11:00 → terça 09:00 (24h = 1 dia inteiro não conta)
Reabertura: terça 09:00
Conclusão: terça 11:00

Tempo Total = 2h (segunda) + 2h (terça) = 4h
(O período "Aguardando" de 24h é completamente descontado)
```

---

## Regras de Negócio

### 1. Quando um Chamado É Considerado no SLA?

**✅ Incluído nos cálculos:**
- Status: Concluído, Cancelado, Aberto, Em Progresso, Aguardando
- Tem data de abertura definida
- Tem primeira resposta ou está ativo
- Não foi deletado
- Data de abertura está dentro do período analisado

**❌ Excluído dos cálculos:**
- Chamados deletados
- Status: Sem status
- Sem data de abertura
- Data de abertura anterior ao último reset do SLA

### 2. Estados do SLA

Um chamado pode estar em um desses estados:

| Estado | Condição | Observação |
|--------|----------|-----------|
| **DENTRO DO PRAZO** | Tempo decorrido < 80% do SLA | Tempo ok, sem urgência |
| **PRÓXIMO A VENCER** | 80% ≤ Tempo < 100% do SLA | Atenção necessária |
| **VENCIDO ATIVO** | Tempo > 100% do SLA | Violação de SLA |
| **CUMPRIDO** | Ticket fechado E Tempo ≤ SLA | Objetivo alcançado ✅ |
| **VIOLADO** | Ticket fechado E Tempo > SLA | Não atingiu SLA ❌ |
| **PAUSADO** | Status = "Em Análise" ou "Aguardando" | Tempo não conta |

### 3. Quando é Considerado "Dentro do SLA"?

```python
if chamado_fechado:
    if tempo_decorrido <= tempo_sla:
        status = "CUMPRIDO" ✅
    else:
        status = "VIOLADO" ❌
else:  # chamado aberto
    percentual = (tempo_decorrido / tempo_sla) * 100
    if percentual > 100:
        status = "VENCIDO ATIVO" ⚠️
    elif percentual >= 80:
        status = "PRÓXIMO A VENCER" ⏰
    else:
        status = "DENTRO DO PRAZO" ✅
```

---

## Cálculo de P90

### O que é P90?

**P90 (90º Percentil)** é um número que representa o tempo máximo que 90% dos chamados levam para ser resolvidos.

**Exemplo:**
Se temos 10 chamados com tempos: 2h, 3h, 4h, 5h, 6h, 7h, 8h, 9h, 10h, 20h
- P90 = 9h (90% dos chamados foram resolvidos em até 9 horas)

### Por que usar P90?

Porque:
- ✅ Não é afetado por outliers (aquele chamado que durou 20h)
- ✅ Representa realidade melhor que a média
- ✅ Permite ajustar SLAs com base em dados reais

### Margem de Segurança (15%)

Aplicamos uma margem de 15% ao valor calculado:

```
SLA Recomendado = round(P90 * 1.15)
```

**Exemplo:**
- P90 calculado: 20 horas
- Com margem: 20 * 1.15 = 23 horas
- Recomendação: 23 horas

Essa margem protege contra variações e garante que 90% dos chamados reais sejam cumpridos.

### Como o P90 é Calculado?

1. **Período analisado**: últimos 30 dias
2. **Chamados inclusos**: apenas status "Concluído" ou "Cancelado"
3. **Cálculo**:
   - Coleta tempo de resolução de todos os chamados
   - Ordena os tempos
   - Pega a posição 90% da lista
   - Multiplica por 1.15 (margem de segurança)
   - Arredonda para número inteiro

```
tempos_ordenados = [2, 3, 4, 5, 6, 7, 8, 9, 10, 20]  # 10 valores
indice_90 = 0.9 * (10 - 1) = 8.1 ≈ 8
p90 = tempos_ordenados[8] = 10  # 9º valor (0-indexado)
p90_com_margem = round(10 * 1.15) = 12
```

### P90 Incremental

É uma otimização que não recalcula tudo de novo:

1. **Armazena em cache** os tempos já calculados
2. **Busca apenas novos chamados** (por ID)
3. **Combina com dados antigos** e recalcula P90
4. **Muito mais rápido** que recalcular de zero

---

## Cache e Reset

### Sistema de Cache

O sistema mantém caches em dois lugares:

#### 1. Cache em Memória (Rápido)
- Armazenado na RAM do servidor
- **TTL** (Time To Live): até 24 horas dependendo da métrica
- Perdido quando servidor reinicia

#### 2. Cache no Banco de Dados (Persistente)
- Armazenado em `metrics_cache_db`
- Persiste mesmo após restart
- Pode ter expiração

### Estratégia de Leitura

```
1. Tenta buscar da memória
   ↓
2. Se expirou ou não encontrou, tenta banco de dados
   ↓
3. Se encontrou no banco e ainda é válido, carrega em memória
   ↓
4. Se expirou em ambos, recalcula
```

### Chaves de Cache Principais

```
sla_compliance_24h      → Conformidade SLA (últimas 24h)
sla_compliance_mes      → Conformidade SLA (mês)
sla_distribution        → Distribuição dentro/fora SLA
tempo_resposta_24h      → Tempo médio de resposta
tempo_resposta_mes      → Tempo médio de resposta (mês)
metrics_basic           → Métricas básicas do dashboard
chamados_hoje:{data}    → Contagem de chamados por dia
sla_p90_tempos_resposta:{prioridade}
sla_p90_tempos_resolucao:{prioridade}
sla_p90_ultimo_chamado_id:{prioridade}
```

### O que é o "Reset do SLA"?

O reset limpa completamente o sistema e começa do zero:

#### 1. O que é apagado:
- ❌ Todo cache em memória
- ❌ Todo cache no banco de dados
- ❌ Histórico de P90 incremental

#### 2. O que é registrado:
- ✅ Data/hora de `ultimo_reset_em` em cada configuração de SLA
- ✅ Próximos cálculos ignorarão chamados abertos ANTES do reset

#### 3. Exemplo:

```
Reset feito em: 2025-11-28 17:01:36

Antes do reset:
- Chamado A (aberto 2025-11-20)
- Chamado B (aberto 2025-11-25)
- Chamado C (aberto 2025-11-28)

Depois do reset:
- Chamado A e B: IGNORADOS nos próximos cálculos P90
- Chamado C: INCLUÍDO (aberto APÓS o reset)
```

### Por que Fazer Reset?

- 🔄 Mudou a configuração de SLA e quer recalcular do zero
- 🧹 Quer limpar dados históricos antigos
- ⚡ Começa fresco com base em dados mais recentes

---

## Métricas e Relatórios

### 1. SLA Distribution (Distribuição)

Conta quantos chamados estão dentro vs fora do SLA:

```
Período: últimos 30 dias
Chamados analisados: 100

Dentro SLA: 68
Fora SLA:   32

Percentual Dentro:  68%
Percentual Fora:    32%
```

**Como é calculado:**
1. Busca todos os chamados do período
2. Exclui cancelados
3. Para cada, calcula tempo de resolução
4. Compara com SLA configurado
5. Conta e calcula percentual

### 2. SLA Compliance (Conformidade)

Medida de quanto o sistema está respeitando os SLAs:

**Compliance 24h**: análise em tempo real das últimas 24 horas
```
Chamados ativos ou fechados nas últimas 24h: 20
Dentro SLA: 19
Compliance: 19/20 = 95%
```

**Compliance Mês**: cálculo consolidado do mês
```
Mês: Novembro
Total resolvido: 150
Dentro SLA: 102
Compliance: 102/150 = 68%
```

### 3. Tempo Médio de Resposta

Média de quanto tempo leva para dar primeira resposta:

```
Últimos 30 dias:
- Prioridade Alta: 2.5 horas
- Prioridade Normal: 6.3 horas
```

### 4. P90 Analysis (Análise P90)

Recomendação de SLAs baseada em dados reais:

```
Prioridade: Alta
SLA Atual: 24 horas

Análise de 50 chamados nos últimos 30 dias:
- Mínimo: 0.5 horas
- Máximo: 45 horas
- P90: 20 horas

Com margem: 20 * 1.15 = 23 horas

Recomendação:
- Mude SLA de 24h para 23h?
- Ganho: vai passar de 68% para 72% de conformidade
```

---

## Troubleshooting

### Problema: Todas as métricas mostram 0 (zero)

**Causa provável:**
- Sistema foi resetado recentemente
- Não há chamados fechados APÓS o reset

**Solução:**
```bash
# 1. Verifique quando foi o reset:
SELECT prioridade, ultimo_reset_em FROM sla_configuration;

# 2. Se quiser restaurar cálculos anteriores, limpe o reset:
UPDATE sla_configuration SET ultimo_reset_em = NULL;

# 3. Recalcule P90:
POST /api/sla/recalcular/p90

# 4. Verifique novamente
GET /api/metrics/dashboard/basic
```

### Problema: Erro "or_ is not defined"

**Causa:** Falta importação no arquivo de API

**Solução:**
```python
# Em backend/ti/api/sla.py, adicione:
from sqlalchemy import and_, or_
```

### Problema: Cache não limpa

**Causa:** Dados antigos ainda estão em cache

**Solução:**
```bash
# Limpe o cache via API:
POST /api/sla/cache/reset-all

# Ou delete diretamente do banco:
DELETE FROM metrics_cache_db;
```

### Problema: P90 retorna "sem dados suficientes"

**Causa:**
- Menos de 2 chamados fechados no período
- Todos estão em status aberto ou cancelado

**Solução:**
1. Feche alguns chamados com status "Concluído"
2. Aguarde algumas horas
3. Tente recalcular P90

### Problema: Tempo de SLA está muito alto/baixo

**Causa:**
- Há chamados "problemáticos" que inflam a estatística
- ou SLA está mal configurado

**Solução:**
1. Analise usando `/api/sla/recommendations/p90-analysis`
2. Verifique outliers (aquele chamado que durou muito)
3. Use P90 para sugestão de novo SLA (ignora outliers)

---

## Endpoints Úteis

### Visualizar SLA
```bash
GET /api/sla/config                          # Lista configurações
GET /api/sla/config/{id}                     # Detalhes de uma prioridade
GET /api/metrics/dashboard/sla               # Métricas do dashboard
GET /api/sla/recommendations/p90-analysis    # Análise P90 recomendado
```

### Atualizar SLA
```bash
PUT /api/sla/config/{id}                     # Atualiza tempo de resposta/resolução
POST /api/sla/business-hours                 # Define horário de funcionamento
POST /api/sla/feriados                       # Adiciona dias não úteis
```

### Recalcular P90
```bash
POST /api/sla/recalcular/p90                 # Recalcula P90 (completo, 30 dias)
POST /api/sla/recalcular/p90-incremental    # Recalcula P90 (incremental, mais rápido)
```

### Reset e Cache
```bash
POST /api/sla/reset-and-recalculate          # Reset completo do SLA
POST /api/sla/cache/reset-all                # Limpa apenas cache
GET  /api/sla/cache/stats                    # Estatísticas do cache
POST /api/sla/cache/warmup                   # Carrega cache em memória
```

---

## Resumo Executivo

### Como o SLA Funciona (Simplificado)

1. **Define-se um limite de tempo** por prioridade (ex: Alta = 24 horas)
2. **Cronômetro começa** quando chamado é aberto
3. **Conta apenas horas comerciais** (segunda-sexta, 08-18)
4. **Se pausado** (Aguardando Cliente), tempo não avança
5. **Quando fechado**, compara tempo decorrido com limite
   - Se tempo ≤ limite: ✅ CUMPRIDO
   - Se tempo > limite: ❌ VIOLADO
6. **Métricas agregadas** mostram quantos foram cumpridos
7. **P90 recomenda** ajuste de limites com base em dados reais

### Fluxo Típico

```
Chamado aberto (seg 10:00)
  ↓
Primeira resposta (seg 11:00) → 1h contado
  ↓
Parado em "Aguardando" (seg 14:00 → ter 09:00) → 0h contado
  ↓
Retomado (ter 09:00)
  ↓
Resolvido (ter 15:00) → 6h contados (seg: 8h + ter: 6h = 14h)
  ↓
Verifica SLA (24h) → 14h < 24h → ✅ CUMPRIDO
```

---

## Referências de Código

- **Cálculo de horas de negócio**: `backend/ti/services/sla.py` (linhas 58-165)
- **Regras de estado**: `backend/ti/services/sla_status.py` (linhas 60-97)
- **P90**: `backend/ti/services/sla_p90_calculator.py` (todo o arquivo)
- **Métricas**: `backend/ti/services/metrics.py` (todo o arquivo)
- **Cache**: `backend/ti/services/sla_cache.py` (todo o arquivo)
- **API**: `backend/ti/api/sla.py` (todo o arquivo)

---

**Última atualização**: 2025-11-28
**Versão**: 1.0
