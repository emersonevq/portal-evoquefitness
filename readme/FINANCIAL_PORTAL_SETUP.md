# 🏦 Setup Rápido: Portal Financeiro com SSO

## ⚡ Quick Checklist

Siga estes passos para configurar o Portal Financeiro com SSO.

### Passo 1: Preparar o `.env` do Portal Financeiro

Crie um arquivo `frontend/.env` no projeto do Portal Financeiro com:

```env
# ======== Auth0 Configuration ========
VITE_AUTH0_DOMAIN=evoqueacademia.us.auth0.com
VITE_AUTH0_CLIENT_ID=uvLK21vRoW9NMK7EsI46OosLyi9bPK2z
VITE_AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br

# ======== URLs (DIFERENTES do Portal Evoque!) ========
VITE_AUTH0_REDIRECT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
VITE_AUTH0_LOGOUT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io

# ======== Builder.io (se houver) ========
VITE_PUBLIC_BUILDER_KEY=__BUILDER_PUBLIC_KEY__
```

**⚠️ Importante**: 
- Use o **MESMO** `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID` e `AUTH0_AUDIENCE` do Portal Evoque
- Use **URLs DIFERENTES** específicas do seu Portal Financeiro

---

### Passo 2: Copiar Arquivos de Autenticação

Do Portal Evoque para o Portal Financeiro, copie:

```bash
# Contexto de autenticação (CRÍTICO!)
cp frontend/src/lib/auth-context.tsx → seu-portal-financeiro/src/lib/

# Hook de autenticação (CRÍTICO!)
cp frontend/src/hooks/useAuth.ts → seu-portal-financeiro/src/hooks/

# Páginas de Auth
cp -r frontend/src/pages/auth/ → seu-portal-financeiro/src/pages/

# Componentes de proteção
cp frontend/src/components/RequireLogin.tsx → seu-portal-financeiro/src/components/
```

**Arquivos mínimos necessários**:
- ✅ `src/lib/auth-context.tsx` - SSO Logic
- ✅ `src/hooks/useAuth.ts` - Hook para usar auth
- ✅ `src/pages/auth/Login.tsx` - Página de login
- ✅ `src/pages/auth/Callback.tsx` - Callback do Auth0

---

### Passo 3: Registrar Redirect URI no Auth0

1. Acesse [Auth0 Dashboard](https://manage.auth0.com)
2. Vá para **Applications** → **Evoque Portal** (ou qual for seu App ID)
3. Clique em **Settings**
4. Procure por **Allowed Callback URLs**
5. Adicione:
   ```
   https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
   ```
6. Procure por **Allowed Logout URLs**
7. Adicione:
   ```
   https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
   ```
8. Clique **Save Changes**

---

### Passo 4: Atualizar Backend CORS

O backend já foi atualizado para aceitar o Portal Financeiro!

**Status**: ✅ `FINANCIAL_PORTAL_URL` já configurada

Nenhuma ação necessária, mas você pode verificar:

```python
# backend/main.py (linhas 96-112)
# Verifica se FINANCIAL_PORTAL_URL está presente
_financial_portal_url = os.getenv("FINANCIAL_PORTAL_URL", "").strip()
if _financial_portal_url:
    _allowed_origins.append(_financial_portal_url)
```

---

### Passo 5: Integrar no App.tsx

Seu `frontend/src/App.tsx` deve ter:

```tsx
import { AuthProvider } from "./lib/auth-context";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* suas rotas */}
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```

---

### Passo 6: Proteger Rotas

Use o componente `RequireLogin` para proteger rotas:

```tsx
<Route
  path="/setor/financeiro"
  element={
    <RequireLogin>
      <FinancialPage />
    </RequireLogin>
  }
/>
```

---

## 🧪 Teste

### Local (Desenvolvimento)

```bash
# Terminal 1 - Backend (mesmo backend de ambos portais)
cd backend
python main.py

# Terminal 2 - Portal Evoque
cd portal-evoque/frontend
npm run dev

# Terminal 3 - Portal Financeiro
cd portal-financeiro/frontend
npm run dev
```

**Teste**:
1. Acesse Portal Evoque em `http://localhost:3005`
2. Faça login
3. Abra Portal Financeiro em `http://localhost:3006` (porta diferente)
4. ✓ Você **NÃO** estará logado (sessão é por porta)
5. Faça login no Portal Financeiro
6. ✓ Agora está logado em ambos

---

### Produção/QA

1. **Login no Portal Evoque**:
   - `https://app.portalevoque.com/`
   - Login com Auth0

2. **Abra Portal Financeiro em NOVA ABA**:
   - `https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/`
   - ✓ Deve estar logado automaticamente (SSO!)

---

## 🔄 Como Funciona o SSO

```
┌─────────────────────────────────────────┐
│ Usuário logado em Portal Evoque        │
│ (Auth0 mantém cookie de sessão)        │
└──────────────┬──────────────────────────┘
               │
               ├─ Abre Portal Financeiro
               │
               ├─ Frontend tenta Silent Auth
               │  (usa prompt=none no Auth0)
               │
               ├─ Auth0 verifica cookie
               │  "Ah, você está logado como user@mail.com"
               │
               └─ ✓ Login automático!
```

---

## 🚀 Deploy em Produção

Quando estiver tudo testado:

1. **Configurar URL de produção no `.env`**:
   ```env
   VITE_AUTH0_REDIRECT_URI=https://seu-dominio-producao.com/auth/callback
   VITE_AUTH0_LOGOUT_URI=https://seu-dominio-producao.com
   ```

2. **Registrar em Auth0**:
   - Adicionar URLs de produção em Allowed Callback URLs

3. **Build e Deploy**:
   ```bash
   npm run build
   npm run preview  # Teste local
   # Deploy para seu hosting
   ```

4. **Testar em produção**:
   - Fazer login em um portal
   - Abrir outro em nova aba
   - ✓ SSO funciona!

---

## ⚠️ Problemas Comuns

### "Erro: Invalid redirect_uri"
**Causa**: URL não registrada em Auth0
**Solução**: Vá para Auth0 Dashboard → Allowed Callback URLs → Adicione sua URL

### "Silent Authentication não funciona"
**Causa**: Provavelmente usuário não está logado no Auth0
**Esperado**: Página de login será mostrada
**Solução**: Faça login no Portal Evoque primeiro

### "CORS error"
**Causa**: Backend não aceita seu domínio
**Solução**: Verifique se `FINANCIAL_PORTAL_URL` está configurada no backend

### "User not found in database"
**Causa**: Usuário está em Auth0 mas não no seu banco
**Solução**: Crie o usuário ou implemente auto-provisioning

---

## 📚 Referência Rápida

| Arquivo | Função |
|---------|--------|
| `auth-context.tsx` | Contexto de autenticação com SSO |
| `useAuth.ts` | Hook para acessar dados de usuário |
| `Login.tsx` | Página de login (Auth0) |
| `Callback.tsx` | Página de callback (recebe code do Auth0) |
| `RequireLogin.tsx` | Componente para proteger rotas |

---

## ✅ Checklist Final

- [ ] `.env` criado com credenciais Auth0
- [ ] Arquivos de auth copiados do Portal Evoque
- [ ] Redirect URI registrada no Auth0
- [ ] Backend CORS inclui Portal Financeiro
- [ ] `App.tsx` tem `<AuthProvider>`
- [ ] Rotas protegidas com `<RequireLogin>`
- [ ] Testado em ambiente local
- [ ] Testado em QA/produção
- [ ] SSO funcionando entre portais ✓

---

**Tempo estimado**: 30-45 minutos  
**Dificuldade**: Baixa (copiar & colar + configurar URLs)

