/**
 * SLA Configuration Page
 * Gerencia configurações, horários e feriados de SLA
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Edit, Trash2, Save, X } from "lucide-react";
import slaService, { ConfiguracaoSla, HorarioComercial, Feriado } from "@/services/slaService";
import { useToast } from "@/hooks/useToast"; // Assumindo que existe um hook de toast

type Tab = "configuracoes" | "horarios" | "feriados";

export function SlaConfig() {
  const [activeTab, setActiveTab] = useState<Tab>("configuracoes");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Configurações
  const {
    data: configuracoes,
    isLoading: loadingConfiguracoes,
    refetch: refetchConfiguracoes,
  } = useQuery({
    queryKey: ["sla-configuracoes"],
    queryFn: () => slaService.obterConfiguracoes(0, 100),
  });

  // Horários
  const {
    data: horarios,
    isLoading: loadingHorarios,
    refetch: refetchHorarios,
  } = useQuery({
    queryKey: ["sla-horarios"],
    queryFn: () => slaService.obterHorarios(0, 100),
  });

  // Feriados
  const {
    data: feriados,
    isLoading: loadingFeriados,
    refetch: refetchFeriados,
  } = useQuery({
    queryKey: ["sla-feriados"],
    queryFn: () => slaService.obterFeriados(0, 200),
  });

  // Mutations
  const criarConfMutation = useMutation({
    mutationFn: (config: Partial<ConfiguracaoSla>) => slaService.criarConfiguracao(config),
    onSuccess: () => {
      refetchConfiguracoes();
      toast({ title: "Configuração criada com sucesso", type: "success" });
    },
  });

  const deletarConfMutation = useMutation({
    mutationFn: (id: number) => slaService.deletarConfiguracao(id),
    onSuccess: () => {
      refetchConfiguracoes();
      toast({ title: "Configuração deletada com sucesso", type: "success" });
    },
  });

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Configuração de SLA</h1>
        <p className="text-gray-600 mt-2">Gerencie SLAs, horários comerciais e feriados</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-gray-200">
        {(["configuracoes", "horarios", "feriados"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 font-medium border-b-2 transition ${
              activeTab === tab
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-600 hover:text-gray-900"
            }`}
          >
            {tab === "configuracoes"
              ? "Configurações SLA"
              : tab === "horarios"
              ? "Horários Comerciais"
              : "Feriados"}
          </button>
        ))}
      </div>

      {/* Tab: Configurações */}
      {activeTab === "configuracoes" && (
        <ConfiguracoesList
          configuracoes={configuracoes?.data || []}
          isLoading={loadingConfiguracoes}
          onDelete={(id) => deletarConfMutation.mutate(id)}
        />
      )}

      {/* Tab: Horários */}
      {activeTab === "horarios" && (
        <HorariosListComponent
          horarios={horarios?.data || []}
          isLoading={loadingHorarios}
        />
      )}

      {/* Tab: Feriados */}
      {activeTab === "feriados" && (
        <FeriadosList
          feriados={feriados?.data || []}
          isLoading={loadingFeriados}
        />
      )}
    </div>
  );
}

// Componente: Lista de Configurações
function ConfiguracoesList({
  configuracoes,
  isLoading,
  onDelete,
}: {
  configuracoes: ConfiguracaoSla[];
  isLoading: boolean;
  onDelete: (id: number) => void;
}) {
  const prioridades = ["Crítica", "Alta", "Normal", "Baixa"];

  return (
    <div className="space-y-4">
      {isLoading ? (
        <div className="text-center py-8">Carregando...</div>
      ) : configuracoes.length === 0 ? (
        <div className="text-center py-8 text-gray-600">Nenhuma configuração encontrada</div>
      ) : (
        <div className="grid gap-4">
          {prioridades.map((prioridade) => {
            const config = configuracoes.find((c) => c.prioridade === prioridade);

            return (
              <div
                key={prioridade}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-lg font-semibold text-gray-900">{prioridade}</h3>
                      {config && (
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            config.ativo
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {config.ativo ? "Ativo" : "Inativo"}
                        </span>
                      )}
                    </div>

                    {config ? (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                        <div>
                          <p className="text-xs text-gray-600 uppercase mb-1">1ª Resposta</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {config.tempo_primeira_resposta}h
                          </p>
                        </div>

                        <div>
                          <p className="text-xs text-gray-600 uppercase mb-1">Resolução</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {config.tempo_resolucao}h
                          </p>
                        </div>

                        <div>
                          <p className="text-xs text-gray-600 uppercase mb-1">Em Risco</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {config.percentual_risco}%
                          </p>
                        </div>

                        <div>
                          <p className="text-xs text-gray-600 uppercase mb-1">Opcões</p>
                          <div className="flex gap-2 text-xs">
                            {config.escalar_automaticamente && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                Auto-escala
                              </span>
                            )}
                            {config.notificar_em_risco && (
                              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
                                Notificação
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-600 text-sm">Nenhuma configuração</p>
                    )}
                  </div>

                  <div className="flex gap-2 ml-4">
                    {config && (
                      <>
                        <button className="p-2 hover:bg-gray-100 rounded-lg transition text-blue-600">
                          <Edit className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => onDelete(config.id)}
                          className="p-2 hover:bg-gray-100 rounded-lg transition text-red-600"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Componente: Lista de Horários
function HorariosListComponent({
  horarios,
  isLoading,
}: {
  horarios: HorarioComercial[];
  isLoading: boolean;
}) {
  const dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

  return (
    <div className="space-y-4">
      {isLoading ? (
        <div className="text-center py-8">Carregando...</div>
      ) : horarios.length === 0 ? (
        <div className="text-center py-8 text-gray-600">Nenhum horário encontrado</div>
      ) : (
        <div className="grid gap-4">
          {horarios.map((horario) => (
            <div
              key={horario.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{horario.nome}</h3>
                  <p className="text-sm text-gray-600">{horario.descricao}</p>
                </div>
                {horario.padrao && (
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                    Padrão
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-4 bg-gray-50 rounded">
                <div>
                  <p className="text-xs text-gray-600 uppercase mb-1">Horário</p>
                  <p className="font-semibold text-gray-900">
                    {horario.hora_inicio} - {horario.hora_fim}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-600 uppercase mb-1">Timezone</p>
                  <p className="font-semibold text-gray-900">{horario.timezone}</p>
                </div>

                <div>
                  <p className="text-xs text-gray-600 uppercase mb-1">Dias Úteis</p>
                  <p className="font-semibold text-gray-900">
                    {[
                      horario.segunda && "Seg",
                      horario.terca && "Ter",
                      horario.quarta && "Qua",
                      horario.quinta && "Qui",
                      horario.sexta && "Sex",
                      horario.sabado && "Sab",
                      horario.domingo && "Dom",
                    ]
                      .filter(Boolean)
                      .join(", ")}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-600 uppercase mb-1">Status</p>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      horario.ativo
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {horario.ativo ? "Ativo" : "Inativo"}
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <button className="p-2 hover:bg-gray-100 rounded-lg transition text-blue-600">
                  <Edit className="w-5 h-5" />
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg transition text-red-600">
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Componente: Lista de Feriados
function FeriadosList({
  feriados,
  isLoading,
}: {
  feriados: Feriado[];
  isLoading: boolean;
}) {
  const feriadosAtivos = feriados.filter((f) => f.ativo);
  const feriadosInativos = feriados.filter((f) => !f.ativo);

  return (
    <div className="space-y-6">
      {isLoading ? (
        <div className="text-center py-8">Carregando...</div>
      ) : (
        <>
          {/* Feriados Ativos */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Feriados Ativos</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {feriadosAtivos.map((feriado) => (
                <div
                  key={feriado.id}
                  className="bg-white border border-green-200 rounded-lg p-4 bg-green-50"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-gray-900">{feriado.nome}</p>
                      <p className="text-sm text-gray-600 mt-1">{feriado.descricao}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        {new Date(feriado.data).toLocaleDateString("pt-BR", {
                          weekday: "long",
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        })}
                      </p>
                      <span
                        className={`inline-block mt-2 px-2 py-1 text-xs font-medium rounded ${
                          feriado.tipo === "fixo"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-purple-100 text-purple-800"
                        }`}
                      >
                        {feriado.tipo === "fixo" ? "Fixo" : "Móvel"}
                      </span>
                    </div>

                    <div className="flex gap-2">
                      <button className="p-2 hover:bg-green-200 rounded-lg transition text-blue-600">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="p-2 hover:bg-green-200 rounded-lg transition text-red-600">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Feriados Inativos */}
          {feriadosInativos.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Feriados Inativos</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {feriadosInativos.map((feriado) => (
                  <div
                    key={feriado.id}
                    className="bg-white border border-gray-200 rounded-lg p-4 opacity-60"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-gray-900">{feriado.nome}</p>
                        <p className="text-sm text-gray-600 mt-1">{feriado.descricao}</p>
                        <p className="text-xs text-gray-500 mt-2">
                          {new Date(feriado.data).toLocaleDateString("pt-BR", {
                            weekday: "long",
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </p>
                      </div>

                      <div className="flex gap-2">
                        <button className="p-2 hover:bg-gray-100 rounded-lg transition text-gray-600">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button className="p-2 hover:bg-gray-100 rounded-lg transition text-red-600">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {feriados.length === 0 && (
            <div className="text-center py-8 text-gray-600">Nenhum feriado encontrado</div>
          )}
        </>
      )}
    </div>
  );
}

export default SlaConfig;
