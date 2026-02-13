import ExcelJS from "exceljs";

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

export async function exportToExcel(
  data: ReportData,
  fileName: string = "relatorio_chamados_30dias.xlsx"
) {
  if (!data.tickets || data.tickets.length === 0) {
    alert("Nenhum dado disponível para exportar");
    return;
  }

  // Criar workbook
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet("Chamados", {
    pageSetup: { paperSize: 9, orientation: "landscape" },
  });

  // Definir colunas
  const columns = [
    { header: "ID", key: "id", width: 8 },
    { header: "Código do Chamado", key: "codigo", width: 15 },
    { header: "Protocolo", key: "protocolo", width: 15 },
    { header: "Nome do Solicitante", key: "solicitante", width: 25 },
    { header: "Problema Reportado", key: "problema", width: 25 },
    { header: "Descrição", key: "descricao", width: 30 },
    { header: "Status", key: "status", width: 15 },
    { header: "Prioridade", key: "prioridade", width: 12 },
    { header: "Unidade", key: "unidade", width: 20 },
    { header: "Data de Abertura", key: "data_abertura", width: 18 },
    { header: "Data de Conclusão", key: "data_conclusao", width: 18 },
    { header: "Última Atualização", key: "data_ultima_atualizacao", width: 18 },
  ];

  worksheet.columns = columns;

  // Estilo do cabeçalho
  const headerRow = worksheet.getRow(1);
  headerRow.height = 25;
  headerRow.font = {
    bold: true,
    color: { argb: "FFFFFFFF" },
    size: 11,
  };
  headerRow.fill = {
    type: "pattern",
    pattern: "solid",
    fgColor: { argb: "FF1F4E78" },
  };
  headerRow.alignment = {
    horizontal: "center",
    vertical: "center",
    wrapText: true,
  };

  // Adicionar dados
  data.tickets.forEach((ticket, index) => {
    const row = worksheet.addRow({
      id: ticket.id,
      codigo: ticket.codigo,
      protocolo: ticket.protocolo,
      solicitante: ticket.solicitante,
      problema: ticket.problema,
      descricao: ticket.descricao,
      status: ticket.status,
      prioridade: ticket.prioridade,
      unidade: ticket.unidade,
      data_abertura: ticket.data_abertura
        ? formatDate(ticket.data_abertura)
        : "-",
      data_conclusao: ticket.data_conclusao
        ? formatDate(ticket.data_conclusao)
        : "-",
      data_ultima_atualizacao: ticket.data_ultima_atualizacao
        ? formatDate(ticket.data_ultima_atualizacao)
        : "-",
    });

    // Alternância de cores nas linhas
    if (index % 2 === 0) {
      row.fill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: "FFF2F2F2" },
      };
    }

    // Bordas e alinhamento
    row.eachCell({ includeEmpty: true }, (cell) => {
      cell.border = {
        top: { style: "thin", color: { argb: "FFD3D3D3" } },
        left: { style: "thin", color: { argb: "FFD3D3D3" } },
        bottom: { style: "thin", color: { argb: "FFD3D3D3" } },
        right: { style: "thin", color: { argb: "FFD3D3D3" } },
      };
      cell.alignment = {
        horizontal: "left",
        vertical: "center",
        wrapText: true,
      };
      cell.font = {
        size: 10,
      };
    });

    row.height = 20;
  });

  // Adicionar bordas ao cabeçalho
  headerRow.eachCell({ includeEmpty: true }, (cell) => {
    cell.border = {
      top: { style: "thin", color: { argb: "FF1F4E78" } },
      left: { style: "thin", color: { argb: "FF1F4E78" } },
      bottom: { style: "medium", color: { argb: "FF1F4E78" } },
      right: { style: "thin", color: { argb: "FF1F4E78" } },
    };
  });

  // Congelar linha de cabeçalho
  worksheet.views = [{ state: "frozen", ySplit: 1 }];

  // Auto-filtro
  worksheet.autoFilter.from = {
    row: 1,
    column: 1,
  };
  worksheet.autoFilter.to = {
    row: data.tickets.length + 1,
    column: columns.length,
  };

  // Salvar arquivo
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  window.URL.revokeObjectURL(url);
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
