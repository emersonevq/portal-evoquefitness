import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Download, TrendingUp } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { exportToExcel } from "@/lib/excel-export";
import { toast } from "sonner";
import { format, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";

interface TicketData {
  id: number;
  codigo: string;
  protocolo: string;
  solicitante: string;
  problema: string;
  descricao: string;
  status: string;
  prioridade: string;
  unidade: string;
  data_abertura: string | null;
  data_conclusao: string | null;
  data_ultima_atualizacao: string | null;
}

interface ReportData {
  count: number;
  total: number;
  data_relatorio: string;
  tickets: TicketData[];
}

interface Props {
  startDate?: string;
  endDate?: string;
}

export default function AttendedTicketsMetric({ startDate, endDate }: Props) {
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        let url = "/chamados/report/last-30-days";

        // Use custom date range if provided
        if (startDate && endDate) {
          url = `/chamados/report?start_date=${startDate}&end_date=${endDate}`;
        }

        const response = await apiFetch(url);

        if (!response.ok) {
          throw new Error("Erro ao buscar dados");
        }

        const data = await response.json();
        setReportData(data);
        setError(null);
      } catch (err) {
        console.error("[ATTENDED TICKETS] Erro:", err);
        setError(
          err instanceof Error ? err.message : "Erro ao carregar dados"
        );
        toast.error("Não foi possível carregar os dados dos chamados");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [startDate, endDate]);

  const handleDownloadExcel = () => {
    if (!reportData) {
      toast.error("Nenhum dado disponível para exportar");
      return;
    }

    try {
      exportToExcel(reportData, "relatorio_chamados_30dias.xlsx");
      toast.success("Relatório baixado com sucesso!");
    } catch (err) {
      console.error("[EXCEL EXPORT] Erro:", err);
      toast.error("Erro ao baixar relatório");
    }
  };

  return (
    <div className="rounded-2xl border border-border/60 bg-gradient-to-br from-blue-50/50 to-indigo-50/50 p-6 sm:p-7 shadow-md hover:shadow-lg transition-all duration-300">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-2">
            {startDate && endDate
              ? `${format(parseISO(startDate), "dd 'de' MMM", { locale: ptBR })} até ${format(parseISO(endDate), "dd 'de' MMM 'de' yyyy", { locale: ptBR })}`
              : "Últimos 30 Dias"}
          </h3>
          {loading ? (
            <div className="h-12 w-32 bg-gray-200 animate-pulse rounded" />
          ) : error ? (
            <div className="text-sm text-red-600">{error}</div>
          ) : (
            <div className="flex items-end gap-3">
              <span className="text-4xl sm:text-5xl font-black text-blue-600">
                {reportData?.count || 0}
              </span>
              <span className="text-sm text-muted-foreground mb-1">
                chamados atendidos
              </span>
            </div>
          )}
        </div>
        <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-xl">
          <TrendingUp className="w-6 h-6 text-blue-600" />
        </div>
      </div>

      {/* Separator */}
      <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent mb-6" />

      {/* Download Button */}
      <Button
        onClick={handleDownloadExcel}
        disabled={loading || !reportData || (reportData.count === 0 && !loading)}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-all duration-300 flex items-center justify-center gap-2"
      >
        <Download className="w-4 h-4" />
        Baixar Relatório em Excel
      </Button>

      {/* Additional info */}
      {reportData && reportData.count > 0 && (
        <p className="text-xs text-muted-foreground mt-3 text-center">
          Inclui detalhes completos: ID, código, solicitante, problema, status,
          datas de abertura e conclusão
        </p>
      )}
    </div>
  );
}
