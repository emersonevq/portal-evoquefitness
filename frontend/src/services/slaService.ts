import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface SlaMetrics {
  percentual_sla_resposta: number;
  percentual_sla_resolucao: number;
  chamados_em_risco: number;
  chamados_vencidos: number;
  chamados_pausados: number;
  tempo_medio_resposta_horas: number;
  tempo_medio_resolucao_horas: number;
  ultima_atualizacao: string;
}

export interface SlaConfig {
  id: number;
  prioridade: string;
  tempo_resposta_horas: number;
  tempo_resolucao_horas: number;
  descricao?: string;
  ativo: boolean;
  criado_em?: string;
  atualizado_em?: string;
}

export interface SlaChamadoStatus {
  chamado_id: number;
  codigo: string;
  protocolo?: string;
  prioridade: string;
  status: string;
  status_normalizado: string;
  solicitante?: string;
  unidade?: string;
  problema?: string;
  data_abertura: string;
  tempo_limite_horas: number;
  tempo_decorrido_horas: number;
  tempo_pausado_horas: number;
  tempo_restante_horas: number;
  percentual_consumido: number;
  em_risco: boolean;
  vencido: boolean;
  pausado: boolean;
  prazo_limite?: string;
}

export interface SlaDashboard {
  periodo_inicio: string;
  periodo_fim: string;
  total_chamados: number;
  total_chamados_ativos: number;
  total_chamados_concluidos: number;
  dentro_sla_resposta: number;
  fora_sla_resposta: number;
  percentual_sla_resposta: number;
  tempo_medio_resposta_horas: number;
  dentro_sla_resolucao: number;
  fora_sla_resolucao: number;
  percentual_sla_resolucao: number;
  tempo_medio_resolucao_horas: number;
  chamados_em_risco: number;
  chamados_vencidos: number;
  chamados_pausados: number;
  lista_em_risco: SlaChamadoStatus[];
  lista_vencidos: SlaChamadoStatus[];
  lista_pausados: SlaChamadoStatus[];
  ultima_atualizacao: string;
  proximo_recalculo?: string;
}

class SlaService {
  private baseUrl = `${API_BASE_URL}/api/sla`;

  async getDashboardResumo(): Promise<SlaMetrics> {
    try {
      const response = await axios.get(`${this.baseUrl}/dashboard/resumo`);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar resumo SLA:", error);
      throw error;
    }
  }

  async getDashboard(
    dataInicio?: Date,
    dataFim?: Date,
    prioridade?: string,
  ): Promise<SlaDashboard> {
    try {
      const params = new URLSearchParams();
      if (dataInicio) params.append("data_inicio", dataInicio.toISOString());
      if (dataFim) params.append("data_fim", dataFim.toISOString());
      if (prioridade) params.append("prioridade", prioridade);

      const response = await axios.get(`${this.baseUrl}/dashboard`, { params });
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar dashboard SLA:", error);
      throw error;
    }
  }

  async getSlaConfiguracao(): Promise<SlaConfig[]> {
    try {
      const response = await axios.get(`${this.baseUrl}/config`);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar configurações SLA:", error);
      throw error;
    }
  }

  async getSlaAlturaStatus(chamadoId: number): Promise<SlaChamadoStatus> {
    try {
      const response = await axios.get(`${this.baseUrl}/chamado/${chamadoId}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao buscar SLA do chamado ${chamadoId}:`, error);
      throw error;
    }
  }

  async getSchedulerStatus(): Promise<any> {
    try {
      const response = await axios.get(`${this.baseUrl}/scheduler/status`);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar status do scheduler:", error);
      throw error;
    }
  }

  async executarRecalculo(): Promise<any> {
    try {
      const response = await axios.post(`${this.baseUrl}/scheduler/executar`);
      return response.data;
    } catch (error) {
      console.error("Erro ao executar recálculo:", error);
      throw error;
    }
  }
}

export const slaService = new SlaService();
