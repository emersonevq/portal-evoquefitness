# Integração Frontend - Módulo SLA

Guia completo para integrar os componentes de SLA no frontend React.

## Estrutura de Arquivos Criados

```
frontend/src/
├── services/
│   └── slaService.ts              # Service para API REST
├── components/
│   ├── SlaIndicator.tsx           # Componente de status
│   ├── SlaProgressBar.tsx         # Barra de progresso
│   ├── SlaInfoDisplay.tsx         # Exibição detalhada
│   ├── SlaMetricsCard.tsx         # Card de métricas
│   └── SlaDetailsSection.tsx      # Seção integrada em chamados
└── pages/
    ├── SlaDashboard.tsx           # Dashboard completo
    └── SlaConfig.tsx              # Configurações (admin)
```

## 1. Instalação de Dependências

Verificar que as dependências estão instaladas:

```bash
cd frontend
npm install
```

Dependências necessárias (já devem estar):
- `@tanstack/react-query` - Cache de dados
- `framer-motion` - Animações
- `lucide-react` - Ícones
- `tailwindcss` - Estilos

## 2. Integração no Roteamento

Adicionar as rotas de SLA no arquivo de roteamento principal:

```typescript
// frontend/src/App.tsx ou router.ts
import { SlaDashboard } from "@/pages/SlaDashboard";
import { SlaConfig } from "@/pages/SlaConfig";

const routes = [
  // ... outras rotas
  {
    path: "/sla/dashboard",
    element: <SlaDashboard />,
    meta: { title: "Dashboard SLA", requiredRole: "user" }
  },
  {
    path: "/sla/configuracao",
    element: <SlaConfig />,
    meta: { title: "Configuração SLA", requiredRole: "admin" }
  }
];
```

## 3. Integração em Chamados - Detalhes do Chamado

Adicionar a seção de SLA na página de detalhes do chamado:

```typescript
// frontend/src/pages/ChamadoDetail.tsx
import { SlaDetailsSection } from "@/components/SlaDetailsSection";

export function ChamadoDetail() {
  const { chamadoId } = useParams();
  const { data: chamado } = useQuery({
    queryKey: ["chamado", chamadoId],
    queryFn: () => api.get(`/chamados/${chamadoId}`)
  });

  return (
    <div className="space-y-6">
      {/* Informações básicas do chamado */}
      <ChamadoInfo chamado={chamado} />
      
      {/* NOVO: Seção de SLA */}
      {chamado && (
        <SlaDetailsSection 
          chamadoId={parseInt(chamadoId)}
          chamadoData={chamado}
          showPausas={true}
        />
      )}
      
      {/* Resto do conteúdo */}
    </div>
  );
}
```

## 4. Integração em Lista de Chamados

Adicionar indicador de SLA na tabela de chamados:

```typescript
// frontend/src/components/ChamadosTable.tsx
import { SlaIndicator } from "@/components/SlaIndicator";

export function ChamadosTable({ chamados }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Código</th>
          <th>Título</th>
          <th>Prioridade</th>
          <th>Status</th>
          <th>SLA</th>  {/* NOVA COLUNA */}
        </tr>
      </thead>
      <tbody>
        {chamados.map(chamado => (
          <tr key={chamado.id}>
            <td>{chamado.codigo}</td>
            <td>{chamado.titulo}</td>
            <td>{chamado.prioridade}</td>
            <td>{chamado.status}</td>
            <td>
              <SlaIndicator
                percentualConsumido={chamado.sla_percentual_consumido}
                emRisco={chamado.sla_em_risco}
                vencido={chamado.sla_vencido}
                size="sm"
                showPercentage={false}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

## 5. Integração com WebSocket (Notificações em Tempo Real)

Configurar listeners para eventos de SLA:

```typescript
// frontend/src/hooks/useSlaNotifications.ts
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { socket } from "@/services/socket"; // Seu serviço de socket.io

export function useSlaNotifications() {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Listener para SLA em risco
    socket.on("sla:em_risco", (data) => {
      console.log(`Chamado ${data.codigo} em risco: ${data.percentual}%`);
      
      // Refetch dos dados de SLA
      queryClient.invalidateQueries({ queryKey: ["sla-indicadores"] });
      
      // Mostrar notificação
      toast({
        title: "SLA em Risco",
        description: `Chamado ${data.codigo} está consumindo ${data.percentual}% do SLA`,
        type: "warning"
      });
    });

    // Listener para SLA vencido
    socket.on("sla:vencido", (data) => {
      console.log(`Chamado ${data.codigo} com SLA VENCIDO`);
      
      queryClient.invalidateQueries({ queryKey: ["sla-indicadores"] });
      
      toast({
        title: "SLA VENCIDO",
        description: `Chamado ${data.codigo} ultrapassou o SLA`,
        type: "error"
      });
    });

    // Listener para conclusão
    socket.on("sla:concluido", (data) => {
      console.log(`Chamado ${data.codigo} concluído - Status: ${data.status}`);
      
      queryClient.invalidateQueries({ queryKey: ["sla-indicadores"] });
    });

    return () => {
      socket.off("sla:em_risco");
      socket.off("sla:vencido");
      socket.off("sla:concluido");
    };
  }, [queryClient]);
}
```

Usar em um layout ou página principal:

```typescript
// frontend/src/layouts/MainLayout.tsx
import { useSlaNotifications } from "@/hooks/useSlaNotifications";

export function MainLayout() {
  useSlaNotifications(); // Ativa listeners de SLA
  
  return (
    <div>
      {/* Layout content */}
    </div>
  );
}
```

## 6. Menu de Navegação

Adicionar links no menu de navegação:

```typescript
// frontend/src/components/Navigation.tsx
export const menuItems = [
  // ... outros itens
  {
    label: "SLA",
    icon: Clock,
    children: [
      {
        label: "Dashboard",
        href: "/sla/dashboard",
        requiredRole: "user"
      },
      {
        label: "Configuração",
        href: "/sla/configuracao",
        requiredRole: "admin"
      }
    ]
  }
];
```

## 7. Estilo e Customização

### Cores do SLA
```css
/* Dentro do SLA */
.sla-ok { @apply text-green-600 bg-green-50; }

/* Em Risco (75-99%) */
.sla-warning { @apply text-yellow-600 bg-yellow-50; }

/* Vencido (100%+) */
.sla-error { @apply text-red-600 bg-red-50; }
```

### Customizar Componentes

Exemplo - Modificar cores de SlaProgressBar:

```typescript
// Adicionar no componente
const colors = {
  dentro: "bg-green-600",
  risco: "bg-amber-500",
  vencido: "bg-red-600"
};
```

## 8. Testes

Exemplo de teste com React Testing Library:

```typescript
// frontend/src/components/__tests__/SlaIndicator.test.tsx
import { render, screen } from "@testing-library/react";
import { SlaIndicator } from "@/components/SlaIndicator";

describe("SlaIndicator", () => {
  it("deve exibir status 'Dentro' com percentual < 75%", () => {
    render(
      <SlaIndicator
        percentualConsumido={50}
        emRisco={false}
        vencido={false}
      />
    );
    
    expect(screen.getByText("Dentro")).toBeInTheDocument();
  });

  it("deve exibir status 'Em Risco' com percentual >= 75%", () => {
    render(
      <SlaIndicator
        percentualConsumido={80}
        emRisco={true}
        vencido={false}
      />
    );
    
    expect(screen.getByText("Em Risco")).toBeInTheDocument();
  });
});
```

## 9. Performance Otimizações

### Lazy Loading
```typescript
import { lazy, Suspense } from "react";

const SlaDashboard = lazy(() => import("@/pages/SlaDashboard"));
const SlaConfig = lazy(() => import("@/pages/SlaConfig"));

export function App() {
  return (
    <Suspense fallback={<Loading />}>
      {/* rotas */}
    </Suspense>
  );
}
```

### Query Cache Configuração
```typescript
// frontend/src/services/queryClient.ts
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutos
      gcTime: 1000 * 60 * 10, // 10 minutos
    },
  },
});
```

## 10. Troubleshooting

### Problema: Componentes não carregam dados
**Solução**: Verificar se o slaService está usando o api client correto

```typescript
// frontend/src/services/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:3001/api",
  headers: {
    "Content-Type": "application/json"
  }
});

// Adicionar interceptor de token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Problema: WebSocket não conecta
**Solução**: Verificar configuração do socket.io

```typescript
// frontend/src/services/socket.ts
import io from "socket.io-client";

export const socket = io(
  process.env.REACT_APP_API_URL || "http://localhost:3001",
  {
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5
  }
);
```

## 11. Documentação de Componentes

Cada componente tem JSDoc documentado:

```typescript
/**
 * SlaIndicator - Exibe status e percentual de SLA
 * 
 * @prop percentualConsumido - Percentual consumido (0-100)
 * @prop emRisco - Indica se está em risco
 * @prop vencido - Indica se venceu
 * @prop showPercentage - Mostrar percentual (default: true)
 * @prop size - Tamanho (sm, md, lg)
 */
```

## Proximos Passos

1. Integrar componentes nas páginas existentes
2. Testar notificações em tempo real
3. Adicionar testes unitários
4. Performance tuning com dados reais
5. Fazer deploy em staging
6. Validação com usuários

## Suporte

Para dúvidas sobre integração:
- Verificar tipos TypeScript em `slaService.ts`
- Consultar exemplos em arquivos de página
- Verificar logs do console para erros de API
