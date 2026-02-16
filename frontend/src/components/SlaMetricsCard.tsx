/**
 * Componente SlaMetricsCard
 * Exibe métricas resumidas de SLA
 * 
 * Características:
 * - Taxa de cumprimento
 * - Chamados em risco e vencidos
 * - Indicadores visuais
 * - Tempo médio de resposta
 */

import React from 'react';
import { TrendingUp, AlertCircle, Clock, CheckCircle2 } from 'lucide-react';

interface SlaMetrics {
  taxaCumprimento: number;
  chamadosEmRisco: number;
  chamadosVencidos: number;
  totalChamados: number;
  tempoMedioResposta?: number;
  tempoMedioResolucao?: number;
}

interface SlaMetricsCardProps {
  metrics: SlaMetrics;
  period?: 'dia' | 'semana' | 'mês';
  compact?: boolean;
}

export const SlaMetricsCard: React.FC<SlaMetricsCardProps> = ({ 
  metrics, 
  period = 'dia',
  compact = false
}) => {
  const getStatusColor = (percent: number) => {
    if (percent >= 90) return 'text-green-600';
    if (percent >= 75) return 'text-yellow-600';
    return 'text-red-600';
  };

  const periodText = {
    dia: 'Hoje',
    semana: 'Esta Semana',
    mês: 'Este Mês'
  };

  if (compact) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700">{periodText[period]}</span>
          <TrendingUp className="w-4 h-4 text-gray-400" />
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          <div className="p-2 bg-gray-50 rounded">
            <div className="text-xs text-gray-600">Cumprimento</div>
            <div className={`text-lg font-bold ${getStatusColor(metrics.taxaCumprimento)}`}>
              {metrics.taxaCumprimento.toFixed(0)}%
            </div>
          </div>
          
          <div className="p-2 bg-red-50 rounded">
            <div className="text-xs text-gray-600">Vencidos</div>
            <div className="text-lg font-bold text-red-600">
              {metrics.chamadosVencidos}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="font-semibold text-lg mb-6">{periodText[period]}</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Taxa de Cumprimento */}
        <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-blue-600" />
            <span className="text-sm text-gray-700">Taxa de Cumprimento</span>
          </div>
          <div className={`text-2xl font-bold ${getStatusColor(metrics.taxaCumprimento)}`}>
            {metrics.taxaCumprimento.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-600 mt-2">
            {metrics.totalChamados} chamados
          </div>
        </div>

        {/* Em Risco */}
        <div className="p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-yellow-600" />
            <span className="text-sm text-gray-700">Em Risco</span>
          </div>
          <div className="text-2xl font-bold text-yellow-600">
            {metrics.chamadosEmRisco}
          </div>
          <div className="text-xs text-gray-600 mt-2">
            {((metrics.chamadosEmRisco / metrics.totalChamados) * 100).toFixed(0)}% do total
          </div>
        </div>

        {/* Vencidos */}
        <div className="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span className="text-sm text-gray-700">Vencidos</span>
          </div>
          <div className="text-2xl font-bold text-red-600">
            {metrics.chamadosVencidos}
          </div>
          <div className="text-xs text-gray-600 mt-2">
            {((metrics.chamadosVencidos / metrics.totalChamados) * 100).toFixed(0)}% do total
          </div>
        </div>

        {/* Tempo Médio */}
        <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-green-600" />
            <span className="text-sm text-gray-700">Tempo Médio</span>
          </div>
          <div className="text-2xl font-bold text-green-600">
            {metrics.tempoMedioResposta?.toFixed(1) || '-'}h
          </div>
          <div className="text-xs text-gray-600 mt-2">
            Resposta
          </div>
        </div>
      </div>

      {/* Barra de status geral */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">SLA Geral</span>
          <span className={`text-sm font-bold ${getStatusColor(metrics.taxaCumprimento)}`}>
            {metrics.taxaCumprimento >= 90 ? '✓ Ótimo' : metrics.taxaCumprimento >= 75 ? '⚠ Bom' : '✗ Crítico'}
          </span>
        </div>
        <div className="w-full h-3 bg-gray-300 rounded-full overflow-hidden">
          <div
            className={`h-full ${
              metrics.taxaCumprimento >= 90
                ? 'bg-green-600'
                : metrics.taxaCumprimento >= 75
                ? 'bg-yellow-500'
                : 'bg-red-600'
            }`}
            style={{ width: `${Math.min(metrics.taxaCumprimento, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default SlaMetricsCard;
