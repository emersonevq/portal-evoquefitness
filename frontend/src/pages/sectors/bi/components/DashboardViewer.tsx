import React, { useState, useRef, useEffect } from "react";
import { Dashboard } from "../data/dashboards";
import { Loader } from "lucide-react";
import { apiFetch } from "@/lib/api";
import * as pbi from "powerbi-client";
import confetti from "canvas-confetti";

interface DashboardViewerProps {
  dashboard: Dashboard;
}

const TENANT_ID = "9f45f492-87a3-4214-862d-4c0d080aa136";

export default function DashboardViewer({ dashboard }: DashboardViewerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticating, setIsAuthenticating] = useState(true);
  const [embedError, setEmbedError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const embedContainerRef = useRef<HTMLDivElement | null>(null);
  const reportRef = useRef<pbi.Report | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const triggerConfetti = () => {
    const duration = 2000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    const randomInRange = (min: number, max: number) =>
      Math.random() * (max - min) + min;

    const interval: NodeJS.Timeout = setInterval(() => {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        clearInterval(interval);
        return;
      }

      const particleCount = 50 * (timeLeft / duration);
      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.1, 0.9), y: Math.random() - 0.2 },
      });
    }, 250);
  };

  // Load and embed Power BI report with token
  useEffect(() => {
    let isMounted = true;
    let report: pbi.Report | null = null;

    const embedReport = async () => {
      try {
        setIsLoading(true);
        setIsAuthenticating(true);
        setEmbedError(null);

        // Get embed token
        const tokenResponse = await apiFetch(
          `/powerbi/embed-token/${dashboard.reportId}`,
        );

        if (!tokenResponse.ok) {
          throw new Error(
            `Falha ao obter token de embed: ${tokenResponse.status}`,
          );
        }

        const tokenData = await tokenResponse.json();
        const embedToken = tokenData.token;

        if (!embedToken) {
          throw new Error("Nenhum token de embed recebido");
        }

        if (!isMounted) return;

        const isDevelopmentMode = tokenData.mode === "development";
        if (isDevelopmentMode) {
          console.warn("⚠️ Modo de desenvolvimento: usando token simulado");
        }

        setIsAuthenticating(false);

        // Create Power BI client
        const powerBiClient = new pbi.service.Service(
          pbi.factories.hpmFactory,
          pbi.factories.wpmpFactory,
          pbi.factories.routerFactory,
        );

        // Configure embed config
        const embedConfig: pbi.IReportEmbedConfiguration = {
          type: "report",
          id: dashboard.reportId,
          embedUrl: `https://app.powerbi.com/reportEmbed?reportId=${dashboard.reportId}&ctid=${TENANT_ID}`,
          accessToken: embedToken,
          tokenExpiration: new Date(Date.now() + 60 * 60 * 1000), // 1 hour
          permissions: pbi.models.Permissions.All,
          settings: {
            filterPaneEnabled: true,
            navContentPaneEnabled: true,
            bars: {
              statusBar: {
                visible: true,
              },
            },
          },
        };

        // Embed the report
        if (embedContainerRef.current && isMounted) {
          report = powerBiClient.embed(
            embedContainerRef.current,
            embedConfig as any,
          ) as pbi.Report;
          reportRef.current = report;

          // Handle events
          report.on("loaded", () => {
            if (isMounted) {
              setIsLoading(false);
              triggerConfetti();
            }
          });

          report.on("error", (event: any) => {
            console.error("Report error:", event.detail);
            if (isMounted) {
              setEmbedError("Erro ao carregar relatório");
              setIsLoading(false);
            }
          });
        }
      } catch (error) {
        console.error("Error embedding report:", error);
        if (isMounted) {
          setEmbedError(
            error instanceof Error
              ? error.message
              : "Erro ao carregar dashboard",
          );
          setIsLoading(false);
          setIsAuthenticating(false);
        }
      }
    };

    embedReport();

    return () => {
      isMounted = false;
      if (report) {
        report = null;
      }
    };
  }, [dashboard.reportId]);

  // Sync fullscreen state with browser events
  useEffect(() => {
    const handler = () =>
      setIsFullscreen(
        Boolean(
          (document as any).fullscreenElement ||
            (document as any).webkitFullscreenElement ||
            (document as any).mozFullScreenElement,
        ),
      );
    document.addEventListener("fullscreenchange", handler);
    document.addEventListener("webkitfullscreenchange", handler);
    document.addEventListener("mozfullscreenchange", handler);
    return () => {
      document.removeEventListener("fullscreenchange", handler);
      document.removeEventListener("webkitfullscreenchange", handler);
      document.removeEventListener("mozfullscreenchange", handler);
    };
  }, []);

  const toggleFullscreen = async () => {
    try {
      const docAny = document as any;
      const isInFs = !!(
        docAny.fullscreenElement ||
        docAny.webkitFullscreenElement ||
        docAny.mozFullScreenElement
      );

      if (!isInFs) {
        if (containerRef.current) {
          const el: any = containerRef.current;
          if (el.requestFullscreen) await el.requestFullscreen();
          else if (el.webkitRequestFullscreen)
            await el.webkitRequestFullscreen();
          else if (el.mozRequestFullScreen) await el.mozRequestFullScreen();
          setIsFullscreen(true);
        }
      } else {
        if (document.exitFullscreen) await document.exitFullscreen();
        else if (docAny.webkitExitFullscreen)
          await docAny.webkitExitFullscreen();
        else if (docAny.mozCancelFullScreen) await docAny.mozCancelFullScreen();
        setIsFullscreen(false);
      }
    } catch (e) {
      // ignore
    }
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className="bi-dashboard-header px-4 py-2 border-b bg-white flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-gray-900">
            {dashboard.title}
          </h1>
          <p className="text-xs text-gray-600">{dashboard.description}</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            aria-label={
              isFullscreen ? "Sair da tela cheia" : "Entrar em tela cheia"
            }
            onClick={toggleFullscreen}
            className="bi-control-button"
          >
            {isFullscreen ? (
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M9 9L5 5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M15 15L19 19"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M9 3H5a2 2 0 0 0-2 2v4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M15 21h4a2 2 0 0 0 2-2v-4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M21 9V5a2 2 0 0 0-2-2h-4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M3 15v4a2 2 0 0 0 2 2h4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </button>
        </div>
      </div>

      <div className="flex-1 bi-viewer-outer" ref={containerRef}>
        {isLoading && (
          <div className="bi-loading-overlay">
            <div className="flex flex-col items-center gap-3">
              <Loader className="w-6 h-6 animate-spin text-primary" />
              <p className="text-sm text-gray-600">
                {isAuthenticating ? "Logando..." : "Carregando dashboard..."}
              </p>
            </div>
          </div>
        )}

        {embedError && (
          <div className="bi-loading-overlay">
            <div className="flex flex-col items-center gap-3">
              <div className="text-4xl">⚠️</div>
              <p className="text-sm text-red-600">{embedError}</p>
            </div>
          </div>
        )}

        <div
          className="bi-embed-card"
          ref={embedContainerRef}
          style={{
            width: "100%",
            height: "100%",
            display: embedError ? "none" : "block",
          }}
        />

        {isFullscreen && (
          <button
            onClick={toggleFullscreen}
            className="bi-fullscreen-toggle"
            aria-label="Sair da tela cheia"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
