import React, { useEffect, useState } from 'react';
import { slaService, SlaMetrics, SlaDashboard as ISlaDashboard } from '../../services/slaService';
import { SlaMetricsCard } from './SlaMetricsCard';
import { SlaAlertsList } from './SlaAlertsList';
import { RefreshCw, AlertTriangle } from 'lucide-react';

export const SlaDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SlaMetrics | null>(null);
  const [dashboard, setDashboard] = useState<ISlaDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const carregarDados = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metricsData, dashboardData] = await Promise.all([
        slaService.getDashboardResumo(),
        slaService.getDashboard(),
      ]);

      setMetrics(metricsData);
      setDashboard(dashboardData);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Erro ao carregar dados SLA:', err);
      setError('Erro ao carregar dados de SLA');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarDados();

    // Recarregar a cada 5 minutos
    const interval = setInterval(carregarDados, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const formatarHora = (horas: number): string => {
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

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-2" />
          <p className="text-gray-600">Carregando dados de SLA...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-red-800">{error}</p>
          <button
            onClick={carregarDados}
            className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200 transition"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="sla-dashboard space-y-6">
      {/* Cabeçalho */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard SLA</h1>
          <p className="text-gray-600 text-sm mt-1">
            {dashboard && `Período: ${new Date(dashboard.periodo_inicio).toLocaleDateString('pt-BR')} a ${new Date(dashboard.periodo_fim).toLocaleDateString('pt-BR')}`}
          </p>
          {lastUpdate && (
            <p className="text-gray-500 text-xs mt-1">
              Atualizado em {lastUpdate.toLocaleTimeString('pt-BR')}
            </p>
          )}
        </div>
        <button
          onClick={carregarDados}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
        >
          <RefreshCw className="w-4 h-4" />
          Atualizar
        </button>
      </div>

      {/* Resumo de chamados */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-gray-600 text-sm font-medium">Total de Chamados</div>
            <div className="text-3xl font-bold text-gray-900 mt-1">{dashboard.total_chamados}</div>
            <div className="text-xs text-gray-500 mt-2">
              {dashboard.total_chamados_ativos} ativos, {dashboard.total_chamados_concluidos} concluídos
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-gray-600 text-sm font-medium">Em Risco</div>
            <div className="text-3xl font-bold text-yellow-600 mt-1">{dashboard.chamados_em_risco}</div>
            <div className="text-xs text-gray-500 mt-2">Atenção necessária</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-gray-600 text-sm font-medium">Vencidos</div>
            <div className="text-3xl font-bold text-red-600 mt-1">{dashboard.chamados_vencidos}</div>
            <div className="text-xs text-gray-500 mt-2">SLA vencido</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-gray-600 text-sm font-medium">Pausados</div>
            <div className="text-3xl font-bold text-blue-600 mt-1">{dashboard.chamados_pausados}</div>
            <div className="text-xs text-gray-500 mt-2">Aguardando análise</div>
          </div>
        </div>
      )}

      {/* Métricas principais */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SlaMetricsCard
            title="SLA de Resposta"
            percentual={metrics.percentual_sla_resposta}
            chamadosAtivos={dashboard?.dentro_sla_resposta || 0}
            timeAv={formatarHora(metrics.tempo_medio_resposta_horas)}
          />
          <SlaMetricsCard
            title="SLA de Resolução"
            percentual={metrics.percentual_sla_resolucao}
            chamadosAtivos={dashboard?.dentro_sla_resolucao || 0}
            timeAv={formatarHora(metrics.tempo_medio_resolucao_horas)}
          />
        </div>
      )}

      {/* Listas de alertas */}
      {dashboard && (
        <div className="grid grid-cols-1 gap-6">
          <SlaAlertsList
            title="Chamados Vencidos"
            chamados={dashboard.lista_vencidos}
            type="vencido"
          />
          <SlaAlertsList
            title="Chamados em Risco"
            chamados={dashboard.lista_em_risco}
            type="em_risco"
          />
          <SlaAlertsList
            title="Chamados Pausados"
            chamados={dashboard.lista_pausados}
            type="pausado"
          />
        </div>
      )}

      {/* Footer */}
      {dashboard?.proximo_recalculo && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
          Próximo cálculo automático: {new Date(dashboard.proximo_recalculo).toLocaleTimeString('pt-BR')}
        </div>
      )}
    </div>
  );
};
