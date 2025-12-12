# 🔐 Guia de Implementação: SSO entre Portal Evoque e Portal Financeiro

## 📋 Visão Geral

Este guia implementa **Single Sign-On (SSO)** entre dois portais usando Auth0:
- **Portal Evoque**: `https://app.portalevoque.com/`
- **Portal Financeiro**: `https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/` (QA)

Quando um usuário faz login em um portal, ele fica automaticamente logado no outro graças à **Silent Authentication** do Auth0.

---

## 🎯 Como Funciona

### Fluxo de SSO

```
Usuário em Portal Evoque        Usuário em Portal Financeiro
        │                                  │
        ├─ Faz Login                       ├─ Acessa o portal
        │                                  │
        ├─ Auth0 cria sessão               ├─ Nenhuma sessão local
        │                                  │
        └─────────────────────────────────┴─────────────────────┐
                                                                  │
                              ┌─────────────────────────────────┘
                              │
                              ├─ Tentativa de Silent Auth
                              │
                              ├─ Auth0 reconhece usuário
                              │
                              └─ Login automático ✓
```

### Tecnologia

**Silent Authentication**: Usa o parâmetro `prompt=none` no Auth0:
- Se o usuário já está logado no Auth0, faz login automaticamente
- Se não está logado, falha silenciosamente (usuário vê página de login)
- Funciona mesmo em domínios diferentes

---

## ⚙️ Configuração Portal Evoque (Implementado)

### 1️⃣ Variáveis de Ambiente

Arquivo: `frontend/.env`

```env
VITE_AUTH0_DOMAIN=evoqueacademia.us.auth0.com
VITE_AUTH0_CLIENT_ID=uvLK21vRoW9NMK7EsI46OosLyi9bPK2z
VITE_AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
VITE_AUTH0_REDIRECT_URI=https://app.portalevoque.com/auth/callback
VITE_AUTH0_LOGOUT_URI=https://app.portalevoque.com
```

### 2️⃣ Implementação Frontend

Arquivo: `frontend/src/lib/auth-context.tsx`

**Novo método: `attemptSilentAuth()`**

```typescript
const attemptSilentAuth = async (): Promise<boolean> => {
  // 1. Constrói URL de autorização com prompt=none
  // 2. Tenta comunicar com Auth0 usando fetch
  // 3. Se sucesso: Auth0 redireciona com código
  // 4. Se falha: Retorna false (usuário não está logado)
  
  // Timeout de 5 segundos para não travar a página
};
```

**Integração no `useEffect` inicial**:
- Se não há sessão local e não está na página de callback
- Chama `attemptSilentAuth()`
- Se falha, usuário vê página de login normalmente

### 3️⃣ Backend - Endpoint de Troca de Código

Arquivo: `backend/auth0/routes.py`

Endpoint: `POST /api/auth/auth0-exchange`

```
Fluxo:
1. Frontend envia code + redirect_uri
2. Backend troca code por access_token no Auth0
3. Backend valida JWT
4. Backend busca usuário no banco por email
5. Backend retorna dados do usuário
```

---

## 🔧 Configuração Portal Financeiro (A Fazer)

### Passo 1: Criar `.env` no Frontend

```env
# Auth0 - MESMO tenant do Portal Evoque
VITE_AUTH0_DOMAIN=evoqueacademia.us.auth0.com
VITE_AUTH0_CLIENT_ID=uvLK21vRoW9NMK7EsI46OosLyi9bPK2z
VITE_AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br

# URL DEVE SER DIFERENTE (URL do Portal Financeiro)
VITE_AUTH0_REDIRECT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
VITE_AUTH0_LOGOUT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
```

### Passo 2: Copiar Implementação do Auth0

Copie os arquivos:
- `frontend/src/lib/auth-context.tsx`
- `frontend/src/pages/auth/` (Login, Callback, etc)
- `frontend/src/hooks/useAuth.ts`

### Passo 3: Configurar Auth0 - Adicionar Redirect URI

Na **Auth0 Dashboard** → **Applications** → **Settings**:

Adicione à lista "Allowed Callback URLs":
```
https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io (logout)
```

### Passo 4: Backend - Adicionar URL do Portal Financeiro a CORS

Arquivo: `backend/main.py` (ou arquivo de config de CORS)

```python
CORS_ORIGINS = [
    "http://localhost:3005",
    "https://app.portalevoque.com",
    "https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io"  # Novo
]
```

### Passo 5: Configurar Variáveis de Ambiente do Backend

Arquivo: `backend/.env`

```env
# Não precisa mudar - Auth0 é o mesmo
AUTH0_DOMAIN=evoqueacademia.us.auth0.com
AUTH0_CLIENT_ID=uvLK21vRoW9NMK7EsI46OosLyi9bPK2z
AUTH0_CLIENT_SECRET=GeaVyti9rlpMkPdl55Bk2zHiES_4HuUal-hIKTyIeWrEZr-SpnJUgKZ6-ZuAWDeh
AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br

# CORS deve incluir o domínio do Portal Financeiro
CORS_ORIGINS=http://localhost:3005,https://app.portalevoque.com,https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
```

---

## 🧪 Teste de SSO

### Teste Local

1. **Terminal 1** - Backend:
```bash
cd backend
python main.py
# Backend roda em http://localhost:3001
```

2. **Terminal 2** - Portal Evoque:
```bash
cd frontend
npm run dev
# Roda em http://localhost:3005
```

3. **Teste**:
   - Acesse `http://localhost:3005`
   - Clique em "Login com Auth0"
   - Faça login
   - Abra outra aba em `http://localhost:3005` (mesma porta = **não funciona** pois é mesma sessão)
   - Para testar em paralelo, use porta diferente (modificar vite.config.ts)

### Teste em Produção

1. **Acesse Portal Evoque**: `https://app.portalevoque.com/`
2. **Faça Login**
3. **Abra Portal Financeiro em nova aba**: `https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/`
4. **Resultado esperado**: Seu usuário já estará logado automaticamente ✓

---

## 🔒 Segurança

### ✅ Implementado

- **Backend faz a troca de código** (`/api/auth/auth0-exchange`)
  - Mais seguro que client-side
  - Client secret nunca é exposto ao navegador
  
- **Validação JWT no Backend**
  - Verifica assinatura RS256
  - Valida audience e issuer
  
- **SessionStorage (não localStorage)**
  - Sessão se encerra ao fechar a aba
  - Mais seguro que localStorage

### ⚠️ Ações Urgentes de Segurança

**CRITICAMENTE IMPORTANTE**:

1. ✅ `.env` foi adicionado ao `.gitignore`
2. ⚠️ **REVOGUE os secrets expostos no Azure Portal**
   - `POWERBI_CLIENT_SECRET`
   - `GRAPH_CLIENT_SECRET`
   - Senha do banco de dados

3. 🔐 **Use Azure Key Vault em produção**
   - Não armazene secrets em `.env`
   - Use variáveis de ambiente do sistema

4. 🔄 **Gere novos secrets**
   - Entre no Azure Portal
   - Regenere as credenciais
   - Atualize no `.env` local
   - NÃO comite no git

---

## 📊 Diagrama de Fluxo Completo

```
┌──────────────────────────────────────────────────────────┐
│                  Primeira Acesso (Sem Login)             │
└──────────────────────────────────────────────────────────┘
                            │
                            ├─ Frontend verifica sessionStorage
                            │
                            ├─ Não encontra sessão
                            │
                            ├─ Tenta Silent Auth (prompt=none)
                            │
                            ├─ Auth0 responde: "Usuário não autenticado"
                            │
                            └─ Usuário vê página de LOGIN

┌──────────────────────────────────────────────────────────┐
│            Após Login no Portal 1 (Evoque)               │
└──────────────────────────────────────────────────────────┘
                            │
                            ├─ Auth0 cria sessão de navegador
                            │  (cookie de domínio Auth0)
                            │
                            └─ Usuário logado em Portal Evoque

┌──────────────────────────────────────────────────────────┐
│         Acessar Portal 2 (Financeiro) - SSO!             │
└──────────────────────────────────────────────────────────┘
                            │
                            ├─ Frontend verifica sessionStorage
                            │
                            ├─ Não encontra sessão local
                            │
                            ├─ Tenta Silent Auth (prompt=none)
                            │
                            ├─ Auth0 verifica seu cookie
                            │  "Ah! Você está logado como user@example.com"
                            │
                            ├─ Auth0 retorna code automaticamente
                            │
                            ├─ Frontend troca code por access_token
                            │
                            ├─ Backend valida e retorna usuário
                            │
                            └─ ✓ Usuário automaticamente logado!
```

---

## 🛠️ Troubleshooting

### "Erro: Silent Authentication Timeout"
- Normal se usuário não está logado no Auth0
- Frontend espera 5 segundos e desiste
- Usuário é apresentado com página de login

### "Error: Invalid redirect_uri"
- Verifique se a URL está registrada em Auth0
- Deve estar em **Applications → Settings → Allowed Callback URLs**

### "Email not verified"
- Se `AUTH0_REQUIRE_EMAIL_VERIFIED=True`, usuário precisa verificar email no Auth0
- Configure como `False` para permitir emails não verificados

### "User not found in database"
- Usuário está no Auth0, mas não foi criado no banco de dados
- Crie o usuário via admin ou API
- Auth0 não cria automaticamente no seu banco

---

## 📚 Referências

- [Auth0 Silent Authentication](https://auth0.com/docs/get-started/authentication-and-authorization-flow/silent-authentication)
- [OAuth 2.0 Authorization Code Flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow)
- [Auth0 JavaScript SPA Documentation](https://auth0.com/docs/quickstart/spa/react/)

---

## ✅ Checklist de Implementação

### Portal Evoque
- [x] `.env` com credenciais Auth0
- [x] `auth-context.tsx` com Silent Authentication
- [x] Backend endpoint `/api/auth/auth0-exchange`
- [x] Backend `.env` com Auth0 config

### Portal Financeiro
- [ ] Criar `.env` com URLs do seu domínio
- [ ] Copiar arquivos de auth
- [ ] Registrar Redirect URI no Auth0
- [ ] Adicionar domínio ao CORS do backend
- [ ] Testar Silent Authentication

---

**Última atualização**: Dezembro 2024
**Status**: ✅ Portal Evoque pronto | ⏳ Portal Financeiro aguardando configuração
