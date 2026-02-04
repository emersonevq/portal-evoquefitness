import { api } from "@/lib/api";

export interface SlaConfig {
  id: number;
  prioridade: string;
  tempo_resposta_horas: number;
  tempo_resolucao_horas: number;
  descricao?: string;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
  ultimo_reset_em?: string;
}

export interface SlaChamadoStatus {
  chamado_id: number;
  codigo: string;
  prioridade: string;
  status: string;
  tempo_decorrido_horas: number;
  tempo_pausado_horas: number;
  tempo_limite_resposta_horas: number;
  tempo_limite_resolucao_horas: number;
  resposta_em_dia: boolean;
  resposta_em_risco: boolean;
  resposta_vencida: boolean;
  resolucao_em_dia: boolean;
  resolucao_em_risco: boolean;
  resolucao_vencida: boolean;
  percentual_resposta: number;
  percentual_resolucao: number;
  pausado: boolean;
  ativo: boolean;
}

export interface SlaDashboard {
  periodo_inicio: string;
  periodo_fim: string;
  total_chamados: number;
  chamados_ativos: number;
  chamados_concluidos: number;
  chamados_resposta_ok: number;
  chamados_resposta_risco: number;
  chamados_resposta_vencido: number;
  percentual_resposta_ok: number;
  tempo_medio_resposta_horas: number;
  chamados_resolucao_ok: number;
  chamados_resolucao_risco: number;
  chamados_resolucao_vencido: number;
  percentual_resolucao_ok: number;
  tempo_medio_resolucao_horas: number;
  chamados_em_risco: number;
  chamados_vencidos: number;
  chamados_pausados: number;
  lista_em_risco: SlaChamadoStatus[];
  lista_vencidos: SlaChamadoStatus[];
  lista_pausados: SlaChamadoStatus[];
  ultima_atualizacao: string;
}

export interface SlaDashboardResumo {
  percentual_resposta_ok: number;
  percentual_resolucao_ok: number;
  chamados_em_risco: number;
  chamados_vencidos: number;
  chamados_pausados: number;
  tempo_medio_resposta_horas: number;
  tempo_medio_resolucao_horas: number;
  ultima_atualizacao: string;
}

class SlaService {
  private baseUrl = "/sla";

  async getDashboardResumo(): Promise<SlaDashboardResumo> {
    try {
      const response = await api.get<SlaDashboardResumo>(
        `${this.baseUrl}/dashboard/resumo`
      );
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar resumo SLA:", error);
      throw error;
    }
  }

  async getDashboard(
    dataInicio?: Date,
    dataFim?: Date
  ): Promise<SlaDashboard> {
    try {
      const params = new URLSearchParams();
      if (dataInicio) params.append("data_inicio", dataInicio.toISOString());
      if (dataFim) params.append("data_fim", dataFim.toISOString());

      const queryString = params.toString();
      const url = `${this.baseUrl}/dashboard${
        queryString ? `?${queryString}` : ""
      }`;

      const response = await api.get<SlaDashboard>(url);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar dashboard SLA:", error);
      throw error;
    }
  }

  async getSlaConfiguracao(): Promise<SlaConfig[]> {
    try {
      const response = await api.get<SlaConfig[]>(`${this.baseUrl}/config`);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar configurações SLA:", error);
      throw error;
    }
  }

  async getSlaAlturaStatus(chamadoId: number): Promise<SlaChamadoStatus> {
    try {
      const response = await api.get<SlaChamadoStatus>(
        `${this.baseUrl}/chamado/${chamadoId}`
      );
      return response.data;
    } catch (error) {
      console.error(
        `Erro ao buscar SLA do chamado ${chamadoId}:`,
        error
      );
      throw error;
    }
  }

  async getSchedulerStatus(): Promise<any> {
    try {
      const response = await api.get(`${this.baseUrl}/scheduler/status`);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar status do scheduler:", error);
      throw error;
    }
  }

  async executarRecalculo(): Promise<any> {
    try {
      const response = await api.post(`${this.baseUrl}/scheduler/executar`);
      return response.data;
    } catch (error) {
      console.error("Erro ao executar recálculo:", error);
      throw error;
    }
  }

  async getCacheStatus(): Promise<any> {
    try {
      const response = await api.get(`${this.baseUrl}/cache/status`);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar status do cache:", error);
      throw error;
    }
  }

  async invalidarCache(): Promise<void> {
    try {
      await api.post(`${this.baseUrl}/cache/invalidar`);
    } catch (error) {
      console.error("Erro ao invalidar cache:", error);
      throw error;
    }
  }
}

export const slaService = new SlaService();
