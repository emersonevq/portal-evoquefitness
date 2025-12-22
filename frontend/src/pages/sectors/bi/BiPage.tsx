import { useState, useEffect } from "react";
import Layout from "@/components/layout/Layout";
import DashboardViewer from "./components/DashboardViewer";
import DashboardSidebar from "./components/DashboardSidebar";
import AuthenticationHandler from "./components/AuthenticationHandler";
import { useDashboards } from "./hooks/useDashboards";
import { Loader } from "lucide-react";

export default function BiPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const { categories, loading, error, getDashboardById } = useDashboards();
  const [selectedDashboardId, setSelectedDashboardId] = useState<number | null>(null);

  // Set first dashboard when categories load (only initialize, don't change if already selected)
  useEffect(() => {
    if (!loading && categories.length > 0 && selectedDashboardId === null) {
      const firstDashboard = categories[0]?.dashboards[0];
      if (firstDashboard) {
        setSelectedDashboardId(firstDashboard.id);
      }
    }
  }, [loading, selectedDashboardId]);

  // Get the dashboard object from ID (will be stable as long as the dashboard exists)
  const selectedDashboard = selectedDashboardId !== null
    ? categories.flatMap(c => c.dashboards).find(d => d.id === selectedDashboardId) || null
    : null;

  const handleSelectDashboard = (dashboard: any) => {
    console.log("[BI] 🔄 Trocando dashboard...");
    console.log(
      "[BI] Dashboard anterior:",
      selectedDashboard?.title || "nenhum",
    );
    console.log("[BI] Novo dashboard:", dashboard.title);
    console.log("[BI] Report ID:", dashboard.report_id);
    console.log("[BI] Dataset ID:", dashboard.dataset_id);
    setSelectedDashboardId(dashboard.id);
  };

  return (
    <Layout>
      <AuthenticationHandler onAuthenticated={() => setIsAuthenticated(true)}>
        {isAuthenticated && (
          <div className="bi-page-root">
            {/* Carregando dashboards */}
            {loading && (
              <div className="w-full h-full flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                  <Loader className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-muted-foreground">
                    Carregando dashboards do banco...
                  </p>
                </div>
              </div>
            )}

            {/* Erro ao carregar */}
            {error && (
              <div className="w-full h-full flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                  <div className="text-4xl">⚠️</div>
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              </div>
            )}

            {/* Conteúdo carregado */}
            {!loading && !error && categories.length > 0 && (
              <>
                {/* Sidebar com lista de dashboards */}
                <DashboardSidebar
                  categories={categories}
                  selectedDashboard={selectedDashboard}
                  onSelectDashboard={handleSelectDashboard}
                />

                {/* Área principal de conteúdo */}
                <main className="bi-content">
                  {selectedDashboard && (
                    <DashboardViewer dashboard={selectedDashboard} />
                  )}
                </main>
              </>
            )}

            {/* Sem dashboards */}
            {!loading && !error && categories.length === 0 && (
              <div className="w-full h-full flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                  <div className="text-4xl">📊</div>
                  <p className="text-muted-foreground">
                    Nenhum dashboard disponível
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </AuthenticationHandler>
    </Layout>
  );
}
