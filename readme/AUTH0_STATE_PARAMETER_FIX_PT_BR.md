# Correção: "The State Parameter is Missing"

## O Problema

Você estava recebendo o erro **"The state parameter is missing"** ao tentar fazer login no Portal Financeiro via Auth0, mesmo que:
- O Auth0 estivesse corretamente configurado
- O usuário existisse no Auth0 com credenciais válidas
- A mesma conta funcionasse no Portal Evoque

## Raiz do Problema

O erro ocorria porque o código anterior tinha implementação incorreta do fluxo OAuth 2.0:

### Código Anterior (Incorreto)

```typescript
// ❌ INCORRETO: Tentando fazer fetch da URL de autorização
const authorizationUrl = new URL(`https://${import.meta.env.VITE_AUTH0_DOMAIN}/authorize`);

const params = {
  response_type: "code",
  client_id: import.meta.env.VITE_AUTH0_CLIENT_ID,
  redirect_uri: import.meta.env.VITE_AUTH0_REDIRECT_URI,
  state: Math.random().toString(36).substring(7), // ❌ State fraco e não armazenado
};

Object.entries(params).forEach(([key, value]) => {
  authorizationUrl.searchParams.append(key, value);
});

// ❌ ERRADO: Tentar fazer fetch de uma URL de autorização
const response = await fetch(authorizationUrl.toString(), {
  method: "GET",
  signal: controller.signal,
});
```

**Problemas:**
1. ❌ Tentava fazer `fetch()` do endpoint `/authorize` do Auth0 (isso não funciona)
2. ❌ Gerava state com `Math.random()` (não é criptograficamente seguro)
3. ❌ Não armazenava o state no `sessionStorage` antes do redirecionamento
4. ❌ Falta de validação do state no callback

## A Solução

### Código Novo (Correto)

```typescript
// ✅ CORRETO: Gerar state seguro e armazenar
function generateSecureState(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array); // Criptograficamente seguro
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

// ✅ Armazenar state ANTES de fazer o redirect
const state = generateSecureState();
sessionStorage.setItem("auth_state", state); // ← CRÍTICO!

// ✅ Construir a URL de autorização
const authorizationUrl = new URL(`https://${import.meta.env.VITE_AUTH0_DOMAIN}/authorize`);

const params = {
  response_type: "code",
  client_id: import.meta.env.VITE_AUTH0_CLIENT_ID,
  redirect_uri: import.meta.env.VITE_AUTH0_REDIRECT_URI,
  scope: "openid profile email offline_access",
  audience: import.meta.env.VITE_AUTH0_AUDIENCE,
  state: state, // ✅ Use o state gerado
};

Object.entries(params).forEach(([key, value]) => {
  authorizationUrl.searchParams.append(key, value);
});

// ✅ CORRETO: Redirecionar (não fazer fetch)
window.location.href = authorizationUrl.toString();
```

### Validação do State no Callback

```typescript
// ✅ Validar state no callback para proteção CSRF
const code = searchParams.get("code");
const state = searchParams.get("state");

const storedState = sessionStorage.getItem("auth_state");
const isValidState = storedState && state === storedState;

if (!isValidState) {
  console.error("❌ Ataque CSRF detectado - state inválido");
  throw new Error("Invalid state parameter - CSRF validation failed");
}

// ✅ Limpar state após validação
sessionStorage.removeItem("auth_state");
```

## Mudanças Implementadas

### 1. Função de Geração de State Seguro

```typescript
function generateSecureState(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join("");
}
```

**Por que é mais seguro:**
- ✅ Usa `crypto.getRandomValues()` (verdadeiro aleatório criptográfico)
- ✅ Gera 32 bytes (256 bits) de entropia
- ✅ Impossível adivinhar ou reproduzir

### 2. Armazenamento Correto do State

```typescript
// Antes de redirecionar para Auth0
sessionStorage.setItem("auth_state", state);

// Depois que Auth0 redireciona de volta
const storedState = sessionStorage.getItem("auth_state");
const isValid = state === storedState;
```

### 3. Redirecionamento Correto

```typescript
// ✅ CORRETO: Redirecionamento direto
window.location.href = authorizationUrl.toString();

// ❌ ERRADO: Tentar fazer fetch
const response = await fetch(authorizationUrl.toString());
```

**Por quê?**
- O endpoint `/authorize` do Auth0 NÃO é uma API
- Ele é um endpoint de redirecionamento HTML
- Deve ser acessado via `window.location.href`, não via `fetch()`

### 4. Tratamento de Erros Auth0

```typescript
const error = searchParams.get("error");
const errorDescription = searchParams.get("error_description");

if (error) {
  console.error("[AUTH] Auth0 error:", error, errorDescription);
  
  // Se error=login_required, significa que não há sessão ativa
  if (error === "login_required") {
    console.debug("[AUTH] No Auth0 session found (expected for first login)");
    return;
  }
  
  // Para outros erros, redirecionar para login
  navigate("/auth0/login", { replace: true });
}
```

## Fluxo Correto Completo

```
USUÁRIO CLICA LOGIN
    ↓
Frontend gera state seguro e armazena em sessionStorage
    ↓
Frontend redireciona para: https://auth0.com/authorize?code=xxx&state=yyy
    ↓
Auth0 verifica se há sessão ativa
    ├─ SIM (usuário logado em outro portal): 
    │   → Auth0 retorna código de autorização
    │
    └─ NÃO (primeiro login):
        → Auth0 mostra tela de login
        → Usuário entra credenciais
        → Auth0 retorna código de autorização
    ↓
Auth0 redireciona para: https://portal.com/auth/callback?code=zzz&state=yyy
    ↓
Frontend valida state:
    ├─ State matches (seguro): Continuar
    └─ State não matches (CSRF): Rejeitar
    ↓
Frontend envia code para backend: POST /api/auth/auth0-exchange
    ↓
Backend troca code por access_token com Auth0
    ↓
Backend busca usuário no banco de dados
    ↓
Backend retorna dados do usuário
    ↓
Frontend armazena sessão em sessionStorage
    ↓
✅ USUÁRIO AUTENTICADO
```

## Testando a Correção

### 1. Teste Local

```bash
# Terminal 1: Portal Evoque
cd frontend
npm run dev  # http://localhost:5173

# Terminal 2: Portal Financeiro (outro diretório/porta)
VITE_AUTH0_REDIRECT_URI=http://localhost:5174/auth/callback npm run dev -- --port 5174
```

**Passos para testar:**
1. Abra `http://localhost:5173`
2. Clique em "Entrar com Auth0"
3. Faça login com seu usuário Auth0
4. Volte para `http://localhost:5174`
5. Clique em "Entrar com Auth0"
6. ✅ Você deve ser automaticamente autenticado (SSO)

### 2. Teste de Console

Abra o console do navegador (`F12`) e procure por:

```
[AUTH] State stored: abc123def456...
[AUTH] Redirecting to Auth0 for login
[AUTH] ✓ Code and state found
[AUTH] ✓ State parameter validated
```

✅ Se vir essas mensagens, o fluxo está funcionando corretamente.

### 3. Teste de Network

Abra a aba Network do DevTools (`F12` → Network) e procure por:

1. **POST `/api/auth/auth0-exchange`**
   - Status: 200
   - Response contém: `id`, `email`, `nivel_acesso`, `setores`, `access_token`

2. **GET `/auth/callback?code=...&state=...`**
   - Status: 200 (redirecionado para `/setor/...` ou `/`)

## Checklist de Verificação

- [ ] Geração de state usa `crypto.getRandomValues()`
- [ ] State é armazenado em `sessionStorage` antes do redirect
- [ ] State é validado no callback
- [ ] Endpoint Auth0 é acessado via `window.location.href` (não `fetch()`)
- [ ] Erros Auth0 são tratados (`login_required`, `access_denied`, etc.)
- [ ] Backend recebe e valida o código
- [ ] Backend retorna dados do usuário
- [ ] Frontend armazena sessão em `sessionStorage`
- [ ] Não há erros CORS no console
- [ ] não há erros "state parameter is missing"

## Comparação: Antes vs Depois

| Aspecto | Antes ❌ | Depois ✅ |
|---------|---------|----------|
| Geração de State | `Math.random()` (fraco) | `crypto.getRandomValues()` (seguro) |
| Armazenamento de State | Não armazenado | `sessionStorage.setItem()` |
| Validação de State | Não validado | Validado no callback |
| Acesso Auth0 | `fetch()` (erro) | `window.location.href` (correto) |
| Tratamento de Erros | Genérico | Específico por tipo de erro |
| Proteção CSRF | Nenhuma | State parameter |
| Fluxo OAuth 2.0 | Incorreto | Correto (RFC 6749) |

## Segurança

### Por que o State Parameter é Importante?

O parâmetro `state` protege contra ataques **Cross-Site Request Forgery (CSRF)**:

**Ataque CSRF Sem State:**
```
1. Atacante cria site malicioso
2. Usuário clica em link malicioso
3. Link redireciona para: https://portal.com/auth/callback?code=FAKE_CODE
4. Portal troca código fake por token fake
5. Usuário é "logado" como alguém que não é
```

**Com State Parameter:**
```
1. Atacante cria site malicioso
2. Usuário clica em link malicioso
3. Link redireciona para: https://portal.com/auth/callback?code=FAKE_CODE&state=WRONG_STATE
4. Portal verifica: state !== storedState
5. ❌ Callback rejeitado (proteção CSRF)
```

### Outras Proteções Implementadas

- ✅ **Armazenamento em sessionStorage** (não localStorage) - mais seguro
- ✅ **Validação de token** - backend valida assinatura JWT
- ✅ **Verificação de email** - Auth0 pode exigir email verificado
- ✅ **HTTPS obrigatório** - produção
- ✅ **Refresh token** - renovação automática de sessão

## Próximos Passos

### 1. Atualize o Auth0

Verifique se seu Auth0 está configurado corretamente:

```bash
# Teste a troca de código
curl -X POST https://seu-dominio.auth0.com/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "SEU_CLIENT_ID",
    "client_secret": "SEU_CLIENT_SECRET",
    "code": "AUTH_CODE",
    "grant_type": "authorization_code",
    "redirect_uri": "https://seu-dominio.com/auth/callback"
  }'
```

### 2. Teste em Produção

- [ ] URLs Auth0 atualizadas para produção
- [ ] Variáveis de ambiente corretas
- [ ] HTTPS habilitado
- [ ] Teste SSO entre portais

### 3. Monitore Erros

Adicione logs no backend para monitorar:
- Erros de troca de código
- Usuários não encontrados
- Tokens inválidos

## Referências

- [RFC 6749 - OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- [Auth0 Authorization Code Flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow)
- [OWASP - State Parameter](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN - crypto.getRandomValues()](https://developer.mozilla.org/en-US/docs/Web/API/Crypto/getRandomValues)
