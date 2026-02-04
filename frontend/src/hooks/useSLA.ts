import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { slaService, SlaDashboard, SlaChamadoStatus } from "@/services/slaService";

export function useSLADashboard() {
  const queryClient = useQueryClient();

  const { data: dashboard, ...query } = useQuery({
    queryKey: ["sla-dashboard"],
    queryFn: () => slaService.getDashboard(),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });

  // WebSocket listener
  useEffect(() => {
    try {
      const socket = (window as any).__APP_SOCK__;
      if (!socket) return;

      const handleSlaUpdated = () => {
        queryClient.invalidateQueries({ queryKey: ["sla-dashboard"] });
      };

      socket.on("sla:updated", handleSlaUpdated);
      return () => {
        socket.off("sla:updated", handleSlaUpdated);
      };
    } catch (error) {
      console.debug("[useSLADashboard] Erro ao configurar WebSocket:", error);
    }
  }, [queryClient]);

  return {
    dashboard,
    ...query,
  };
}

export function useSLAChamado(chamadoId: number) {
  const queryClient = useQueryClient();

  const { data: slaStatus, ...query } = useQuery({
    queryKey: ["sla-chamado", chamadoId],
    queryFn: () => slaService.getSlaAlturaStatus(chamadoId),
    staleTime: 2 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  });

  // WebSocket listener
  useEffect(() => {
    try {
      const socket = (window as any).__APP_SOCK__;
      if (!socket) return;

      const handleChamadoUpdated = (data: any) => {
        if (data.chamado_id === chamadoId) {
          queryClient.invalidateQueries({ queryKey: ["sla-chamado", chamadoId] });
        }
      };

      socket.on("chamado:updated", handleChamadoUpdated);
      return () => {
        socket.off("chamado:updated", handleChamadoUpdated);
      };
    } catch (error) {
      console.debug("[useSLAChamado] Erro ao configurar WebSocket:", error);
    }
  }, [queryClient, chamadoId]);

  const formatTempo = (horas: number): string => {
    if (horas < 1) {
      const minutos = Math.round(horas * 60);
      return `${minutos}min`;
    }
    if (horas < 24) {
      return `${horas.toFixed(1)}h`;
    }
    const dias = Math.floor(horas / 24);
    const horasRestantes = horas % 24;
    return `${dias}d ${horasRestantes.toFixed(0)}h`;
  };

  return {
    slaStatus,
    formatTempo,
    ...query,
  };
}

export function useSLAResumo() {
  const { data: resumo, ...query } = useQuery({
    queryKey: ["sla-resumo"],
    queryFn: () => slaService.getDashboardResumo(),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });

  return {
    resumo,
    ...query,
  };
}
