import { Dashboard, getPowerBIEmbedUrl } from "../data/dashboards";
import { Loader } from "lucide-react";
import { useState } from "react";

interface DashboardViewerProps {
  dashboard: Dashboard;
}

export default function DashboardViewer({ dashboard }: DashboardViewerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const embedUrl = getPowerBIEmbedUrl(dashboard.reportId);

  return (
    <div className="w-full h-full flex flex-col">
      <div className="px-6 py-3 border-b bg-transparent">
        <h1 className="text-lg font-semibold text-primary">
          {dashboard.title}
        </h1>
      </div>

      <div className="flex-1 p-6 bi-viewer-outer">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <Loader className="w-8 h-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Carregando dashboard...
              </p>
            </div>
          </div>
        )}

        <div className="bi-embed-card">
          <iframe
            title={dashboard.title}
            src={embedUrl}
            frameBorder="0"
            allowFullScreen
            onLoad={() => setIsLoading(false)}
            className="bi-embed-iframe"
          />
        </div>
      </div>
    </div>
  );
}
