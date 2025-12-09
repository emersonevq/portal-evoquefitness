# Fluxo Completo de Autenticação Auth0

## 🔐 Fluxo OAuth2 Authorization Code Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   FRONTEND (React + Vite)                            │
│                                                                      │
│  1. Usuário clica "Entrar com Auth0" em /auth0/login                │
│     ↓                                                                │
│  2. loginWithAuth0() é chamado                                       │
│     ↓                                                                │
│  3. Redireciona para Auth0:                                         │
│     https://evoqueacademia.us.auth0.com/authorize?                 │
│       response_type=code&                                           │
│       client_id=uvLK21vRoW9NMK7EsI46OosLyi9bPK2z&                 │
│       redirect_uri=http://localhost:5173/auth/callback&            │
│       scope=openid profile email offline_access&                   │
│       audience=https://erp-api.evoquefitness.com.br                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   AUTH0 (evoqueacademia.us.auth0.com)               │
│                                                                      │
│  4. Usuário faz login no Auth0                                      │
│  5. Auth0 valida credenciais                                        │
│  6. Auth0 redireciona para callback com código:                    │
│     http://localhost:5173/auth/callback?code=...&state=...         │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│               FRONTEND CALLBACK (Callback.tsx)                       │
│                                                                      │
│  7. Recebe code do querystring                                      │
│  8. handleAuth0Callback(code, state) é chamado                     │
│  9. Envia POST para Auth0 token endpoint:                          │
│     POST https://evoqueacademia.us.auth0.com/oauth/token           │
│     {                                                               │
│       client_id: "uvLK21vRoW9NMK7EsI46OosLyi9bPK2z",              │
│       code: code,                                                   │
│       grant_type: "authorization_code",                            │
│       redirect_uri: "http://localhost:5173/auth/callback"          │
│     }                                                               │
│     ↓                                                                │
│  10. Recebe access_token e refresh_token                            │
│  11. Armazena em localStorage                                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   BACKEND VALIDATION                                 │
│                                                                      │
│  12. Frontend valida token com backend:                             │
│      POST /api/auth/auth0-login                                    │
│      Authorization: Bearer {access_token}                           │
│      ↓                                                               │
│  13. Backend valida JWT:                                            │
│      - Fetch JWKS de Auth0                                         │
│      - Extrai header.kid                                           │
│      - Obtém chave pública                                         │
│      - Valida assinatura RS256                                     │
│      - Valida audience                                             │
│      - Valida issuer                                               │
│      ↓                                                               │
│  14. Backend procura usuário no banco by email                      │
│  15. Valida se usuário está bloqueado                               │
│  16. Retorna dados do usuário                                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│              FRONTEND SESSION (auth-context.tsx)                     │
│                                                                      │
│  17. Armazena dados do usuário em:                                 │
│      - sessionStorage (evoque-fitness-auth)                        │
│      - localStorage (auth0_access_token)                           │
│      ↓                                                               │
│  18. Atualiza estado isAuthenticated = true                         │
│  19. Redireciona para URL original ou /                            │
│      (capturada em auth0_redirect_after_login)                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 📁 Arquivos Modificados/Criados

### Backend

```
backend/
├── auth0/                          # ✨ NOVA PASTA
│   ├── __init__.py                # Inicialização do módulo
│   ├── config.py                  # Configurações Auth0
│   ├── validator.py               # Validação JWT
│   ├── management.py              # Client Management API
│   └── routes.py                  # Rotas de autenticação
└── main.py                        # ✏️ ATUALIZADO (import auth0_router)
```

### Frontend

```
frontend/src/
├── lib/
│   └── auth-context.tsx           # ✏️ COMPLETAMENTE REESCRITO
├── pages/auth/
│   ├── Login.tsx                  # ✏️ ATUALIZADO (Auth0 button)
│   └── Callback.tsx               # ✨ NOVO (Auth0 callback)
└── App.tsx                        # ✏️ ATUALIZADO (import Callback, nova rota)
  main.tsx                         # ✏️ ATUALIZADO (import Callback, nova rota)
```

### Configuração

```
backend/
└── env.py                         # ✏️ ATUALIZADO (Auth0 M2M credentials)

frontend/
└── .env.example                   # ✨ NOVO (variáveis de ambiente)
```

## 🔑 Variáveis de Ambiente

### Backend (env.py)

```python
# Auth0 Configuration
AUTH0_DOMAIN=evoqueacademia.us.auth0.com
AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
AUTH0_CLIENT_ID=                    # (não usado por enquanto)
AUTH0_CLIENT_SECRET=                # (não usado por enquanto)

# Machine-to-Machine (M2M) Credentials
AUTH0_M2M_CLIENT_ID=XzX8v2bRdjMufvVFcFbrtZXmbn2xBgdE
AUTH0_M2M_CLIENT_SECRET=GiSRQOv7Vyh2Fb2mWz6_dbo5NYBKZO9qBTeQPOwH-erwzjqF3EGyWR861-p-GYKb
```

### Frontend (.env.local)

```bash
VITE_AUTH0_DOMAIN=evoqueacademia.us.auth0.com
VITE_AUTH0_CLIENT_ID=uvLK21vRoW9NMK7EsI46OosLyi9bPK2z
VITE_AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_AUTH0_LOGOUT_URI=http://localhost:5173
```

## 🛣️ Rotas Criadas

### Frontend

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/auth0/login` | Login.tsx | Página de login com botão Auth0 |
| `/auth/callback` | Callback.tsx | Callback do Auth0 com tratamento de código |

### Backend

| Rota | Método | Descrição |
|------|--------|-----------|
| `/api/auth/auth0-login` | POST | Valida token e faz login |
| `/api/auth/auth0-user` | GET | Obtém usuário autenticado |

## 🔄 Contexto de Autenticação (auth-context.tsx)

### Funções Disponíveis

```typescript
const {
  user,                    // Usuário autenticado
  isAuthenticated,         // Boolean
  isLoading,              // Boolean
  login,                  // (email, password) => Promise
  logout,                 // () => Promise
  loginWithAuth0,         // () => Promise (redireciona para Auth0)
  getAccessToken,         // () => string | null
} = useAuthContext();
```

### Propriedades do Usuário

```typescript
interface User {
  id?: number;
  email: string;
  name: string;
  firstName?: string;
  lastName?: string;
  nivel_acesso?: string;
  setores?: string[];
  bi_subcategories?: string[] | null;
  loginTime: number;
}
```

## 🧪 Teste Manual

### 1. Iniciar Aplicação

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Acessar Aplicação

1. Abrir `http://localhost:5173`
2. Clicar em um setor ou botão "Fazer login"
3. Será redirecionado para `/auth0/login`
4. Clicar em "Entrar com Auth0"
5. Será redirecionado para Auth0
6. Fazer login com credenciais de teste
7. Auth0 redirecionará para `/auth/callback?code=...&state=...`
8. App processará o código e redirecionará para a página original

### 3. Verificar Tokens

No console do navegador (F12):

```javascript
// Ver token
console.log(localStorage.getItem('auth0_access_token'));

// Decodificar (para debug)
const token = localStorage.getItem('auth0_access_token');
const decoded = JSON.parse(atob(token.split('.')[1]));
console.log(decoded);

// Ver dados do usuário
console.log(JSON.parse(sessionStorage.getItem('evoque-fitness-auth')));
```

## 🔒 Segurança

### ✅ Implementado

- [x] JWT validation com RS256
- [x] JWKS caching para performance
- [x] Token storage em localStorage
- [x] Audience validation
- [x] Issuer validation
- [x] User validation in database
- [x] HTTPS redirect (em produção)

### ⚠️ Recomendações

- [ ] Implementar refresh token rotation
- [ ] Implementar logout com revogação de token
- [ ] Adicionar rate limiting no backend
- [ ] Adicionar CORS configuration
- [ ] Usar httpOnly cookies em produção
- [ ] Implementar token expiration handling

## 📝 Próximas Tarefas

1. **Teste do fluxo completo**
   - [ ] Verificar login
   - [ ] Verificar dados do usuário
   - [ ] Verificar logout
   - [ ] Verificar redirecionamento

2. **Integração com setores**
   - [ ] Atualizar componentes que usam `loginWithMicrosoft`
   - [ ] Testar acesso a setores após login
   - [ ] Verificar permissões por setor

3. **Produção**
   - [ ] Configurar URLs de callback em produção
   - [ ] Configurar CORS
   - [ ] Implementar refresh token
   - [ ] Testar em staging
   - [ ] Deploy em produção

## 🆘 Problemas Comuns

| Problema | Solução |
|----------|---------|
| "Invalid Redirect URI" | Verifique URLs no Auth0 Dashboard |
| "undefined is not a function" | Verifique import de `useAuthContext` |
| "JWKS fetch failed" | Verifique conexão com Auth0 |
| "Token verification failed" | Verifique AUTH0_AUDIENCE |
| "User not found" | Crie usuário no banco ou Auth0 |
| "Callback não funciona" | Verifique rota `/auth/callback` existe |

## 📚 Referências

- Auth0 Docs: https://auth0.com/docs
- OAuth2 Flow: https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow
- JWKS: https://auth0.com/docs/get-started/backend-integration/jwks-endpoint
