import { useState, useEffect, useMemo, useRef } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

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
  const prevCategoriesRef = useRef<DashboardCategory[] | null>(null);
  const isFetchingRef = useRef(false);
  const hasInitializedRef = useRef(false);
  const { user } = useAuth();

  useEffect(() => {
    // Se já inicializou e não há mudanças no usuário, não refetch
    if (hasInitializedRef.current) return;

    const fetchDashboards = async () => {
      // Prevent multiple simultaneous fetches
      if (isFetchingRef.current) {
        console.log(
          "[BI] ⏸️  Fetch já em progresso, ignorando nova requisição",
        );
        return;
      }

      try {
        isFetchingRef.current = true;
        setLoading(true);
        setError(null);

        console.log("[BI] 📥 Buscando dashboards do banco de dados...");

        const response = await apiFetch("/powerbi/db/dashboards");

        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}: Falha ao buscar dashboards do servidor`,
          );
        }

        const dashboards: Dashboard[] = await response.json();

        if (!Array.isArray(dashboards)) {
          throw new Error("Resposta inválida: esperado array de dashboards");
        }

        console.log(`[BI] ✅ ${dashboards.length} dashboards encontrados`);

        // Log cada dashboard para debug
        dashboards.forEach((dash) => {
          console.log(`[BI]   - ${dash.title} (${dash.dashboard_id})`);
          console.log(`[BI]     Report: ${dash.report_id}`);
          console.log(`[BI]     Dataset: ${dash.dataset_id}`);
        });

        // Filter dashboards based on user permissions
        let filteredDashboards = dashboards;
        if (
          user &&
          user.bi_subcategories &&
          Array.isArray(user.bi_subcategories) &&
          user.bi_subcategories.length > 0
        ) {
          console.log(
            `[BI] 🔐 Filtrando dashboards por permissão do usuário:`,
            user.bi_subcategories,
          );
          filteredDashboards = dashboards.filter((dash) =>
            user.bi_subcategories.includes(dash.dashboard_id),
          );
          console.log(
            `[BI] ✅ ${filteredDashboards.length} dashboards após filtragem`,
          );
        } else {
          console.log("[BI] ⚠️ Usuário sem permissões de BI definidas");
        }

        // Group dashboards by category
        const grouped = filteredDashboards.reduce((acc, dashboard) => {
          const existingCategory = acc.find(
            (cat) => cat.id === dashboard.category,
          );

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

        // Only update state if data actually changed
        const dataChanged =
          prevCategoriesRef.current === null ||
          JSON.stringify(prevCategoriesRef.current) !== JSON.stringify(grouped);

        if (dataChanged) {
          console.log(
            `[BI] ✅ Dashboards organizados em ${grouped.length} categorias`,
          );
          prevCategoriesRef.current = grouped;
          setCategories(grouped);
        } else {
          console.log(
            "[BI] ℹ️ Dados de dashboards não mudaram, evitando re-render",
          );
          prevCategoriesRef.current = grouped;
        }

        // Marca como inicializado
        hasInitializedRef.current = true;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Erro desconhecido";
        console.error("[BI] ❌ Erro ao buscar dashboards:", message);
        setError(message);
        // Em caso de erro, permite tentar novamente
        hasInitializedRef.current = false;
      } finally {
        isFetchingRef.current = false;
        setLoading(false);
      }
    };

    fetchDashboards();
  }, []); // Removida a dependência de userPermissionSignature - busca apenas uma vez

  // Efeito separado para monitorar mudanças no usuário OU nas suas permissões
  useEffect(() => {
    // Se o usuário mudou OU as permissões de BI mudaram, resetamos o estado para buscar novos dashboards
    if (user && hasInitializedRef.current) {
      console.log(
        "[BI] 👤 Usuário ou permissões alteradas, resetando dashboards...",
      );
      console.log("[BI] Novas bi_subcategories:", user.bi_subcategories);
      hasInitializedRef.current = false;
      prevCategoriesRef.current = null;
      setCategories([]);
      setLoading(true);
    }
  }, [user?.id, user?.bi_subcategories?.join(",")]); // Monitora ID e BI subcategories

  const getDashboardById = (dashboardId: string): Dashboard | undefined => {
    for (const category of categories) {
      const dashboard = category.dashboards.find(
        (d) => d.dashboard_id === dashboardId,
      );
      if (dashboard) return dashboard;
    }
    return undefined;
  };

  // Função para forçar refresh manual (se necessário)
  const refreshDashboards = () => {
    hasInitializedRef.current = false;
    prevCategoriesRef.current = null;
    setLoading(true);
    setCategories([]);
  };

  return {
    categories,
    loading,
    error,
    getDashboardById,
    refreshDashboards,
  };
}
