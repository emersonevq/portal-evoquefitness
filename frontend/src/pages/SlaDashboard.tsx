/**
 * SLA Dashboard Page
 * Exibe métricas e indicadores em tempo real
 */

import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Clock, TrendingUp, RefreshCw } from "lucide-react";
import slaService, { SlaIndicadores, SlaMetricas } from "@/services/slaService";
import { SlaMetricsCard } from "@/components/SlaMetricsCard";
import { SlaIndicator } from "@/components/SlaIndicator";

type Periodo = "dia" | "semana" | "mês";

export function SlaDashboard() {
  const [periodo, setPeriodo] = useState<Periodo>("dia");
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch indicadores
  const { data: indicadores, isLoading: loadingIndicadores, refetch: refetchIndicadores } = useQuery({
    queryKey: ["sla-indicadores"],
    queryFn: () => slaService.obterIndicadores(),
    refetchInterval: autoRefresh ? 30000 : false, // Atualizar a cada 30 segundos
  });

  // Fetch métricas
  const { data: metricas, isLoading: loadingMetricas, refetch: refetchMetricas } = useQuery({
    queryKey: ["sla-metricas", periodo],
    queryFn: () => slaService.obterMetricas(periodo),
    refetchInterval: autoRefresh ? 60000 : false, // Atualizar a cada 1 minuto
  });

  // Fetch relatório
  const { data: relatorio, isLoading: loadingRelatorio } = useQuery({
    queryKey: ["sla-relatorio"],
    queryFn: () => slaService.obterRelatorioDiario(),
    refetchInterval: autoRefresh ? 60000 : false,
  });

  const isLoading = loadingIndicadores || loadingMetricas || loadingRelatorio;

  const handleRefresh = () => {
    refetchIndicadores();
    refetchMetricas();
  };

  const getStatusSLA = (taxaCumprimento: number): { label: string; color: string } => {
    if (taxaCumprimento >= 90) return { label: "Excelente", color: "text-green-600" };
    if (taxaCumprimento >= 75) return { label: "Bom", color: "text-yellow-600" };
    return { label: "Crítico", color: "text-red-600" };
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard SLA</h1>
          <p className="text-gray-600 mt-1">Métricas e indicadores em tempo real</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-2 hover:bg-gray-100 rounded-lg transition disabled:opacity-50"
            title="Atualizar dados"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? "animate-spin" : ""}`} />
          </button>

          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-atualizar
          </label>
        </div>
      </div>

      {/* Indicadores em Tempo Real */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase font-medium">Abertos</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">{indicadores?.abertos || 0}</p>
            </div>
            <Clock className="w-8 h-8 text-blue-400 opacity-20" />
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase font-medium">Em Atendimento</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">{indicadores?.em_atendimento || 0}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-blue-400 opacity-20" />
          </div>
        </div>

        <div className="bg-white border border-yellow-200 rounded-lg p-4 bg-yellow-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-yellow-700 uppercase font-medium">Em Risco</p>
              <p className="text-2xl font-bold text-yellow-600 mt-2">{indicadores?.em_risco || 0}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-yellow-400 opacity-50" />
          </div>
        </div>

        <div className="bg-white border border-red-200 rounded-lg p-4 bg-red-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-red-700 uppercase font-medium">Vencidos</p>
              <p className="text-2xl font-bold text-red-600 mt-2">{indicadores?.vencidos || 0}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-400 opacity-50" />
          </div>
        </div>

        <div className="bg-white border border-green-200 rounded-lg p-4 bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-green-700 uppercase font-medium">Taxa de Cumprimento</p>
              <p className="text-2xl font-bold text-green-600 mt-2">
                {indicadores?.taxa_cumprimento.toFixed(1)}%
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-400 opacity-50" />
          </div>
        </div>
      </div>

      {/* Selector de Período */}
      <div className="flex gap-2">
        {(["dia", "semana", "mês"] as const).map((p) => (
          <button
            key={p}
            onClick={() => setPeriodo(p)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              periodo === p
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {p === "dia" ? "Hoje" : p === "semana" ? "Esta Semana" : "Este Mês"}
          </button>
        ))}
      </div>

      {/* Métricas */}
      {metricas && (
        <SlaMetricsCard
          metrics={{
            taxaCumprimento: metricas.metricas?.taxa_cumprimento || 0,
            chamadosEmRisco: metricas.metricas?.em_risco || 0,
            chamadosVencidos: metricas.metricas?.vencidos || 0,
            totalChamados: metricas.metricas?.total || 0,
            tempoMedioResposta: metricas.metricas?.tempo_medio_resposta,
            tempoMedioResolucao: metricas.metricas?.tempo_medio_resolucao,
          }}
          period={periodo}
        />
      )}

      {/* Métricas por Prioridade */}
      {metricas?.por_prioridade && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-lg mb-4">Cumprimento por Prioridade</h3>

          <div className="space-y-4">
            {Object.entries(metricas.por_prioridade).map(([prioridade, dados]: any) => (
              <div key={prioridade} className="flex items-center gap-4">
                <div className="w-24">
                  <p className="font-medium text-gray-700">{prioridade}</p>
                  <p className="text-xs text-gray-600">
                    {dados.dentro_sla}/{dados.total}
                  </p>
                </div>

                <div className="flex-1">
                  <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        dados.taxa >= 90
                          ? "bg-green-600"
                          : dados.taxa >= 75
                          ? "bg-yellow-500"
                          : "bg-red-600"
                      }`}
                      style={{ width: `${Math.min(dados.taxa, 100)}%` }}
                    />
                  </div>
                </div>

                <div className="w-16 text-right">
                  <p className="font-semibold text-gray-900">{dados.taxa.toFixed(1)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relatório Diário */}
      {relatorio && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-lg mb-4">Resumo Executivo - Hoje</h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs text-blue-700 uppercase font-medium">Total de Chamados</p>
              <p className="text-2xl font-bold text-blue-900 mt-2">
                {relatorio.resumo_executivo?.total_chamados || 0}
              </p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-xs text-green-700 uppercase font-medium">Concluídos</p>
              <p className="text-2xl font-bold text-green-900 mt-2">
                {relatorio.resumo_executivo?.concluidos || 0}
              </p>
            </div>

            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-xs text-yellow-700 uppercase font-medium">Taxa de Cumprimento</p>
              <p className="text-2xl font-bold text-yellow-900 mt-2">
                {relatorio.resumo_executivo?.taxa_cumprimento.toFixed(1)}%
              </p>
            </div>

            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-xs text-red-700 uppercase font-medium">Críticos</p>
              <p className="text-2xl font-bold text-red-900 mt-2">
                {relatorio.resumo_executivo?.criticos || 0}
              </p>
            </div>
          </div>

          {/* Top Prioridades Pendentes */}
          {relatorio.top_prioridades_pendentes && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="font-medium text-gray-900 mb-4">Prioridades Pendentes</h4>

              <div className="space-y-3">
                {relatorio.top_prioridades_pendentes.map((item: any) => (
                  <div key={item.prioridade} className="flex items-center justify-between">
                    <span className="font-medium text-gray-700">{item.prioridade}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-600">{item.quantidade} chamados</span>
                      <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-500"
                          style={{ width: `${item.percentual}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700 w-12 text-right">
                        {item.percentual.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <div className="inline-block animate-spin">
              <RefreshCw className="w-8 h-8 text-blue-600" />
            </div>
            <p className="text-gray-600 mt-4">Carregando dados...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default SlaDashboard;
