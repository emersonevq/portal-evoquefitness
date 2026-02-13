import * as XLSX from "xlsx";

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

export function exportToExcel(data: ReportData, fileName: string = "relatorio_chamados_30dias.xlsx") {
  if (!data.tickets || data.tickets.length === 0) {
    alert("Nenhum dado disponível para exportar");
    return;
  }

  // Preparar dados formatados para o Excel
  const formattedData = data.tickets.map((ticket) => ({
    "ID": ticket.id,
    "Código do Chamado": ticket.codigo,
    "Protocolo": ticket.protocolo,
    "Nome do Solicitante": ticket.solicitante,
    "Problema Reportado": ticket.problema,
    "Descrição": ticket.descricao,
    "Status": ticket.status,
    "Prioridade": ticket.prioridade,
    "Unidade": ticket.unidade,
    "Data de Abertura": ticket.data_abertura ? formatDate(ticket.data_abertura) : "-",
    "Data de Conclusão": ticket.data_conclusao ? formatDate(ticket.data_conclusao) : "-",
    "Última Atualização": ticket.data_ultima_atualizacao ? formatDate(ticket.data_ultima_atualizacao) : "-",
  }));

  // Criar workbook
  const ws = XLSX.utils.json_to_sheet(formattedData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Chamados");

  // Configurar largura das colunas
  const columnWidths = [
    { wch: 8 },   // ID
    { wch: 15 },  // Código
    { wch: 15 },  // Protocolo
    { wch: 25 },  // Solicitante
    { wch: 25 },  // Problema
    { wch: 30 },  // Descrição
    { wch: 15 },  // Status
    { wch: 12 },  // Prioridade
    { wch: 20 },  // Unidade
    { wch: 18 },  // Data de Abertura
    { wch: 18 },  // Data de Conclusão
    { wch: 18 },  // Última Atualização
  ];
  ws["!cols"] = columnWidths;

  // Salvar arquivo
  XLSX.writeFile(wb, fileName);
}

function formatDate(isoDateString: string): string {
  try {
    const date = new Date(isoDateString);
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoDateString;
  }
}
