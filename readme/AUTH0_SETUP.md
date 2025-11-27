# Integração Auth0 + Microsoft Office 365

## Status: ✅ Implementado

A autenticação da aplicação foi integrada com Auth0 para usar Microsoft Office 365 como provedor de identidade.

---

## 📋 O que foi implementado

### Frontend

- ✅ Instalação da biblioteca `@auth0/auth0-react`
- ✅ Wrapper `Auth0Provider` em `main.tsx`
- ✅ Atualização do `auth-context.tsx` para usar Auth0
- ✅ Nova página de login com botão "Entrar com Microsoft"
- ✅ Arquivo `.env` com credenciais Auth0
- ✅ Arquivo `.env.local` para desenvolvimento local

### Backend

- ✅ Novo endpoint `/api/usuarios/auth0-login` para validar usuários
- ✅ Atualização de `backend/env.py` com credenciais Auth0
- ✅ Adição de dependências ao `requirements.txt`

---

## 🔐 Credenciais Auth0

As credenciais foram configuradas no Auth0 Dashboard:

### Configuração Auth0

```
Domínio: evoqueacademia.us.auth0.com
Client ID: uvLK21vRoW9NMK7EsI46OosLyi9bPK2z
Audience: https://erp-api.evoquefitness.com.br
```

### Conexão Microsoft

```
Nome: Portalevoquefitness
Tipo: Azure AD Enterprise
Tenant: 9f45f492-87a3-4214-862d-4c0d080aa136
```

---

## 🚀 Fluxo de Autenticação

### 1. Usuário acessa a aplicação

- URL: `https://portalevoque.com`
- Vê tela de login com botão "Entrar com Microsoft"

### 2. Clica em "Entrar com Microsoft"

- Frontend redireciona para Auth0
- Auth0 redireciona para Microsoft Login

### 3. Usuário faz login com email corporativo

- Email: `usuario@academiaevoque.com.br`
- Senha: Credenciais da conta Microsoft

### 4. Microsoft valida e retorna para Auth0

- Auth0 executa action "Add Email to Token"
- Email é adicionado ao JWT

### 5. Retorno para a aplicação

- Frontend recebe `id_token` e `access_token`
- Frontend envia `/api/usuarios/auth0-login` com o email

### 6. Backend valida email no banco

- Se email existe no banco:
  - ✅ Login bem-sucedido
  - Usuário é redirecionado para dashboard
- Se email NÃO existe:
  - ❌ Erro 403 - Acesso Negado
  - Mensagem: "Email não encontrado no sistema"

---

## 📝 Variáveis de Ambiente

### Frontend (.env ou .env.local)

```env
VITE_AUTH0_DOMAIN=evoqueacademia.us.auth0.com
VITE_AUTH0_CLIENT_ID=uvLK21vRoW9NMK7EsI46OosLyi9bPK2z
VITE_AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
VITE_AUTH0_REDIRECT_URI=http://localhost:5173  # Para desenvolvimento
# Ou: https://portalevoque.com  # Para produção
```

### Backend (backend/env.py)

```python
AUTH0_DOMAIN=evoqueacademia.us.auth0.com
AUTH0_AUDIENCE=https://erp-api.evoquefitness.com.br
AUTH0_ISSUER_BASE_URL=https://evoqueacademia.us.auth0.com
```

---

## 🔧 Como testar

### 1. Ambiente de Desenvolvimento

```bash
# Frontend
cd frontend
npm run dev

# Backend
cd backend
python main.py
```

### 2. Acessar a aplicação

- URL: `http://localhost:5173`
- Clique em "Entrar com Microsoft"
- Use credenciais de teste do Azure AD

### 3. Para produção

- Atualize `VITE_AUTH0_REDIRECT_URI` para `https://portalevoque.com`
- Certifique-se que as URLs estão configuradas no Auth0 Dashboard

---

## 📚 Endpoints

### POST `/api/usuarios/auth0-login`

**Descrição**: Valida token Auth0 e faz login do usuário

**Headers**:

```
Authorization: Bearer {token_jwt}
Content-Type: application/json
```

**Body**:

```json
{
  "email": "usuario@academiaevoque.com.br",
  "name": "Nome do Usuário"
}
```

**Response (200 OK)**:

```json
{
  "id": 123,
  "nome": "João",
  "sobrenome": "Silva",
  "usuario": "joao.silva",
  "email": "joao.silva@academiaevoque.com.br",
  "nivel_acesso": "user",
  "setores": ["ti", "compras"],
  "bi_subcategories": null,
  "alterar_senha_primeiro_acesso": false
}
```

**Response (403 Forbidden)**:

```json
{
  "detail": "Usuário com email 'xxx@xxx.com' não encontrado no sistema."
}
```

---

## 🛠️ Manutenção

### Adicionar novo usuário

1. Crie o usuário normalmente no banco de dados
2. Use o mesmo email da conta Microsoft Office 365
3. Usuário poderá fazer login com "Entrar com Microsoft"

### Remover acesso

1. Bloqueie o usuário via admin panel
2. Ou delete o usuário do banco
3. Logout automático será acionado

### Alterar configurações Auth0

1. Acesse o Auth0 Dashboard
2. Vá para a aplicação "Portal Evoque Fitness"
3. Atualize as credenciais se necessário

---

## ⚠️ Observações Importantes

1. **Email único**: O email do usuário no banco deve ser o mesmo da conta Microsoft
2. **Bloqueio de usuário**: Usuários bloqueados não conseguem fazer login
3. **Primeiro acesso**: Senhas legadas não são mais necessárias
4. **Segurança**: Nunca commit das credenciais Auth0 no repositório
5. **Token expiração**: Tokens Auth0 expiram em 1 hora (configurável)

---

## 🔗 Referências

- [Auth0 Documentation](https://auth0.com/docs)
- [Auth0 React SDK](https://auth0.com/docs/libraries/auth0-react)
- [Azure AD Enterprise Connection](https://auth0.com/docs/protocols/saml/saml-configuration/microsoft-azure-active-directory)

---

## 📞 Suporte

Para problemas com autenticação:

1. Verifique se o email está registrado no banco
2. Verifique se o usuário não está bloqueado
3. Confirme as credenciais Auth0 em `frontend/.env`
4. Verifique os logs do backend para erros

---

**Última atualização**: Dezembro 2024
