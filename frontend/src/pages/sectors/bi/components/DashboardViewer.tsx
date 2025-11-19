import React, { useState, useRef, useEffect, useReducer, useCallback } from "react";
import { Dashboard } from "../hooks/useDashboards";
import { apiFetch } from "@/lib/api";
import {
  AlertCircle, RefreshCw, Loader2, CheckCircle2, 
  ZoomIn, ZoomOut, Download, Settings, Eye, EyeOff
} from "lucide-react";
import * as pbi from "powerbi-client";

interface DashboardViewerProps {
  dashboard: Dashboard;
}

type ViewerState = 
  | "idle"
  | "fetching-token"
  | "validating"
  | "embedding"
  | "ready"
  | "error"
  | "timeout";

interface StateData {
  status: ViewerState;
  error: string | null;
  progress: number;
  retryCount: number;
  message: string;
}

type Action = 
  | { type: "START" }
  | { type: "FETCHING_TOKEN" }
  | { type: "VALIDATING" }
  | { type: "EMBEDDING"; progress: number }
  | { type: "READY" }
  | { type: "ERROR"; error: string }
  | { type: "TIMEOUT" }
  | { type: "RETRY" }
  | { type: "RESET" };

const initialState: StateData = {
  status: "idle",
  error: null,
  progress: 0,
  retryCount: 0,
  message: "Pronto para carregar o dashboard"
};

function stateReducer(state: StateData, action: Action): StateData {
  switch (action.type) {
    case "START":
      return { ...state, status: "fetching-token", progress: 10, message: "Iniciando carregamento..." };
    case "FETCHING_TOKEN":
      return { ...state, progress: 25, message: "Obtendo credenciais de acesso..." };
    case "VALIDATING":
      return { ...state, status: "validating", progress: 50, message: "Validando configurações..." };
    case "EMBEDDING":
      return { ...state, status: "embedding", progress: action.progress, message: "Carregando dashboard..." };
    case "READY":
      return { ...state, status: "ready", progress: 100, error: null, message: "Dashboard carregado com sucesso!" };
    case "ERROR":
      return { ...state, status: "error", error: action.error, message: `Erro: ${action.error}` };
    case "TIMEOUT":
      return { ...state, status: "timeout", error: "Timeout ao carregar dashboard", message: "Tempo limite excedido" };
    case "RETRY":
      return { ...state, retryCount: state.retryCount + 1, status: "fetching-token", progress: 10, error: null, message: `Tentando novamente (${state.retryCount + 1}/3)...` };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

/**
 * DashboardViewer v2 - Arquitetura completamente diferente
 * 
 * Ao invés de tentar embedar direto no DOM com complexos gerenciadores de ciclo de vida,
 * esta versão usa um sistema de "container controller" que:
 * 
 * 1. Separa completamente o ciclo de vida do Power BI do React
 * 2. Usa um container dedicado com reset forçado entre mudanças
 * 3. Implementa validação rigorosa antes de qualquer operação
 * 4. Usa um state machine simples e previsível
 * 5. Retry automático silencioso para erros de URL
 */
export default function DashboardViewer({ dashboard }: DashboardViewerProps) {
  const [state, dispatch] = useReducer(stateReducer, initialState);
  
  // Refs para gerenciamento do ciclo de vida
  const containerRef = useRef<HTMLDivElement>(null);
  const serviceRef = useRef<pbi.service.Service | null>(null);
  const reportRef = useRef<pbi.Report | null>(null);
  const isMountedRef = useRef(true);
  const sessionIdRef = useRef<string>(Math.random().toString(36));
  const retryTimeoutRef = useRef<NodeJS.Timeout>();
  const embedTimeoutRef = useRef<NodeJS.Timeout>();
  
  // Estado do dashboard
  const [currentDashboardId, setCurrentDashboardId] = useState(dashboard.report_id);
  const [autoRetryActive, setAutoRetryActive] = useState(false);

  /**
   * FASE 1: Obter token do backend
   */
  const fetchEmbedToken = useCallback(async (sessionId: string) => {
    try {
      dispatch({ type: "FETCHING_TOKEN" });

      const response = await apiFetch(
        `/powerbi/embed-token/${dashboard.report_id}?datasetId=${dashboard.dataset_id}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Falha ao obter token`);
      }

      const data = await response.json();

      if (!data.token || !data.embedUrl) {
        throw new Error("Resposta inválida do servidor: token ou URL ausentes");
      }

      return { token: data.token, embedUrl: data.embedUrl };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro desconhecido";
      throw new Error(`Falha ao obter token: ${message}`);
    }
  }, [dashboard.report_id, dashboard.dataset_id]);

  /**
   * FASE 2: Validar URL de embed
   */
  const validateEmbedUrl = useCallback((url: string): boolean => {
    if (!url || typeof url !== "string") {
      console.error("[DashboardViewer] URL inválida: tipo incorreto");
      return false;
    }

    // Validação rigorosa
    const checks = [
      {
        name: "HTTPS Protocol",
        test: () => url.startsWith("https://"),
        error: "URL deve usar HTTPS"
      },
      {
        name: "PowerBI Domain",
        test: () => url.includes("app.powerbi.com"),
        error: "Domínio deve ser app.powerbi.com"
      },
      {
        name: "Embed Endpoint",
        test: () => url.includes("/reportEmbed"),
        error: "URL deve conter /reportEmbed"
      },
      {
        name: "Query Parameters",
        test: () => {
          try {
            const urlObj = new URL(url);
            return urlObj.searchParams.has("reportId");
          } catch {
            return false;
          }
        },
        error: "URL deve conter reportId"
      }
    ];

    for (const check of checks) {
      if (!check.test()) {
        console.error(`[DashboardViewer] Validação falhou: ${check.name} - ${check.error}`);
        return false;
      }
    }

    console.log("[DashboardViewer] URL validada com sucesso");
    return true;
  }, []);

  /**
   * FASE 3: Limpar container completamente
   */
  const cleanContainer = useCallback(async () => {
    if (!containerRef.current) return;

    // Remover todos os filhos
    while (containerRef.current.firstChild) {
      containerRef.current.removeChild(containerRef.current.firstChild);
    }

    // Resetar atributos
    containerRef.current.innerHTML = "";
    containerRef.current.className = "dashboard-embed-container";
    containerRef.current.style.cssText = "";

    // Aguardar DOM reflow
    await new Promise(resolve => setTimeout(resolve, 100));
  }, []);

  /**
   * FASE 4: Criar nova instância do Power BI Service
   */
  const createNewService = useCallback(() => {
    // Sempre criar nova instância
    serviceRef.current = new pbi.service.Service(
      pbi.factories.hpmFactory,
      pbi.factories.wpmpFactory,
      pbi.factories.routerFactory
    );
    console.log("[DashboardViewer] Novo Power BI Service criado");
  }, []);

  /**
   * FASE 5: Executar embed (a parte crítica)
   */
  const performEmbed = useCallback(async (token: string, embedUrl: string, sessionId: string) => {
    return new Promise<void>((resolve, reject) => {
      if (!containerRef.current || !serviceRef.current || !isMountedRef.current) {
        reject(new Error("Container ou Service não disponível"));
        return;
      }

      if (sessionId !== sessionIdRef.current) {
        reject(new Error("Sessão cancelada"));
        return;
      }

      try {
        // Mostrar container
        containerRef.current.style.display = "block";

        // Configuração minimal e robusta
        const config: pbi.IReportEmbedConfiguration = {
          type: "report",
          id: dashboard.report_id,
          embedUrl: embedUrl,
          accessToken: token,
          tokenType: pbi.models.TokenType.Embed,
          permissions: pbi.models.Permissions.Read,
          settings: {
            filterPaneEnabled: true,
            navContentPaneEnabled: true,
            background: pbi.models.BackgroundType.Transparent,
            layoutType: pbi.models.LayoutType.Custom,
            customLayout: {
              displayOption: pbi.models.DisplayOption.FitToWidth,
            }
          }
        };

        // Fazer o embed
        const report = serviceRef.current.embed(containerRef.current, config) as pbi.Report;
        reportRef.current = report;

        // Setup de timeout
        let didResolve = false;
        const timeoutHandle = setTimeout(() => {
          if (!didResolve && isMountedRef.current) {
            didResolve = true;
            reject(new Error("Timeout ao aguardar renderização (45s)"));
          }
        }, 45000);

        // Handlers de evento
        const handleLoaded = () => {
          dispatch({ type: "EMBEDDING", progress: 85 });
          console.log("[DashboardViewer] Relatório carregado");
        };

        const handleRendered = () => {
          if (!didResolve && isMountedRef.current) {
            didResolve = true;
            clearTimeout(timeoutHandle);
            console.log("[DashboardViewer] Relatório renderizado com sucesso");
            resolve();
          }
        };

        const handleError = (event: any) => {
          const errorMsg = event?.detail?.message || "Erro desconhecido";
          console.error("[DashboardViewer] Erro do relatório:", errorMsg);
          
          if (!didResolve && isMountedRef.current) {
            didResolve = true;
            clearTimeout(timeoutHandle);
            reject(new Error(errorMsg));
          }
        };

        // Registrar eventos
        report.on("loaded", handleLoaded);
        report.on("rendered", handleRendered);
        report.on("error", handleError);

      } catch (err) {
        reject(err);
      }
    });
  }, [dashboard.report_id]);

  /**
   * ORQUESTRADOR: Coordena todo o fluxo de carregamento
   */
  const loadDashboard = useCallback(async (isRetry = false) => {
    // Gerar novo ID de sessão para cancelar tentativas anteriores
    const sessionId = Math.random().toString(36);
    sessionIdRef.current = sessionId;

    if (isRetry) {
      dispatch({ type: "RETRY" });
      setAutoRetryActive(true);
    } else {
      dispatch({ type: "START" });
      setAutoRetryActive(false);
    }

    try {
      // 1. Obter token
      const { token, embedUrl } = await fetchEmbedToken(sessionId);
      
      if (sessionId !== sessionIdRef.current) throw new Error("Sessão cancelada");

      // 2. Validar URL
      dispatch({ type: "VALIDATING" });
      if (!validateEmbedUrl(embedUrl)) {
        throw new Error("URL de embed inválida");
      }

      if (sessionId !== sessionIdRef.current) throw new Error("Sessão cancelada");

      // 3. Preparar ambiente
      dispatch({ type: "EMBEDDING", progress: 60 });
      
      // Limpar container
      await cleanContainer();

      // Criar novo service
      createNewService();

      if (sessionId !== sessionIdRef.current) throw new Error("Sessão cancelada");

      // 4. Executar embed
      dispatch({ type: "EMBEDDING", progress: 75 });
      await performEmbed(token, embedUrl, sessionId);

      // 5. Sucesso!
      dispatch({ type: "READY" });
      setAutoRetryActive(false);

    } catch (err) {
      if (!isMountedRef.current || sessionId !== sessionIdRef.current) {
        return; // Componente desmontado ou sessão cancelada
      }

      const error = err instanceof Error ? err.message : "Erro desconhecido";
      console.error("[DashboardViewer] Erro ao carregar:", error);

      // Verificar se é erro de URL e tentar novamente automaticamente
      const isUrlError = error.includes("Invalid embed URL") || 
                         error.includes("URL") ||
                         error.includes("embed");

      if (isUrlError && state.retryCount < 3) {
        console.warn("[DashboardViewer] Erro de URL detectado, tentando novamente automaticamente...");
        
        // Aguardar antes de tentar novamente
        retryTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current && sessionId === sessionIdRef.current) {
            loadDashboard(true);
          }
        }, 1000);
      } else if (state.retryCount >= 3) {
        dispatch({ type: "ERROR", error: "Falha após múltiplas tentativas. Por favor, recarregue a página." });
      } else {
        dispatch({ type: "ERROR", error });
      }
    }
  }, [fetchEmbedToken, validateEmbedUrl, cleanContainer, createNewService, performEmbed, state.retryCount]);

  /**
   * EFEITO: Detectar mudança de dashboard e carregar automaticamente
   */
  useEffect(() => {
    if (currentDashboardId !== dashboard.report_id) {
      console.log(`[DashboardViewer] Dashboard alterado: ${dashboard.title}`);
      
      setCurrentDashboardId(dashboard.report_id);
      
      // Cancelar tentativas anteriores
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (embedTimeoutRef.current) {
        clearTimeout(embedTimeoutRef.current);
      }
      
      // Resetar estado
      dispatch({ type: "RESET" });
      
      // Limpar container
      cleanContainer();
      
      // Carregar novo dashboard
      loadDashboard(false);
    }
  }, [dashboard.report_id, dashboard.title, currentDashboardId, cleanContainer, loadDashboard]);

  /**
   * EFEITO: Auto-iniciar carregamento na montagem
   */
  useEffect(() => {
    isMountedRef.current = true;
    loadDashboard(false);

    return () => {
      isMountedRef.current = false;
      
      // Limpar timeouts
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      if (embedTimeoutRef.current) clearTimeout(embedTimeoutRef.current);

      // Limpar Power BI
      if (reportRef.current) {
        try {
          reportRef.current.off("loaded");
          reportRef.current.off("rendered");
          reportRef.current.off("error");
        } catch (e) {
          // Ignorar
        }
      }

      // Limpar container
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, [loadDashboard]);

  // Handlers de UI
  const handleRetry = () => {
    loadDashboard(true);
  };

  const handleReset = () => {
    dispatch({ type: "RESET" });
    loadDashboard(false);
  };

  // Renderização
  return (
    <div className="w-full h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header com status */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  state.status === "ready"
                    ? "bg-green-500"
                    : state.status === "error" || state.status === "timeout"
                    ? "bg-red-500"
                    : "bg-blue-500 animate-pulse"
                }`}
              />
              <h2 className="text-sm font-semibold text-slate-900">{dashboard.title}</h2>
            </div>
          </div>

          {state.status !== "ready" && (
            <div className="text-xs text-slate-600">{state.message}</div>
          )}

          {state.status === "ready" && (
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span className="text-xs font-medium text-green-600">Carregado</span>
            </div>
          )}
        </div>

        {/* Progress bar */}
        {state.status !== "ready" && state.status !== "error" && state.status !== "idle" && (
          <div className="mt-2 w-full bg-slate-200 h-1 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${state.progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Container principal */}
      <div className="flex-1 relative overflow-hidden">
        {/* Estado: Idle (antes de começar) */}
        {state.status === "idle" && !autoRetryActive && (
          <div className="absolute inset-0 flex items-center justify-center bg-white">
            <div className="text-center max-w-sm">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-50 mb-4">
                <AlertCircle className="w-8 h-8 text-blue-500" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                {dashboard.title}
              </h3>
              <p className="text-sm text-slate-600 mb-6">{dashboard.description}</p>
              <button
                onClick={handleReset}
                className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                <AlertCircle className="w-4 h-4" />
                Carregar Dashboard
              </button>
            </div>
          </div>
        )}

        {/* Estado: Carregando */}
        {(state.status === "fetching-token" ||
          state.status === "validating" ||
          state.status === "embedding") && (
          <div className="absolute inset-0 flex items-center justify-center bg-white">
            <div className="text-center">
              <Loader2 className="w-10 h-10 animate-spin text-blue-500 mx-auto mb-4" />
              <p className="text-sm font-medium text-slate-900">{state.message}</p>
              <p className="text-xs text-slate-500 mt-1">
                {Math.round(state.progress)}%
              </p>
            </div>
          </div>
        )}

        {/* Estado: Erro */}
        {(state.status === "error" || state.status === "timeout") && !autoRetryActive && (
          <div className="absolute inset-0 flex items-center justify-center bg-white">
            <div className="max-w-sm text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 mb-4">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                Falha ao carregar dashboard
              </h3>
              <p className="text-sm text-slate-600 mb-6 break-words">
                {state.error || "Erro desconhecido"}
              </p>
              <div className="flex gap-2 justify-center">
                <button
                  onClick={handleRetry}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
                >
                  <RefreshCw className="w-4 h-4" />
                  Tentar Novamente
                </button>
                <button
                  onClick={handleReset}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition-colors font-medium text-sm"
                >
                  <AlertCircle className="w-4 h-4" />
                  Resetar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Container do dashboard (Power BI) */}
        <div
          ref={containerRef}
          className="dashboard-embed-container absolute inset-0"
          style={{ display: state.status === "ready" ? "block" : "none" }}
        />

        {/* Retry automático silencioso */}
        {autoRetryActive && (
          <div className="absolute bottom-4 right-4 bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700 flex items-center gap-2">
            <Loader2 className="w-3 h-3 animate-spin" />
            Tentando novamente...
          </div>
        )}
      </div>

      {/* Footer com info */}
      {state.status === "ready" && (
        <div className="bg-white border-t border-slate-200 px-6 py-2 text-xs text-slate-500">
          Dashboard carregado com sucesso • ID: {dashboard.report_id.substring(0, 12)}...
        </div>
      )}
    </div>
  );
}
