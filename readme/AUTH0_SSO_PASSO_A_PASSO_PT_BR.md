# Guia Rápido: Configurando SSO Entre Portais

## Resumo Executivo

Com a correção implementada, o SSO funciona assim:

```
Usuário faz login em Portal Evoque
        ↓
Auth0 cria sessão
        ↓
Usuário acessa Portal Financeiro
        ↓
Portal Financeiro detecta sessão Auth0 ativa
        ↓
✅ Usuário automaticamente autenticado
```

## O Que Foi Mudado

Seu código anterior tinha o erro **"The state parameter is missing"** porque:

1. ❌ Tentava usar `fetch()` para acessar o endpoint `/authorize` do Auth0
2. ❌ Não armazenava o parâmetro `state` antes do redirecionamento
3. ❌ Gerava `state` com `Math.random()` (inseguro)

**Agora está corrigido:**
- ✅ Usa `window.location.href` para redirecionar (correto)
- ✅ Armazena `state` em `sessionStorage` antes do redirect
- ✅ Gera `state` com `crypto.getRandomValues()` (seguro)
- ✅ Valida `state` no callback para proteção CSRF

## Instruções de Configuração

### Passo 1: Configurar Auth0 - Portal Evoque

1. Abra [Auth0 Dashboard](https://manage.auth0.com)
2. Vá para **Applications → Portal Evoque**
3. Clique em **Settings**
4. Na seção "Application URIs", configure:

   **Callback URLs:**
   ```
   http://localhost:5173/auth/callback
   http://localhost:3005/auth/callback
   https://portalevoque.com/auth/callback
   https://app.portalevoque.com/auth/callback
   https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
   ```

   **Logout URLs:**
   ```
   http://localhost:5173
   http://localhost:3005
   https://portalevoque.com
   https://app.portalevoque.com
   https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
   ```

   **Allowed Web Origins:**
   ```
   http://localhost:5173
   http://localhost:3005
   https://portalevoque.com
   https://app.portalevoque.com
   https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
   ```

5. Clique em **Save**
6. Vá para aba **Connections**
7. Habilite "Username-Password-Authentication"

### Passo 2: Configurar Auth0 - Portal Financeiro

1. Abra [Auth0 Dashboard](https://manage.auth0.com)
2. Vá para **Applications → Portal Financeiro**
3. Clique em **Settings**
4. Na seção "Application URIs", configure:

   **Callback URLs:**
   ```
   http://localhost:5173/auth/callback
   http://localhost:3005/auth/callback
   https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
   ```

   **Logout URLs:**
   ```
   http://localhost:5173
   http://localhost:3005
   https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
   ```

   **Allowed Web Origins:**
   ```
   http://localhost:5173
   http://localhost:3005
   https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
   ```

5. Clique em **Save**
6. Vá para aba **Connections**
7. Habilite "Username-Password-Authentication" **(MESMA que o Portal Evoque)**

### Passo 3: Verificar Variáveis de Ambiente

Frontend deve ter configurado (pode ser na UI, em `.env` ou no servidor):

```env
VITE_AUTH0_DOMAIN=seu-dominio.auth0.com
VITE_AUTH0_CLIENT_ID=seu-client-id
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_AUTH0_AUDIENCE=seu-audience
VITE_AUTH0_LOGOUT_URI=http://localhost:5173
```

**Para Produção:**
```env
VITE_AUTH0_DOMAIN=seu-dominio.auth0.com
VITE_AUTH0_CLIENT_ID=seu-client-id
VITE_AUTH0_REDIRECT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
VITE_AUTH0_AUDIENCE=seu-audience
VITE_AUTH0_LOGOUT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
```

### Passo 4: Verificar Usuários no Banco de Dados

Certifique-se que:
1. Usuário existe no Auth0 (ex: `emerson.silva@academiaevoque.com.br`)
2. Usuário existe no seu banco de dados **com MESMO EMAIL**
3. Usuário tem permissões atribuídas

**Para verificar no Auth0:**
- Dashboard → Users & Roles → Users
- Procure por seu email
- Deve ter `email_verified: true` (se seu sistema exigir)

**Para verificar no banco de dados:**
```sql
SELECT * FROM usuarios WHERE email = 'emerson.silva@academiaevoque.com.br';
```

## Teste Rápido

### Teste Local

1. **Abra o Portal Evoque:**
   ```bash
   cd frontend
   npm run dev
   # Abre em http://localhost:5173
   ```

2. **Clique em "Entrar com Auth0"**

3. **Faça login com seu usuário**
   - Email: seu-email@dominio.com
   - Senha: sua-senha

4. **Você deve ver a página inicial autenticada**

5. **Abra Portal Financeiro (em outra porta):**
   ```bash
   cd portal-financeiro
   VITE_AUTH0_REDIRECT_URI=http://localhost:5174/auth/callback npm run dev -- --port 5174
   ```

6. **Clique em "Entrar com Auth0"**

7. **✅ Você deve ser automaticamente autenticado (SSO)**
   - Não deve pedir email/senha novamente
   - Deve ir direto para página autenticada

### Verificar No Console

Abra `F12` → **Console** e procure por:

```
[AUTH] Redirecting to Auth0 for login
[AUTH] State stored: abc123...
[AUTH] Code and state found
[AUTH] ✓ State parameter validated
[AUTH] ✓ Authentication successful
```

✅ Se vir essas mensagens, está funcionando!

### Se Não Funcionar

1. **Verificar erro "login_required":**
   - Significa: usuário não está logado no Auth0
   - Solução: Faça login em outro portal primeiro

2. **Verificar erro "CORS":**
   - Significa: Allowed Web Origins não configurado
   - Solução: Adicione domínio no Auth0 → Applications → Settings → Allowed Web Origins

3. **Verificar erro "Usuário não encontrado":**
   - Significa: Email do Auth0 não existe no banco de dados
   - Solução: Crie o usuário no banco com mesmo email

4. **Verificar erro "state mismatch":**
   - Significa: sessionStorage está bloqueado
   - Solução: Verifique modo privado/incógnito do navegador

## Fluxo Detalhado do SSO

### Quando Usuário Faz Login no Portal Evoque:

```
1. Usuário clica "Entrar com Auth0"
2. Frontend gera state aleatório seguro
3. Frontend armazena state em sessionStorage
4. Frontend redireciona para Auth0
5. Auth0 mostra tela de login
6. Usuário insere email/senha
7. Auth0 valida credenciais
8. Auth0 cria COOKIE DE SESSÃO em seu navegador
9. Auth0 redireciona para Portal com código de autorização
10. Frontend valida state (proteção CSRF)
11. Frontend envia código para backend trocar por token
12. Backend valida token e busca usuário no BD
13. Frontend salva sessão em sessionStorage
14. ✅ Usuário logado em Portal Evoque
```

### Quando Usuário Acessa Portal Financeiro (SSO):

```
1. Usuário abre Portal Financeiro
2. Frontend verifica se há sessão local (sessionStorage)
3. Não há sessão local (primeira vez neste portal)
4. Usuário clica "Entrar com Auth0"
5. Frontend gera state aleatório seguro
6. Frontend armazena state em sessionStorage
7. Frontend redireciona para Auth0
8. ⭐ AUTH0 VÊ QUE JÁ HÁ COOKIE DE SESSÃO ATIVO
9. Auth0 NÃO mostra tela de login
10. Auth0 automaticamente retorna código de autorização
11. Frontend redireciona para callback com código
12. Frontend valida state
13. Frontend envia código para backend trocar por token
14. Backend valida token e busca usuário no BD
15. Frontend salva sessão em sessionStorage
16. ✅ Usuário logado em Portal Financeiro (SEM INSERIR SENHA)
```

## Diferenças Entre Portais

### Portal Evoque vs Portal Financeiro

| Aspecto | Portal Evoque | Portal Financeiro |
|---------|---------------|-------------------|
| Cliente Auth0 | ✅ Específico | ✅ Específico |
| Banco de Dados | ✅ Mesmo | ✅ Mesmo |
| Domínio | `portalevoque.com` | `qas-frontend-app...` |
| Callback URL | `portalevoque.com/auth/callback` | `qas-frontend-app.../auth/callback` |
| SSO Automático | Não (primeira vez) | ✅ Sim (se logado em Evoque) |

## Segurança Implementada

### 1. Parâmetro State (CSRF)
- ✅ Gerado com `crypto.getRandomValues()` (256 bits)
- ✅ Armazenado em `sessionStorage` (não localStorage)
- ✅ Validado no callback
- ✅ Se não corresponder, autenticação é rejeitada

### 2. Token JWT
- ✅ Validado pelo backend
- ✅ Assinatura verificada
- ✅ Email verificado
- ✅ Usuário e permissões validadas

### 3. Sessão
- ✅ Armazenada em `sessionStorage` (não localStorage)
- ✅ Expira em 24 horas
- ✅ Pode ser revogada manualmente
- ✅ Sincronizada com Auth0

## Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| "The state parameter is missing" | ❌ Erro resolvido (era bug anterior) |
| "login_required" | ✅ Normal - faça login em outro portal |
| "User not found" | Crie usuário no BD com mesmo email Auth0 |
| "CORS error" | Adicione domínio em Auth0 → Allowed Web Origins |
| "No Auth0 session" | Esperado - faça login em outro portal |
| "Usuário está bloqueado" | Desbloqueie em Auth0 ou BD |

## Próximas Melhorias (Futuro)

- [ ] Implementar PKCE (code_challenge) - ainda mais seguro
- [ ] Refresh token automático - renovar sessão sem relogin
- [ ] Silent refresh - renovar token sem interrupção
- [ ] Logout sincronizado - fazer logout em ambos portais
- [ ] Device flow - login em outros dispositivos

## Suporte Técnico

Se tiver problemas, verifique:

1. **Logs do navegador** (F12 → Console)
   - Procure por `[AUTH]` para logs de autenticação
   - Procure por erros em vermelho

2. **Network tab** (F12 → Network)
   - Verifique requisição `/api/auth/auth0-exchange`
   - Status deve ser 200
   - Resposta deve conter `id`, `email`, `nivel_acesso`

3. **Auth0 Logs** (Dashboard → Logs)
   - Verifique se login foi bem sucedido
   - Procure por erros de validação

4. **Banco de Dados**
   - Verifique se usuário existe
   - Verifique se email corresponde exatamente

## Documentação Completa

Para mais detalhes, veja:
- `readme/AUTH0_SSO_SETUP_PT_BR.md` - Configuração completa
- `readme/AUTH0_STATE_PARAMETER_FIX_PT_BR.md` - Detalhes técnicos da correção
