import { useState, useEffect } from "react";
import Layout from "@/components/layout/Layout";
import DashboardViewer from "./components/DashboardViewer";
import DashboardSidebar from "./components/DashboardSidebar";
import DashboardGrid from "./components/DashboardGrid";
import { dashboardsData, getAllDashboards, Dashboard, getPowerBIEmbedUrl } from "./data/dashboards";
import { useAuthContext } from "@/lib/auth-context";

export default function BiPage() {
  console.log("[BiPage] Rendering BiPage component!");
  const [selectedDashboard, setSelectedDashboard] = useState<Dashboard | null>(
    getAllDashboards()[0] || null,
  );

  const handleSelectDashboard = (dashboard: Dashboard) => {
    setSelectedDashboard(dashboard);
  };

  // Render viewer-only when user is authenticated, otherwise show sidebar + viewer
  const { user } = useAuthContext();

  return (
    <Layout>
      <div className="bi-page-root">
        {user ? (
          // Authenticated: show only the BI content maximized
          <main className="bi-content full">
            <div className="bi-viewer-outer">
              {selectedDashboard && (
                // render iframe directly to maximize space
                <iframe
                  title={selectedDashboard.title}
                  src={getPowerBIEmbedUrl(selectedDashboard.reportId)}
                  frameBorder="0"
                  allowFullScreen
                  className="bi-embed-iframe full-bleed"
                />
              )}
            </div>
          </main>
        ) : (
          // Not authenticated: show sidebar and viewer with controls
          <>
            <DashboardSidebar
              categories={dashboardsData}
              selectedDashboard={selectedDashboard}
              onSelectDashboard={handleSelectDashboard}
            />

            <main className="bi-content">
              <div className="px-6 py-3 border-b bg-transparent flex items-center gap-4">
                <div className="text-sm text-muted-foreground">☰</div>
                <h1 className="text-sm font-medium text-primary-foreground">
                  {selectedDashboard?.title}
                </h1>
              </div>

              <div className="bi-viewer-outer">
                {selectedDashboard && <DashboardViewer dashboard={selectedDashboard} />}
              </div>
            </main>
          </>
        )}
      </div>
    </Layout>
  );
}
