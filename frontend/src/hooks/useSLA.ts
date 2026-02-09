/**
 * Hook customizado para gerenciar estado de SLA
 * Inclui auto-refresh a cada 15 minutos
 * Trata cache e erros automaticamente
 */

import { useState, useEffect, useCallback } from "react";
import { slaService, MetricasSLA, MetricaPrioridade, Dashboard } from "@/services/slaService";

export interface UseSLAState {
  metricas: MetricasSLA | null;
  metricasPorPrioridade: MetricaPrioridade[] | null;
  dashboard: Dashboard | null;
  loading: boolean;
  error: string | null;
  ultimaAtualizacao: Date | null;
  proximaAtualizacao: Date | null;
  periodoDias: number;
}

const INTERVALO_AUTO_REFRESH_MINUTOS = 15;
const INTERVALO_POLL_MINUTOS = 5; // Poll a cada 5 minutos

/**
 * Hook para obter e gerenciar métricas de SLA
 */
export function useSLA() {
  const [state, setState] = useState<UseSLAState>({
    metricas: null,
    metricasPorPrioridade: null,
    dashboard: null,
    loading: true,
    error: null,
    ultimaAtualizacao: null,
    proximaAtualizacao: null,
    periodoDias: 30,
  });

  const [atualizando, setAtualizando] = useState(false);

  /**
   * Carrega dados de SLA
   */
  const carregarDados = useCallback(async (periodoDias: number = 30) => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      // Carrega em paralelo
      const [metricas, metricasPrioridade, dashboard] = await Promise.all([
        slaService.obterMetricas(periodoDias),
        slaService.obterMetricasPorPrioridade(periodoDias),
        slaService.obterDashboard(),
      ]);

      const agora = new Date();
      const proxima = new Date(agora.getTime() + INTERVALO_AUTO_REFRESH_MINUTOS * 60000);

      setState((prev) => ({
        ...prev,
        metricas: metricas.metricas,
        metricasPorPrioridade: metricasPrioridade.por_prioridade,
        dashboard: dashboard,
        loading: false,
        ultimaAtualizacao: agora,
        proximaAtualizacao: proxima,
        periodoDias,
      }));
    } catch (error) {
      const mensagem = error instanceof Error ? error.message : "Erro ao carregar SLA";
      setState((prev) => ({
        ...prev,
        loading: false,
        error: mensagem,
      }));
      console.error("Erro ao carregar SLA:", error);
    }
  }, []);

  /**
   * Atualiza SLA manualmente
   */
  const atualizar = useCallback(async () => {
    try {
      setAtualizando(true);
      const resultado = await slaService.atualizarSLA();

      // Recarrega dados após atualização
      await carregarDados(state.periodoDias);

      return resultado;
    } catch (error) {
      const mensagem = error instanceof Error ? error.message : "Erro ao atualizar SLA";
      setState((prev) => ({
        ...prev,
        error: mensagem,
      }));
      throw error;
    } finally {
      setAtualizando(false);
    }
  }, [carregarDados, state.periodoDias]);

  /**
   * Muda período de análise
   */
  const mudarPeriodo = useCallback((periodoDias: number) => {
    carregarDados(periodoDias);
  }, [carregarDados]);

  /**
   * Auto-refresh a cada 15 minutos
   */
  useEffect(() => {
    // Carrega dados inicialmente
    carregarDados(state.periodoDias);

    // Intervalo de refresh automático
    const intervalo = setInterval(() => {
      carregarDados(state.periodoDias);
    }, INTERVALO_AUTO_REFRESH_MINUTOS * 60000);

    return () => clearInterval(intervalo);
  }, []);

  return {
    ...state,
    atualizando,
    atualizar,
    mudarPeriodo,
    carregarDados,
  };
}

/**
 * Hook para obter SLA de um chamado específico
 */
export function useSLAChamado(chamadoId: number) {
  const [sla, setSla] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    try {
      setLoading(true);
      const resultado = await slaService.obterSLAChamado(chamadoId);
      setSla(resultado.sla);
      setError(null);
    } catch (err) {
      const mensagem = err instanceof Error ? err.message : "Erro ao carregar SLA";
      setError(mensagem);
    } finally {
      setLoading(false);
    }
  }, [chamadoId]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  return { sla, loading, error, recarregar: carregar };
}

/**
 * Hook para obter alertas (chamados em risco e vencidos)
 */
export function useSLAAlerts() {
  const [alertas, setAlertas] = useState({
    emRisco: [] as any[],
    vencidos: [] as any[],
    total: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    try {
      setLoading(true);
      const [emRisco, vencidos] = await Promise.all([
        slaService.obterChamadosEmRisco(),
        slaService.obterChamadosVencidos(),
      ]);

      setAlertas({
        emRisco: emRisco.chamados,
        vencidos: vencidos.chamados,
        total: emRisco.total + vencidos.total,
      });
      setError(null);
    } catch (err) {
      const mensagem = err instanceof Error ? err.message : "Erro ao carregar alertas";
      setError(mensagem);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
    // Atualiza alertas a cada 5 minutos
    const intervalo = setInterval(carregar, INTERVALO_POLL_MINUTOS * 60000);
    return () => clearInterval(intervalo);
  }, [carregar]);

  return { alertas, loading, error, recarregar: carregar };
}

/**
 * Função helper para formatar percentual com cores
 */
export function formatarPercentual(valor: number): {
  texto: string;
  cor: string;
  status: string;
} {
  if (valor >= 100) {
    return { texto: `${valor.toFixed(0)}%`, cor: "text-red-600", status: "Vencido" };
  }
  if (valor >= 80) {
    return { texto: `${valor.toFixed(0)}%`, cor: "text-yellow-600", status: "Em Risco" };
  }
  return { texto: `${valor.toFixed(0)}%`, cor: "text-green-600", status: "Em Dia" };
}

/**
 * Função helper para formatar horas
 */
export function formatarHoras(horas: number): string {
  if (horas < 1) {
    return `${Math.round(horas * 60)}m`;
  }
  if (horas < 24) {
    return `${horas.toFixed(1)}h`;
  }
  const dias = Math.floor(horas / 24);
  const horasRestantes = horas % 24;
  return `${dias}d ${horasRestantes.toFixed(1)}h`;
}

/**
 * Função helper para formatar data relativa
 */
export function formatarDataRelativa(data: Date): string {
  const agora = new Date();
  const diferenca = agora.getTime() - data.getTime();
  const minutos = Math.floor(diferenca / 60000);

  if (minutos < 1) return "agora";
  if (minutos < 60) return `${minutos}m atrás`;

  const horas = Math.floor(minutos / 60);
  if (horas < 24) return `${horas}h atrás`;

  const dias = Math.floor(horas / 24);
  return `${dias}d atrás`;
}
