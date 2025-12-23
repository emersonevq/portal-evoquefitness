# Diagnóstico: Sistema de Permissões após Auth0

## 🔍 Problema Identificado

Após a implementação do Auth0, o sistema de sincronização de permissões em tempo real parou de funcionar para os níveis de acesso (administrador, gestor, gerente, gerente regional, coordenador, etc).

## 🔧 Solução Implementada

### 1. **Frontend (useAuth.ts)**

- ✅ Adicionado intervalo de re-identificação do Socket.IO (a cada 2 segundos, máximo 5 tentativas)
- ✅ Garantia de que usuários Auth0 se identifiquem corretamente quando o Socket.IO se conecta
- ✅ Fallback de polling a cada 30 segundos para sincronização garantida
- ✅ Melhor logging para debug

### 2. **Frontend (auth-context.tsx)**

- ✅ Adicionada identificação imediata no Socket.IO após login Auth0
- ✅ Garante que o usuário seja reconhecido imediatamente na sala `user:{user_id}`

### 3. **Backend (realtime.py)**

- ✅ Melhor logging para confirmar que eventos estão sendo emitidos
- ✅ Detecção de falhas silenciosas

### 4. **Backend (usuarios.py)**

- ✅ Melhor logging na emissão de eventos
- ✅ Tratamento de erros mais detalhado

## 📋 Como Testar

### Teste 1: Verificar Sincronização em Tempo Real

**Pré-requisitos:**

- Dois navegadores/abas abertas
- Admin logado em um
- Usuário normal logado em outro

**Passos:**

1. Abra o navegador com DevTools (F12)
2. Vá para a aba Console
3. Em uma aba, faça login com um usuário de admin no painel administrativo
4. Em outra aba, faça login com um usuário comum
5. No painel admin, edite os setores do usuário comum (altere de "Setor A" para "Setor B")
6. Clique em "Salvar"
7. **Na aba do usuário comum, observe o console:**

**Esperado:**

```
[SIO] ✓ Received auth:refresh event from server {user_id: 123}
[SIO] ✓ Event is for current user 123 - will refresh permissions
[AUTH] ⟳ Refreshing user data for id 123
[AUTH] ✓ SETORES CHANGED: Setor A → Setor B
```

**Se NÃO vir essas mensagens:**

- O Socket.IO não está recebendo o evento
- Verifique o console do servidor nos logs

### Teste 2: Verificar Fallback de Polling

Mesmo que o Socket.IO falhe, o sistema deve sincronizar a cada 30 segundos.

**Passos:**

1. Faça login com usuário comum
2. No console, note o horário
3. Edite um setor do usuário no painel admin
4. Aguarde até 30 segundos
5. O console deve mostrar:

```
[AUTH] ⟳ Refreshing user data for id 123
[AUTH] ✓ SETORES CHANGED: ...
```

### Teste 3: Verificar Identificação Socket.IO

**No console do usuário logado:**

```javascript
// Copie e cole no console:
console.log("[TEST] Usuário ID:", (window as any).__APP_SOCK__ ? "Socket.IO configurado" : "Socket.IO não configurado");
console.log("[TEST] Socket conectado:", (window as any).__APP_SOCK__?.connected ? "SIM" : "NÃO");
console.log("[TEST] Socket ID:", (window as any).__APP_SOCK__?.id);
```

**Esperado:**

- Socket.IO configurado: SIM
- Socket conectado: SIM
- Socket ID: um ID aleatório (ex: `abc123def456`)

## 🔴 Se o Problema Persistir

### 1. Verifique os Logs do Servidor

Procure por mensagens como:

```
[SIO] emit_refresh_sync: emitting auth:refresh to room=user:123
[API] ✓ Immediate refresh event sent successfully for user_id=123
```

### 2. Verifique a Rede

- Abra DevTools (F12) → Network
- Procure por requisições `socket.io?EIO=4&transport=websocket`
- Deve haver uma conexão WebSocket estabelecida

### 3. Limpe o Cache

```javascript
// No console do navegador:
sessionStorage.clear();
location.reload();
```

### 4. Verifique Permissões no Banco

```sql
-- No seu banco de dados, procure pelo usuário:
SELECT id, email, nivel_acesso, _setores, _bi_subcategories
FROM user
WHERE email = 'usuario@example.com';
```

Confirme que:

- `nivel_acesso` está preenchido
- `_setores` contém um JSON válido (ex: `["Setor A", "Setor B"]`)
- `_bi_subcategories` está correto (pode ser NULL)

## 📊 Fluxo Esperado

```
1. Admin edita permissões de um usuário
                    ↓
2. Frontend envia PUT /api/usuarios/{id}
                    ↓
3. Backend atualiza banco de dados
                    ↓
4. Backend emite event Socket.IO → room: user:{id}
                    ↓
5. Frontend recebe event auth:refresh
                    ↓
6. Frontend faz refresh das permissões via GET /api/usuarios/{id}
                    ↓
7. Frontend atualiza sessionStorage
                    ↓
8. UI re-renderiza com novas permissões
```

## 🎯 Métricas de Sucesso

Após fazer essas correções, você deve ver:

1. ✅ **Socket.IO conectado** logo após login Auth0
2. ✅ **Eventos auth:refresh** chegando em tempo real quando permissões são editadas
3. ✅ **Permissões atualizadas** no máximo em 2 segundos (via Socket.IO) ou 30 segundos (via polling)
4. ✅ **Redirecionamentos automáticos** funcionando baseado no nível de acesso
5. ✅ **Menus e botões** aparecendo/desaparecendo de acordo com as permissões

## 📝 Próximas Ações

Se depois dessas correções o problema persistir:

1. **Ativar modo debug avançado** nos logs
2. **Verificar se há firewalls** bloqueando WebSocket
3. **Testar com diferentes navegadores** para descartar cache
4. **Contatar suporte** com os logs da console do navegador e servidor

## 🔗 Arquivos Modificados

- `frontend/src/hooks/useAuth.ts` - Melhor re-identificação Socket.IO
- `frontend/src/lib/auth-context.tsx` - Identificação imediata após Auth0
- `backend/core/realtime.py` - Melhor logging de emissão
- `backend/ti/api/usuarios.py` - Melhor logging de atualização

## ⚙️ Configuração Recomendada

Para melhor diagnóstico, adicione essas variáveis de ambiente (opcional):

```bash
# Para ativar logging verbose (em desenvolvimento)
DEBUG_AUTH=true
DEBUG_SOCKET=true
```

Estas variáveis ainda não estão sendo usadas, mas você pode implementá-las futuramente.
