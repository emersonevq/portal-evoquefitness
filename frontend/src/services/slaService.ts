/**
 * SLA Service
 * Handles all API communication for SLA-related endpoints
 */

import api from "./api";

// Types
export interface ConfiguracaoSla {
  id: number;
  prioridade: string;
  tempo_primeira_resposta: number;
  tempo_resolucao: number;
  considera_horario_comercial: boolean;
  considera_feriados: boolean;
  escalar_automaticamente: boolean;
  notificar_em_risco: boolean;
  percentual_risco: number;
  ativo: boolean;
}

export interface SlaMetricas {
  taxa_cumprimento: number;
  chamados_em_risco: number;
  chamados_vencidos: number;
  total_chamados: number;
  tempo_medio_resposta?: number;
  tempo_medio_resolucao?: number;
}

export interface SlaIndicadores {
  abertos: number;
  em_atendimento: number;
  em_risco: number;
  vencidos: number;
  concluidos_hoje: number;
  taxa_cumprimento: number;
}

export interface Feriado {
  id: number;
  data: string;
  nome: string;
  tipo: "fixo" | "movel";
  descricao: string;
  ativo: boolean;
}

export interface HorarioComercial {
  id: number;
  nome: string;
  descricao: string;
  hora_inicio: string;
  hora_fim: string;
  segunda: boolean;
  terca: boolean;
  quarta: boolean;
  quinta: boolean;
  sexta: boolean;
  sabado: boolean;
  domingo: boolean;
  timezone: string;
  ativo: boolean;
  padrao: boolean;
}

export interface SlaPausa {
  id: number;
  chamado_id: number;
  pausado_em: string;
  retomado_em?: string;
  duracao_minutos?: number;
  motivo?: string;
}

// Configurações
export const slaService = {
  // Configurações
  async obterConfiguracoes(skip = 0, limit = 20): Promise<{ data: ConfiguracaoSla[]; total: number }> {
    const response = await api.get("/sla/configuracoes", {
      params: { skip, limit },
    });
    return response.data;
  },

  async obterConfiguracao(id: number): Promise<ConfiguracaoSla> {
    const response = await api.get(`/sla/configuracoes/${id}`);
    return response.data;
  },

  async criarConfiguracao(config: Partial<ConfiguracaoSla>): Promise<ConfiguracaoSla> {
    const response = await api.post("/sla/configuracoes", config);
    return response.data;
  },

  async atualizarConfiguracao(id: number, config: Partial<ConfiguracaoSla>): Promise<ConfiguracaoSla> {
    const response = await api.put(`/sla/configuracoes/${id}`, config);
    return response.data;
  },

  async deletarConfiguracao(id: number): Promise<void> {
    await api.delete(`/sla/configuracoes/${id}`);
  },

  // Feriados
  async obterFeriados(skip = 0, limit = 50, ano?: number): Promise<{ data: Feriado[]; total: number }> {
    const response = await api.get("/sla/feriados", {
      params: { skip, limit, ano },
    });
    return response.data;
  },

  async obterFeriado(id: number): Promise<Feriado> {
    const response = await api.get(`/sla/feriados/${id}`);
    return response.data;
  },

  async criarFeriado(feriado: Partial<Feriado>): Promise<Feriado> {
    const response = await api.post("/sla/feriados", feriado);
    return response.data;
  },

  async atualizarFeriado(id: number, feriado: Partial<Feriado>): Promise<Feriado> {
    const response = await api.put(`/sla/feriados/${id}`, feriado);
    return response.data;
  },

  async deletarFeriado(id: number): Promise<void> {
    await api.delete(`/sla/feriados/${id}`);
  },

  async verificarFeriado(data: string): Promise<{ eh_feriado: boolean; feriado?: Feriado }> {
    const response = await api.get(`/sla/feriados/verificar/${data}`);
    return response.data;
  },

  // Horários Comerciais
  async obterHorarios(skip = 0, limit = 50): Promise<{ data: HorarioComercial[]; total: number }> {
    const response = await api.get("/sla/horarios", {
      params: { skip, limit },
    });
    return response.data;
  },

  async obterHorario(id: number): Promise<HorarioComercial> {
    const response = await api.get(`/sla/horarios/${id}`);
    return response.data;
  },

  async criarHorario(horario: Partial<HorarioComercial>): Promise<HorarioComercial> {
    const response = await api.post("/sla/horarios", horario);
    return response.data;
  },

  async atualizarHorario(id: number, horario: Partial<HorarioComercial>): Promise<HorarioComercial> {
    const response = await api.put(`/sla/horarios/${id}`, horario);
    return response.data;
  },

  async deletarHorario(id: number): Promise<void> {
    await api.delete(`/sla/horarios/${id}`);
  },

  // Pausas
  async obterPausasChamado(chamado_id: number): Promise<SlaPausa[]> {
    const response = await api.get(`/sla/pausas/chamado/${chamado_id}`);
    return response.data;
  },

  async retornarPausa(pausa_id: number): Promise<SlaPausa> {
    const response = await api.post(`/sla/pausas/${pausa_id}/retomar`);
    return response.data;
  },

  // Dashboard
  async obterIndicadores(): Promise<SlaIndicadores> {
    const response = await api.get("/sla/dashboard/indicadores");
    return response.data;
  },

  async obterMetricas(periodo: "dia" | "semana" | "mês" = "dia"): Promise<any> {
    const response = await api.get("/sla/dashboard/metricas", {
      params: { periodo },
    });
    return response.data;
  },

  async obterRelatorioDiario(): Promise<any> {
    const response = await api.get("/sla/dashboard/relatorio-diario");
    return response.data;
  },

  // Utilitários
  formatarHoras(horas: number): string {
    const h = Math.floor(horas);
    const m = Math.round((horas - h) * 60);
    return `${h}h ${m}m`;
  },

  getStatusColor(percentual: number, emRisco: boolean, vencido: boolean): string {
    if (vencido) return "text-red-600";
    if (emRisco) return "text-yellow-600";
    return "text-green-600";
  },

  getStatusBgColor(percentual: number, emRisco: boolean, vencido: boolean): string {
    if (vencido) return "bg-red-50";
    if (emRisco) return "bg-yellow-50";
    return "bg-green-50";
  },
};

export default slaService;
