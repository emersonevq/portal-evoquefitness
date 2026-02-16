/**
 * Componente SlaInfoDisplay
 * Exibe informações detalhadas de SLA
 * 
 * Características:
 * - Tempo de resposta (primeira resposta)
 * - Tempo de resolução
 * - Tempo decorrido
 * - Tempo pausado
 * - Status de cumprimento
 */

import React from 'react';
import { Clock, AlertCircle, CheckCircle2, PauseCircle } from 'lucide-react';

interface SlaInfo {
  tempoDecorridoHoras: number;
  tempoPausadoHoras: number;
  tempoLimiteResposta?: number;
  tempoLimiteResolucao?: number;
  percentualConsumido: number;
  emRisco: boolean;
  vencido: boolean;
  dataAbertura: string;
  dataPrimeiraResposta?: string;
  dataConclusao?: string;
}

interface SlaInfoDisplayProps {
  sla: SlaInfo;
  compact?: boolean;
}

const formatHoras = (horas: number): string => {
  const h = Math.floor(horas);
  const m = Math.round((horas - h) * 60);
  return `${h}h ${m}m`;
};

const formatDate = (date: string | undefined): string => {
  if (!date) return '-';
  try {
    return new Date(date).toLocaleString('pt-BR');
  } catch {
    return date;
  }
};

export const SlaInfoDisplay: React.FC<SlaInfoDisplayProps> = ({ sla, compact = false }) => {
  if (compact) {
    return (
      <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium">{formatHoras(sla.tempoDecorridoHoras)} / {sla.tempoLimiteResolucao || '24'}h</span>
        </div>
        {sla.tempoPausadoHoras > 0 && (
          <div className="flex items-center gap-2 text-yellow-600">
            <PauseCircle className="w-4 h-4" />
            <span className="text-sm">Pausa: {formatHoras(sla.tempoPausadoHoras)}</span>
          </div>
        )}
        <div className="flex-1 text-right">
          {sla.vencido ? (
            <span className="text-xs font-medium text-red-600">Vencido</span>
          ) : sla.emRisco ? (
            <span className="text-xs font-medium text-yellow-600">Em risco</span>
          ) : (
            <span className="text-xs font-medium text-green-600">Dentro</span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
        <Clock className="w-5 h-5" />
        Informações de SLA
      </h3>

      <div className="space-y-3">
        {/* Status */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span className="text-sm font-medium text-gray-700">Status</span>
          <div className="flex items-center gap-2">
            {sla.vencido ? (
              <>
                <AlertCircle className="w-5 h-5 text-red-600" />
                <span className="text-sm font-semibold text-red-600">Vencido</span>
              </>
            ) : sla.emRisco ? (
              <>
                <AlertCircle className="w-5 h-5 text-yellow-600" />
                <span className="text-sm font-semibold text-yellow-600">Em Risco</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm font-semibold text-green-600">Dentro do SLA</span>
              </>
            )}
          </div>
        </div>

        {/* Progresso */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span className="text-sm font-medium text-gray-700">Consumo</span>
          <div className="flex items-center gap-2">
            <div className="w-32 h-2 bg-gray-300 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  sla.vencido ? 'bg-red-600' : sla.emRisco ? 'bg-yellow-500' : 'bg-green-600'
                }`}
                style={{ width: `${Math.min(sla.percentualConsumido, 100)}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-700 w-12 text-right">
              {sla.percentualConsumido.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Tempos */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600">Tempo Decorrido</div>
            <div className="text-sm font-semibold text-gray-900 mt-1">
              {formatHoras(sla.tempoDecorridoHoras)}
            </div>
          </div>

          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600">Tempo Limite</div>
            <div className="text-sm font-semibold text-gray-900 mt-1">
              {sla.tempoLimiteResolucao || 24}h
            </div>
          </div>

          {sla.tempoPausadoHoras > 0 && (
            <div className="p-3 bg-yellow-50 rounded-lg col-span-2">
              <div className="text-xs text-yellow-700">Tempo em Pausa</div>
              <div className="text-sm font-semibold text-yellow-900 mt-1">
                {formatHoras(sla.tempoPausadoHoras)}
              </div>
            </div>
          )}
        </div>

        {/* Datas */}
        <div className="space-y-2 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Abertura</span>
            <span className="font-medium text-gray-900">{formatDate(sla.dataAbertura)}</span>
          </div>
          {sla.dataPrimeiraResposta && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Primeira Resposta</span>
              <span className="font-medium text-gray-900">{formatDate(sla.dataPrimeiraResposta)}</span>
            </div>
          )}
          {sla.dataConclusao && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Conclusão</span>
              <span className="font-medium text-gray-900">{formatDate(sla.dataConclusao)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SlaInfoDisplay;
