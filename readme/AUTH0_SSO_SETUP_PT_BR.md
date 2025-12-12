# Guia de Configuração de Single Sign-On (SSO) com Auth0

## Visão Geral

Este guia explica como configurar o Single Sign-On (SSO) entre múltiplos portais (Portal Evoque e Portal Financeiro) usando Auth0. Com a configuração adequada, os usuários podem fazer login em um portal e ser automaticamente autenticados no outro portal sem precisar reinserir as credenciais.

## Problema Resolvido

**Antes:** Os usuários precisavam fazer login separadamente em cada portal, mesmo que ambos usassem Auth0.

**Depois:** Os usuários fazem login em um portal (ex: Evoque) e quando acessam o outro portal (Financeiro), são automaticamente autenticados via gerenciamento de sessão do Auth0.

## Como o SSO Funciona

1. **Usuário faz login no Portal Evoque** → Auth0 cria um cookie de sessão em `https://seu-dominio-auth0.auth0.com`
2. **Usuário acessa Portal Financeiro** → A aplicação verifica se existe uma sessão Auth0 ativa
3. **Sessão Auth0 encontrada** → Usuário é automaticamente autenticado sem precisar reinserir credenciais
4. **Sem sessão Auth0** → Usuário vê a tela de login

## Componentes Alterados

### Contexto de Autenticação Frontend (`frontend/src/lib/auth-context.tsx`)

**Novos Recursos:**

- **Geração Segura de Estado (State)**: Usa `crypto.getRandomValues()` para proteção CSRF criptograficamente segura
- **Validação do Parâmetro State**: Valida o parâmetro state retornado pelo Auth0 para prevenir ataques CSRF
- **Fluxo OAuth 2.0 Padrão**: Implementa o fluxo padrão de código de autorização OAuth
- **Tratamento de Erros**: Manipula corretamente erros do Auth0, incluindo `login_required` que indica ausência de sessão existente

**Funções Principais:**

```typescript
// Gera parâmetro state aleatório seguro
generateSecureState(): string

// Valida o callback OAuth
handleAuth0Callback(code, state)

// Faz login com Auth0
loginWithAuth0()
```

## Configuração Obrigatória no Auth0

### 1. Configurações do Tenant Auth0

Certifique-se de ter:

- Conta e domínio Auth0 (ex: `seu-dominio.auth0.com`)
- Duas aplicações criadas: uma para Portal Evoque, uma para Portal Financeiro
- Conexão de banco de dados habilitada (Username-Password-Authentication)

### 2. Configurações da Aplicação Portal Evoque

No Dashboard Auth0 → Applications → Portal Evoque:

**URIs da Aplicação:**

- **Login URL**: `https://portalevoque.com`
- **Callback URLs**:
  ```
  http://localhost:5173/auth/callback
  http://localhost:3005/auth/callback
  https://portalevoque.com/auth/callback
  https://app.portalevoque.com/auth/callback
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
  ```
- **Logout URLs**:
  ```
  http://localhost:5173
  http://localhost:3005
  https://portalevoque.com
  https://app.portalevoque.com
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
  ```
- **Allowed Web Origins** (para CORS/Silent Auth):
  ```
  http://localhost:5173
  http://localhost:3005
  https://portalevoque.com
  https://app.portalevoque.com
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
  ```

**Conexões:**

- Habilitar "Username-Password-Authentication" (conexão de banco de dados)
- Habilitar conexões sociais se necessário (Google, etc.)

### 3. Configurações da Aplicação Portal Financeiro

No Dashboard Auth0 → Applications → Portal Financeiro:

**URIs da Aplicação:**

- **Login URL**: `https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io`
- **Callback URLs**:
  ```
  http://localhost:5173/auth/callback
  http://localhost:3005/auth/callback
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
  ```
- **Logout URLs**:
  ```
  http://localhost:5173
  http://localhost:3005
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
  ```
- **Allowed Web Origins**:
  ```
  http://localhost:5173
  http://localhost:3005
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
  ```

**Conexões:**

- Habilitar "Username-Password-Authentication" (MESMA conexão que o Portal Evoque)
- Habilitar conexões sociais se necessário

### 4. Variáveis de Ambiente Obrigatórias

Ambas as aplicações precisam destas variáveis de ambiente configuradas:

```env
VITE_AUTH0_DOMAIN=seu-dominio.auth0.com
VITE_AUTH0_CLIENT_ID=seu-client-id-aqui
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_AUTH0_AUDIENCE=sua-api-audience
VITE_AUTH0_LOGOUT_URI=http://localhost:5173
```

Para produção, atualize as URLs:

```env
VITE_AUTH0_DOMAIN=seu-dominio.auth0.com
VITE_AUTH0_CLIENT_ID=seu-client-id-aqui
VITE_AUTH0_REDIRECT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
VITE_AUTH0_AUDIENCE=sua-api-audience
VITE_AUTH0_LOGOUT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
```

## Fluxo de Login SSO

### Passo 1: Usuário Clica no Botão de Login

Usuário no Portal Financeiro clica no botão "Entrar com Auth0".

### Passo 2: Frontend Inicia OAuth

```typescript
const state = generateSecureState();
sessionStorage.setItem("auth_state", state);

window.location.href = `https://seu-dominio.auth0.com/authorize?
  response_type=code
  client_id=${CLIENT_ID}
  redirect_uri=${REDIRECT_URI}
  scope=openid profile email offline_access
  state=${state}`;
```

### Passo 3: Auth0 Verifica a Sessão

- **Se o usuário está logado no Auth0** (vindo do Portal Evoque): Auth0 retorna imediatamente o código de autorização
- **Se o usuário NÃO está logado**: Auth0 mostra o formulário de login ou erro `login_required`

### Passo 4: Redirecionamento de Volta para a App

Auth0 redireciona para: `https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback?code=xxx&state=yyy`

### Passo 5: Frontend Valida o State

```typescript
const storedState = sessionStorage.getItem("auth_state");
if (state !== storedState) {
  throw new Error("Ataque CSRF detectado - incompatibilidade de state");
}
```

### Passo 6: Trocar Código por Token

Frontend envia o código para o backend: `POST /api/auth/auth0-exchange`

Backend:

1. Troca o código por token de acesso com Auth0
2. Valida a assinatura do token
3. Extrai o email do usuário
4. Busca o usuário no banco de dados
5. Retorna dados do usuário e permissões

### Passo 7: Usuário Autenticado

Frontend armazena o token de sessão e dados do usuário em `sessionStorage` e faz login do usuário.

## Solução de Problemas

### "O parâmetro state está faltando"

**Causa:** O parâmetro state não foi armazenado ou validado corretamente.

**Solução:**

1. Verifique se `sessionStorage` está habilitado no navegador
2. Verifique se o state está sendo armazenado antes do redirecionamento: `sessionStorage.setItem("auth_state", state)`
3. Verifique se a URL de redirecionamento corresponde exatamente à configurada no Auth0

### Usuário Faz Login no Evoque, Mas Não é Automaticamente Logado no Financeiro

**Causa:** SSO não está funcionando por falta de configuração do Auth0.

**Possíveis Soluções:**

1. Verifique se ambas as aplicações estão no MESMO tenant Auth0
2. Verifique se ambas as aplicações têm a MESMA conexão de banco de dados habilitada
3. Verifique se "Allowed Web Origins" inclui o domínio do Portal Financeiro
4. Limpe os cookies do navegador e tente novamente
5. Verifique o console do navegador para mensagens de erro do Auth0

### Usuário Vê a Tela de Login no Portal Financeiro

**Comportamento Esperado:** Se o usuário NÃO está logado no Auth0 (primeira vez acessando o sistema), ele deve ver a tela de login. Isso é correto!

**Quando é um problema:**

- Se o usuário ACABOU DE fazer login no Portal Evoque, ele NÃO deve ver a tela de login
- Verifique se o cookie de sessão Auth0 está sendo definido (verifique a aba Network do navegador)

### Erros CORS no Console

**Causa:** "Allowed Web Origins" não configurado corretamente no Auth0.

**Solução:**

1. Vá para Dashboard Auth0 → Applications → Settings
2. Adicione o domínio do seu portal em "Allowed Web Origins"
3. Salve e aguarde ~1 minuto para que as mudanças se propaguem
4. Limpe o cache e cookies do navegador

## Recursos de Segurança Implementados

### 1. Proteção CSRF via Parâmetro State

- State é gerado usando valores aleatórios criptograficamente seguros
- State é validado no callback
- Se o state não corresponder, a autenticação é rejeitada

### 2. Armazenamento Seguro de Tokens

- Tokens de acesso armazenados apenas em `sessionStorage` (não em localStorage)
- Sessão expira após 24 horas
- Sessão pode ser revogada a qualquer momento

### 3. Verificação de Email

- Usuários devem ter email verificado no Auth0 (se obrigatório)
- Backend valida o token antes de emitir sessão

### 4. HTTPS Obrigatório (Produção)

- Todos os redirecionamentos OAuth usam HTTPS
- Cookies marcados como seguros (apenas HTTPS)

## Testando SSO Localmente

### Configuração do Ambiente Local

1. Configure ambos os portais para executar localmente:

   ```bash
   # Terminal 1: Portal Evoque
   cd frontend
   npm run dev  # Executa em http://localhost:5173

   # Terminal 2: Portal Financeiro (projeto diferente)
   cd frontend
   npm run dev  # Também executa em http://localhost:5173
   ```

   ⚠️ Eles terão conflito na mesma porta. Use portas diferentes:

   ```bash
   # Terminal 1: Portal Evoque
   npm run dev

   # Terminal 2: Portal Financeiro
   VITE_AUTH0_REDIRECT_URI=http://localhost:5174/auth/callback npm run dev -- --port 5174
   ```

2. Configure Auth0 com ambas as URLs localhost:
   - Portal Evoque: `http://localhost:5173/auth/callback`
   - Portal Financeiro: `http://localhost:5174/auth/callback`

3. Teste o Fluxo SSO:
   - Faça login no Portal Evoque em `http://localhost:5173`
   - Abra Portal Financeiro em `http://localhost:5174`
   - Você deve ser automaticamente autenticado!

## Testando em Produção

### Antes de Fazer Deploy

1. **Teste Troca de Código OAuth**

   ```bash
   curl -X POST https://seu-dominio.auth0.com/oauth/token \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "SEU_CLIENT_ID",
       "client_secret": "SEU_CLIENT_SECRET",
       "code": "CODIGO_AUTH_DO_NAVEGADOR",
       "grant_type": "authorization_code",
       "redirect_uri": "https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback"
     }'
   ```

2. **Teste Validação de Token**
   - Verifique o endpoint `/api/auth/debug/config` do backend
   - Verifique se a configuração Auth0 está carregada corretamente

3. **Teste Busca no Banco de Dados**
   - Certifique-se de que o usuário existe no banco de dados com o mesmo email do Auth0
   - Usuário deve ter permissões atribuídas

### Checklist de Deployment

- [ ] URLs de callback Auth0 atualizadas para domínio de produção
- [ ] Web origins Auth0 atualizados para domínio de produção
- [ ] URLs de logout atualizadas para domínio de produção
- [ ] Variáveis de ambiente configuradas corretamente no servidor
- [ ] Banco de dados contém todos os usuários com emails correspondentes
- [ ] HTTPS habilitado para todas as URLs
- [ ] Verificação de email Auth0 obrigatória (opcional mas recomendado)

## Avançado: SSO Entre Domínios Diferentes

Para SSO entre domínios completamente diferentes (ex: `portalevoque.com.br` e `financeiro.outraempresa.com`):

1. Ambos os domínios devem estar no MESMO tenant Auth0
2. Ambas as aplicações devem ter conexões de banco de dados idênticas
3. Adicione ambos os domínios em "Allowed Web Origins" para cada aplicação
4. Auth0 compartilhará automaticamente o cookie de sessão entre os domínios

⚠️ Nota: Cookies NÃO viajam entre registros de domínio completamente diferentes (.com.br vs .com). Use apenas a abordagem de mesmo tenant!

## Referências

- [Fluxo de Código de Autorização Auth0](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow)
- [PKCE Auth0 (atualmente não implementado mas recomendado para SPAs)](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow-with-proof-key-for-code-exchange)
- [Parâmetro State Auth0 para Proteção CSRF](https://auth0.com/docs/secure/attack-protection/state-parameter)
- [Melhores Práticas de Segurança OAuth 2.0](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
