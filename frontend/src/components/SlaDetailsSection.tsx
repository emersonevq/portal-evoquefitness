/**
 * Componente SlaDetailsSection
 * Seção de SLA para exibir na página de detalhes do chamado
 * Pode ser integrado em qualquer página que exiba informações de chamado
 * 
 * Uso:
 * <SlaDetailsSection chamadoId={123} />
 */

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Clock, CheckCircle2, Loader } from "lucide-react";
import slaService, { SlaPausa } from "@/services/slaService";
import { SlaProgressBar } from "./SlaProgressBar";
import { SlaInfoDisplay } from "./SlaInfoDisplay";

interface ChamadoSLA {
  id: number;
  codigo: string;
  prioridade: string;
  sla_percentual_consumido: number;
  sla_em_risco: boolean;
  sla_vencido: boolean;
  sla_tempo_decorrido_horas: number;
  sla_tempo_pausado_horas: number;
  data_abertura: string;
  data_primeira_resposta?: string;
  data_conclusao?: string;
}

interface SlaDetailsSectionProps {
  chamadoId: number;
  chamadoData?: Partial<ChamadoSLA>;
  compact?: boolean;
  showPausas?: boolean;
}

export const SlaDetailsSection: React.FC<SlaDetailsSectionProps> = ({
  chamadoId,
  chamadoData,
  compact = false,
  showPausas = true,
}) => {
  // Buscar pausas se necessário
  const { data: pausas, isLoading: loadingPausas } = useQuery({
    queryKey: ["sla-pausas", chamadoId],
    queryFn: () => slaService.obterPausasChamado(chamadoId),
    enabled: showPausas,
  });

  // Se não há dados do chamado, retornar null
  if (!chamadoData) {
    return <div>Carregando informações de SLA...</div>;
  }

  const {
    prioridade,
    sla_percentual_consumido = 0,
    sla_em_risco = false,
    sla_vencido = false,
    sla_tempo_decorrido_horas = 0,
    sla_tempo_pausado_horas = 0,
    data_abertura,
    data_primeira_resposta,
    data_conclusao,
  } = chamadoData;

  const getStatusBadge = () => {
    if (sla_vencido) {
      return (
        <div className="flex items-center gap-2 px-4 py-2 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="font-semibold text-red-700">SLA Vencido</span>
        </div>
      );
    }

    if (sla_em_risco) {
      return (
        <div className="flex items-center gap-2 px-4 py-2 bg-yellow-50 border border-yellow-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-yellow-600" />
          <span className="font-semibold text-yellow-700">SLA em Risco</span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg">
        <CheckCircle2 className="w-5 h-5 text-green-600" />
        <span className="font-semibold text-green-700">Dentro do SLA</span>
      </div>
    );
  };

  if (compact) {
    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-700 mb-2">Prioridade: {prioridade}</p>
            <SlaProgressBar
              percentualConsumido={sla_percentual_consumido}
              emRisco={sla_em_risco}
              vencido={sla_vencido}
              height="sm"
              showLabel={true}
            />
          </div>
          <div>{getStatusBadge()}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Badge */}
      <div>{getStatusBadge()}</div>

      {/* Progress Bar */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Progresso do SLA
        </h3>

        <SlaProgressBar
          percentualConsumido={sla_percentual_consumido}
          emRisco={sla_em_risco}
          vencido={sla_vencido}
          height="lg"
          showLabel={true}
        />

        <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4 pt-6 border-t border-gray-200">
          <div>
            <p className="text-xs text-gray-600 uppercase font-medium">Tempo Decorrido</p>
            <p className="text-lg font-semibold text-gray-900 mt-2">
              {slaService.formatarHoras(sla_tempo_decorrido_horas)}
            </p>
          </div>

          {sla_tempo_pausado_horas > 0 && (
            <div>
              <p className="text-xs text-yellow-700 uppercase font-medium">Tempo Pausado</p>
              <p className="text-lg font-semibold text-yellow-900 mt-2">
                {slaService.formatarHoras(sla_tempo_pausado_horas)}
              </p>
            </div>
          )}

          <div>
            <p className="text-xs text-gray-600 uppercase font-medium">Prioridade</p>
            <p className="text-lg font-semibold text-gray-900 mt-2">{prioridade}</p>
          </div>
        </div>
      </div>

      {/* Detailed Info */}
      <SlaInfoDisplay
        sla={{
          tempoDecorridoHoras: sla_tempo_decorrido_horas,
          tempoPausadoHoras: sla_tempo_pausado_horas,
          percentualConsumido: sla_percentual_consumido,
          emRisco: sla_em_risco,
          vencido: sla_vencido,
          dataAbertura: data_abertura || "",
          dataPrimeiraResposta: data_primeira_resposta,
          dataConclusao: data_conclusao,
        }}
        compact={false}
      />

      {/* Pausas */}
      {showPausas && pausas && pausas.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-lg mb-4">Pausas Registradas</h3>

          <div className="space-y-3">
            {pausas.map((pausa) => (
              <div key={pausa.id} className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900">
                      {pausa.motivo || "Pausa registrada"}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {new Date(pausa.pausado_em).toLocaleString("pt-BR")}
                      {pausa.retomado_em &&
                        ` até ${new Date(pausa.retomado_em).toLocaleString("pt-BR")}`}
                    </p>
                    {pausa.duracao_minutos && (
                      <p className="text-xs text-gray-500 mt-2">
                        Duração: {Math.floor(pausa.duracao_minutos / 60)}h{" "}
                        {pausa.duracao_minutos % 60}m
                      </p>
                    )}
                  </div>

                  {!pausa.retomado_em && (
                    <span className="px-3 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded-full">
                      Em pausa
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info complementar */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Informação:</strong> O SLA é calculado considerando o horário comercial
          (08h-18h, segunda a sexta) e feriados nacionais. Pausas automáticas não são
          contabilizadas no tempo de SLA.
        </p>
      </div>
    </div>
  );
};

export default SlaDetailsSection;
