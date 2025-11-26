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

export function useMetrics() {
  return useQuery({
    queryKey: ["metrics-dashboard"],
    queryFn: async () => {
      const response = await api.get("/metrics/dashboard");
      return response.data as DashboardMetrics;
    },
    refetchInterval: 30000,
    staleTime: 25000,
  });
}
