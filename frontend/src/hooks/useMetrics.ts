import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface DashboardMetrics {
  chamados_hoje: number;
  comparacao_ontem: {
    hoje: number;
    ontem: number;
    percentual: number;
    direcao: "up" | "down";
  };
  tempo_resposta_24h: string;
  sla_compliance_24h: number;
  abertos_agora: number;
  tempo_resolucao_30dias: string;
}

/**
 * Hook para obter métricas do dashboard com cache inteligente
 *
 * Estratégia:
 * - staleTime: 5 minutos (cache está fresco por 5 min)
 * - refetchInterval: 10 minutos (atualiza periodicamente)
 * - Usa cache do servidor + React Query
 */
export function useMetrics() {
  return useQuery({
    queryKey: ["metrics-dashboard"],
    queryFn: async () => {
      const response = await api.get("/metrics/dashboard");
      return response.data as DashboardMetrics;
    },
    refetchInterval: 10 * 60 * 1000, // A cada 10 minutos
    staleTime: 5 * 60 * 1000, // Cache considerado fresco por 5 minutos
    gcTime: 30 * 60 * 1000, // Cache pode permanecer na memória por 30 minutos
  });
}
