import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";

export interface Dashboard {
  id: number;
  dashboard_id: string;
  title: string;
  description: string | null;
  report_id: string;
  dataset_id: string | null;
  category: string;
  category_name: string;
  order: number;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface DashboardCategory {
  id: string;
  name: string;
  dashboards: Dashboard[];
}

export function useDashboards() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<DashboardCategory[]>([]);

  useEffect(() => {
    const fetchDashboards = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log("[BI] Buscando dashboards do banco de dados...");

        const response = await apiFetch("/powerbi/db/dashboards");

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: Falha ao buscar dashboards`);
        }

        const dashboards: Dashboard[] = await response.json();

        console.log(`[BI] ${dashboards.length} dashboards encontrados`);

        // Group dashboards by category
        const grouped = dashboards.reduce((acc, dashboard) => {
          const existingCategory = acc.find((cat) => cat.id === dashboard.category);

          if (existingCategory) {
            existingCategory.dashboards.push(dashboard);
          } else {
            acc.push({
              id: dashboard.category,
              name: dashboard.category_name,
              dashboards: [dashboard],
            });
          }

          return acc;
        }, [] as DashboardCategory[]);

        // Sort dashboards within each category by order
        grouped.forEach((category) => {
          category.dashboards.sort((a, b) => a.order - b.order);
        });

        setCategories(grouped);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Erro desconhecido";
        console.error("[BI] Erro ao buscar dashboards:", message);
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboards();
  }, []);

  const getDashboardById = (dashboardId: string): Dashboard | undefined => {
    for (const category of categories) {
      const dashboard = category.dashboards.find((d) => d.dashboard_id === dashboardId);
      if (dashboard) return dashboard;
    }
    return undefined;
  };

  return {
    categories,
    loading,
    error,
    getDashboardById,
  };
}
