# Implementação Completa do Auth0 no Portal Evoque

## Índice
1. [Criação de Conta no Auth0](#criação-de-conta-no-auth0)
2. [Configuração da Aplicação](#configuração-da-aplicação)
3. [Criação de Usuários](#criação-de-usuários)
4. [Configuração de Permissões e Roles](#configuração-de-permissões-e-roles)
5. [Configuração do Redirecionamento](#configuração-do-redirecionamento)
6. [Integração no Frontend](#integração-no-frontend)
7. [Integração no Backend](#integração-no-backend)
8. [Variáveis de Ambiente](#variáveis-de-ambiente)
9. [Teste da Implementação](#teste-da-implementação)

---

## 1. Criação de Conta no Auth0

### Passo 1: Acessar Auth0
1. Acesse **https://auth0.com**
2. Clique em **"Sign Up"** (ou **"Get Started"** se já tem conta)
3. Escolha sua preferência de login (email, Google, GitHub, Microsoft)

### Passo 2: Criar Tenant
1. Após login, você será direcionado para criar um **Tenant** (seu espaço de trabalho)
2. Preencha os dados:
   - **Tenant Name**: `evoque-portal` (ou similar)
   - **Tenant Region**: Escolha a região mais próxima (ex: `us-east-1` para latência menor)
   - **Tenant Type**: Escolha de acordo com plano (Free funciona para teste)

3. Clique em **"Create"**

### Passo 3: Acessar Dashboard
1. Após criação, você será automaticamente levado ao **Auth0 Dashboard**
2. Salve a URL do seu tenant: `https://YOUR_TENANT_NAME.us.auth0.com`
   - Exemplo: `https://evoque-portal.us.auth0.com`

---

## 2. Configuração da Aplicação

### Passo 1: Criar Aplicação
1. No Dashboard, acesse **Applications → Applications** (menu esquerdo)
2. Clique em **"Create Application"**
3. Preencha:
   - **Name**: `Portal Evoque Frontend`
   - **Application Type**: Escolha **"Single Page Application"** (para React)
   - Clique em **"Create"**

### Passo 2: Obter Credenciais
Na página da aplicação, você verá:

```
Domain:       evoque-portal.us.auth0.com
Client ID:    YOUR_CLIENT_ID_HERE
Client Secret: YOUR_CLIENT_SECRET_HERE
```

**⚠️ Copie e guarde esses valores com segurança!**

### Passo 3: Configurar URLs de Redirect

Ainda na página da aplicação, acesse a aba **"Settings"** e procure por:

**Allowed Callback URLs:**
```
http://localhost:5173/auth/callback
https://seu-dominio-producao.com/auth/callback
```

**Allowed Logout URLs:**
```
http://localhost:5173/
https://seu-dominio-producao.com/
```

**Allowed Web Origins:**
```
http://localhost:5173
https://seu-dominio-producao.com
```

Clique em **"Save Changes"**

### Passo 4: Configurar API

1. Acesse **Applications → APIs** (menu esquerdo)
2. Clique em **"Create API"**
3. Preencha:
   - **Name**: `Portal Evoque API`
   - **Identifier**: `https://erp-api.evoquefitness.com.br` (mesmo do projeto atual)
   - **Signing Algorithm**: RS256
4. Clique em **"Create"**

---

## 3. Criação de Usuários

### Opção A: Via Dashboard (Manual)

1. Acesse **User Management → Users** (menu esquerdo)
2. Clique em **"Create User"**
3. Preencha:
   - **Email**: usuario@academiaevoque.com.br
   - **Password**: Gere uma senha forte
   - **Confirm Password**: Repita a senha
   - **Connection**: `Username-Password-Authentication`
4. Clique em **"Create"**

### Opção B: Via API (Automatizado)

Use a API de Management do Auth0 para criar usuários programaticamente:

```bash
# Obter token de Management API
curl --request POST \
  --url https://YOUR_TENANT.us.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id": "YOUR_MANAGEMENT_API_CLIENT_ID",
    "client_secret": "YOUR_MANAGEMENT_API_CLIENT_SECRET",
    "audience": "https://YOUR_TENANT.us.auth0.com/api/v2/",
    "grant_type": "client_credentials"
  }'

# Criar usuário
curl --request POST \
  --url https://YOUR_TENANT.us.auth0.com/api/v2/users \
  --header 'authorization: Bearer ACCESS_TOKEN' \
  --header 'content-type: application/json' \
  --data '{
    "email": "usuario@academiaevoque.com.br",
    "password": "Senha123!",
    "connection": "Username-Password-Authentication",
    "user_metadata": {
      "nome": "João Silva",
      "sobrenome": "Santos"
    }
  }'
```

### Criar Management API Application

Para usar a API programaticamente:

1. Acesse **Applications → Applications**
2. Clique em **"Create Application"**
3. Escolha **Application Type**: `Machine to Machine Applications`
4. **Name**: `Portal Evoque Backend`
5. Clique em **"Create"**
6. Na próxima tela, autorize para **Auth0 Management API** com escopos:
   - `create:users`
   - `read:users`
   - `update:users`
   - `delete:users`
   - `create:user_blocks`
   - `read:user_blocks`
7. Copie o **Client ID** e **Client Secret**

---

## 4. Configuração de Permissões e Roles

### Passo 1: Criar Roles

1. Acesse **User Management → Roles** (menu esquerdo)
2. Clique em **"Create Role"**
3. Crie as seguintes roles:

```
Role: ADMIN
Description: Administrador do Sistema

Role: TI
Description: Gestor do Portal de TI

Role: FINANCEIRO
Description: Gestor do Portal Financeiro

Role: MANUTENCAO
Description: Gestor do Portal de Manutenção

Role: BI
Description: Gestor do BI
```

### Passo 2: Criar Permissões

1. Acesse **User Management → Permissions** (menu esquerdo)
2. Clique em **"Create Permission"**
3. Crie as permissões:

```
Nome: read:chamados
API: Portal Evoque API
Description: Ler chamados

Nome: create:chamado
API: Portal Evoque API
Description: Criar chamado

Nome: update:chamado
API: Portal Evoque API
Description: Atualizar chamado

Nome: delete:chamado
API: Portal Evoque API
Description: Deletar chamado

Nome: read:dashboard
API: Portal Evoque API
Description: Acessar dashboard

Nome: manage:users
API: Portal Evoque API
Description: Gerenciar usuários
```

### Passo 3: Associar Permissões às Roles

1. Volte para **User Management → Roles**
2. Clique em cada role criada
3. Acesse a aba **"Permissions"**
4. Clique em **"Add Permissions"**
5. Associe as permissões apropriadas para cada role

Exemplo:
- **ADMIN**: Todas as permissões
- **TI**: read:chamados, create:chamado, update:chamado, read:dashboard
- **FINANCEIRO**: read:dashboard, read:chamados
- **BI**: read:dashboard

### Passo 4: Atribuir Roles aos Usuários

1. Acesse **User Management → Users**
2. Clique no usuário desejado
3. Acesse a aba **"Roles"**
4. Clique em **"Add Roles"**
5. Selecione as roles apropriadas
6. Clique em **"Add"**

---

## 5. Configuração do Redirecionamento

### Passo 1: Entender o Fluxo

```
1. Usuário acessa /auth0/login
2. Clica em "Entrar com Auth0"
3. Redireciona para Auth0 login page
4. Auth0 redireciona de volta para /auth/callback
5. Frontend obtém tokens
6. Backend valida tokens
7. Redireciona para URL original ou /
```

### Passo 2: Configurar Rules (Opcional mas Recomendado)

No Auth0 Dashboard:

1. Acesse **Actions → Flows** (ou **Rules** se em versão anterior)
2. **"New Action"** → **"Login/Post Login"**
3. **Name**: `Add Custom Claims`
4. Adicione o código:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://erp-api.evoquefitness.com.br';
  
  // Adicionar roles como claims customizados
  if (event.authorization) {
    api.idToken.setCustomClaim(`${namespace}/roles`, event.authorization.roles);
    api.idToken.setCustomClaim(`${namespace}/permissions`, event.authorization.permissions);
  }
  
  // Adicionar dados customizados do usuário
  api.idToken.setCustomClaim(`${namespace}/nome`, event.user.user_metadata?.nome || '');
  api.idToken.setCustomClaim(`${namespace}/sobrenome`, event.user.user_metadata?.sobrenome || '');
};
```

5. Clique em **"Save"**
6. Vá para **Flows → Login** e arraste a action para o fluxo

---

## 6. Integração no Frontend

### Passo 1: Instalar Dependências

```bash
cd frontend
npm install @auth0/auth0-react
```

### Passo 2: Criar Auth0 Context (frontend/src/lib/auth0-config.ts)

```typescript
import { Auth0Client } from '@auth0/auth0-spa-js';

const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  authorizationParams: {
    redirect_uri: window.location.origin + '/auth/callback',
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
    scope: 'openid profile email offline_access',
  },
};

export default auth0Config;
```

### Passo 3: Atualizar AuthProvider (frontend/src/lib/auth-context.tsx)

Substitua o contexto atual pelo novo com suporte a Auth0.

### Passo 4: Criar Página de Callback (frontend/src/pages/auth/Callback.tsx)

```typescript
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export default function Callback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const redirect = searchParams.get('redirect') || '/';
    // O handling do callback é feito no Auth0Provider
    setTimeout(() => {
      navigate(redirect);
    }, 1000);
  }, [navigate, searchParams]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-muted-foreground">Redirecionando...</p>
      </div>
    </div>
  );
}
```

### Passo 5: Adicionar Rota de Callback (frontend/src/App.tsx)

```tsx
<Route path="/auth/callback" element={<Callback />} />
```

---

## 7. Integração no Backend

### Passo 1: Instalar Dependências

```bash
cd backend
pip install python-jose pyjwt requests
```

### Passo 2: Criar Validação de Token (backend/core/auth0_validator.py)

```python
import os
import requests
from jose import jwt, JWTError
from functools import wraps
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials

AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
AUTH0_AUDIENCE = os.getenv('AUTH0_AUDIENCE')
AUTH0_ISSUER = f'https://{AUTH0_DOMAIN}/'

def get_public_keys():
    """Obtém chaves públicas do Auth0"""
    jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
    response = requests.get(jwks_url)
    return response.json()

def verify_token(token: str) -> dict:
    """Valida token JWT do Auth0"""
    try:
        # Obter header do token
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        
        # Obter chaves públicas
        jwks = get_public_keys()
        key = None
        for k in jwks.get('keys', []):
            if k.get('kid') == kid:
                key = k
                break
        
        if not key:
            raise HTTPException(status_code=401, detail='Token inválido')
        
        # Decodificar e validar token
        payload = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=AUTH0_AUDIENCE,
            issuer=AUTH0_ISSUER,
        )
        return payload
        
    except JWTError:
        raise HTTPException(status_code=401, detail='Token inválido')

security = HTTPBearer()

async def verify_auth0_token(credentials: HTTPAuthCredentials = Depends(security)):
    """Dependência para verificar token em rotas protegidas"""
    token = credentials.credentials
    return verify_token(token)
```

### Passo 3: Atualizar Rota de Login (backend/ti/api/usuarios.py)

```python
from core.auth0_validator import verify_token, verify_auth0_token
from fastapi import Depends

@router.post("/auth0-login")
def auth0_login(
    token_payload: dict = Depends(verify_auth0_token),
    db: Session = Depends(get_db)
):
    """
    Valida token JWT do Auth0 e faz login do usuário
    """
    try:
        email = token_payload.get('email') or token_payload.get('sub')
        name = token_payload.get('name', '')
        
        if not email:
            raise HTTPException(status_code=400, detail='Email não fornecido')
        
        # Buscar usuário no banco
        from ti.models import User
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=403,
                detail=f"Usuário com email '{email}' não encontrado no sistema."
            )
        
        if user.bloqueado:
            raise HTTPException(
                status_code=403,
                detail='Usuário bloqueado. Contate o administrador.'
            )
        
        # Preparar resposta
        setores_list = []
        if getattr(user, "_setores", None):
            try:
                setores_list = json.loads(getattr(user, "_setores", "[]"))
            except:
                setores_list = []
        
        bi_subcategories_list = None
        if getattr(user, "_bi_subcategories", None):
            try:
                bi_subcategories_list = json.loads(
                    getattr(user, "_bi_subcategories", "null")
                )
            except:
                bi_subcategories_list = None
        
        return {
            'id': user.id,
            'nome': user.nome,
            'sobrenome': user.sobrenome,
            'email': user.email,
            'nivel_acesso': user.nivel_acesso,
            'setores': setores_list,
            'bi_subcategories': bi_subcategories_list,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Erro ao autenticar com Auth0: {str(e)}'
        )
```

---

## 8. Variáveis de Ambiente

### Frontend (.env ou .env.local)

```env
# Auth0 Configuration
VITE_AUTH0_DOMAIN=evoque-portal.us.auth0.com
VITE_AUTH0_CLIENT_ID=YOUR_CLIENT_ID_HERE
VITE_AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/auth/callback
```

### Backend (.env)

```env
# Auth0 Configuration
AUTH0_DOMAIN=evoque-portal.us.auth0.com
AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
AUTH0_CLIENT_ID=YOUR_CLIENT_ID_HERE
AUTH0_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
```

---

## 9. Teste da Implementação

### Teste Local

1. **Inicie o backend:**
   ```bash
   cd backend
   python main.py
   ```

2. **Inicie o frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Acesse a aplicação:**
   - `http://localhost:5173`
   - Clique em "Fazer login"
   - Escolha um setor para redirecionar via Auth0
   - Você será redirecionado para Auth0
   - Faça login com suas credenciais
   - Você voltará à aplicação autenticado

### Verificar Tokens

No console do navegador (F12 → Console):

```javascript
// Obter token do localStorage
const token = localStorage.getItem('auth0.access_token');
console.log(token);

// Decodificar (para debug apenas)
const decoded = JSON.parse(atob(token.split('.')[1]));
console.log(decoded);
```

### Troubleshooting

| Erro | Solução |
|------|---------|
| "Invalid Redirect URI" | Verifique as URLs de callback nas settings do Auth0 |
| "Invalid Audience" | Certifique que `AUTH0_AUDIENCE` é igual ao identificador da API |
| "User not found" | O usuário não está registrado. Crie via dashboard do Auth0 ou via API |
| "CORS Error" | Configure CORS no backend para aceitar origem do frontend |

---

## Próximos Passos

1. ✅ Criar conta e tenant no Auth0
2. ✅ Configurar aplicação e API
3. ✅ Criar usuários de teste
4. ✅ Configurar roles e permissões
5. ✅ Atualizar frontend com Auth0 SDK
6. ✅ Atualizar backend com validação de token
7. ✅ Configurar variáveis de ambiente
8. ✅ Testar fluxo de login
9. ⏳ Implementar logout
10. ⏳ Implementar refresh de tokens
11. ⏳ Configurar acesso por role/permissões

---

## Referências Úteis

- **Auth0 Dashboard:** https://manage.auth0.com
- **Auth0 Documentation:** https://auth0.com/docs
- **Auth0 React SDK:** https://github.com/auth0/auth0-react
- **JWKS Endpoint:** `https://YOUR_TENANT.us.auth0.com/.well-known/jwks.json`
- **User Management API:** https://auth0.com/docs/api/management/v2

