# Auth0 Quick Start Guide

## ✅ O que foi feito?

Implementação completa do Auth0 OAuth2 no projeto:

- ✅ Backend Auth0 com validação JWT
- ✅ Frontend com Auth0 SDK customizado
- ✅ Fluxo OAuth2 Authorization Code Flow
- ✅ Variáveis de ambiente configuradas
- ✅ Rotas de callback implementadas

## 🚀 Para começar a testar:

### 1. Verifique as variáveis de ambiente

**Backend** (backend/env.py já está configurado):

```
AUTH0_DOMAIN=evoqueacademia.us.auth0.com
AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
AUTH0_M2M_CLIENT_ID=XzX8v2bRdjMufvVFcFbrtZXmbn2xBgdE
AUTH0_M2M_CLIENT_SECRET=GiSRQOv7Vyh2Fb2mWz6_dbo5NYBKZO9qBTeQPOwH-erwzjqF3EGyWR861-p-GYKb
```

**Frontend** (criar arquivo `frontend/.env.local`):

```env
VITE_AUTH0_DOMAIN=evoqueacademia.us.auth0.com
VITE_AUTH0_CLIENT_ID=uvLK21vRoW9NMK7EsI46OosLyi9bPK2z
VITE_AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_AUTH0_LOGOUT_URI=http://localhost:5173
```

### 2. Iniciar a aplicação

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm install  # Se não tiver feito ainda
npm run dev
```

### 3. Testar o fluxo

1. Abra http://localhost:5173
2. Clique em qualquer setor ou "Fazer login"
3. Clique em "Entrar com Auth0"
4. Faça login com suas credenciais Auth0
5. Você será redirecionado para a página

## 📋 Rotas Implementadas

### Frontend

- `GET /auth0/login` - Página de login
- `GET /auth/callback` - Callback do Auth0

### Backend

- `POST /api/auth/auth0-login` - Validar token JWT
- `GET /api/auth/auth0-user` - Obter usuário autenticado

## 🔐 Segurança

O fluxo usa:

- ✅ OAuth2 Authorization Code Flow
- ✅ JWT com assinatura RS256
- ✅ JWKS validation (chaves públicas)
- ✅ Audience validation
- ✅ Issuer validation
- ✅ User validation no banco de dados

## 🐛 Debug

### Ver logs do backend

```
# Procure por:
✅ Auth0 Management API token obtained
✅ User syncing...
❌ Erros de validação
```

### Ver tokens no navegador

```javascript
// Console do navegador (F12)
localStorage.getItem("auth0_access_token");
JSON.parse(sessionStorage.getItem("evoque-fitness-auth"));
```

## 📂 Arquivos Modificados

```
backend/
├── auth0/ (nova pasta com 4 arquivos)
└── main.py

frontend/src/
├── lib/auth-context.tsx
├── pages/auth/Callback.tsx (novo)
├── pages/auth/Login.tsx
├── App.tsx
└── main.tsx

Configuração:
├── backend/env.py
└── frontend/.env.example
```

## ❓ Problemas?

| Erro               | Verificar                                   |
| ------------------ | ------------------------------------------- |
| Login não funciona | Variáveis de ambiente                       |
| Callback 404       | Rota `/auth/callback` em App.tsx e main.tsx |
| Token inválido     | AUTH0_AUDIENCE no backend                   |
| CORS error         | CORS configuration no backend               |
| User not found     | Usuário no banco com email correto          |

## 📚 Documentação Completa

- `readme/AUTH0_IMPLEMENTACAO_COMPLETA.md` - Guia detalhado de setup
- `readme/AUTH0_FLUXO_COMPLETO.md` - Diagrama do fluxo OAuth2
- `readme/AUTH0_IMPLEMENTACAO_STATUS.md` - Status e próximas tarefas

## 🎯 Próximos Passos

1. Testar login/logout completo
2. Testar acesso a setores
3. Configurar em staging
4. Deploy em produção

---

**Credenciais Auth0 já estão configuradas. Basta iniciar a aplicação e testar!**
