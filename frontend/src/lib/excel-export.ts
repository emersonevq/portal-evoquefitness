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

// ========================================
// CONFIGURAÇÃO DE ESTILOS PADRONIZADOS
// ========================================
const THEME_COLORS = {
  header: {
    background: "FF366092", // Azul escuro (mesmo do backend)
    text: "FFFFFFFF",        // Branco
  },
  highlight: "FFFFC000",     // Laranja (para destaques)
  success: "FF70AD47",       // Verde
  error: "FFC00000",         // Vermelho
  warning: "FFFFF2CC",       // Amarelo claro
  rowAlternate: "FFF2F2F2",  // Cinza claro para linhas alternadas
  border: "FFD3D3D3",        // Cinza para bordas
};

const FONT_CONFIG = {
  standard: "Arial",
  headerSize: 11,
  dataSize: 10,
  titleSize: 14,
};

// ========================================
// FUNÇÃO PRINCIPAL DE EXPORTAÇÃO
// ========================================
export async function exportToExcel(
  data: ReportData,
  fileName: string = "relatorio_chamados_30dias.xlsx"
) {
  if (!data.tickets || data.tickets.length === 0) {
    alert("Nenhum dado disponível para exportar");
    return;
  }

  const workbook = new ExcelJS.Workbook();

  // Configurar propriedades do workbook
  workbook.creator = "Sistema de Chamados";
  workbook.created = new Date();
  workbook.modified = new Date();

  // Criar abas
  createTicketsSheet(workbook, data);
  createSummarySheet(workbook, data);

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

// ========================================
// ABA 1: LISTA DE CHAMADOS
// ========================================
function createTicketsSheet(workbook: ExcelJS.Workbook, data: ReportData) {
  const worksheet = workbook.addWorksheet("Chamados", {
    pageSetup: { paperSize: 9, orientation: "landscape" },
  });

  // Definir colunas
  const columns = [
    { header: "#", key: "numero", width: 6 },
    { header: "Código", key: "codigo", width: 12 },
    { header: "Protocolo", key: "protocolo", width: 15 },
    { header: "Solicitante", key: "solicitante", width: 25 },
    { header: "Problema", key: "problema", width: 25 },
    { header: "Descrição", key: "descricao", width: 35 },
    { header: "Status", key: "status", width: 15 },
    { header: "Prioridade", key: "prioridade", width: 12 },
    { header: "Unidade", key: "unidade", width: 25 },
    { header: "Data Abertura", key: "data_abertura", width: 16 },
    { header: "Data Conclusão", key: "data_conclusao", width: 16 },
    { header: "Última Atualização", key: "data_ultima_atualizacao", width: 18 },
  ];

  worksheet.columns = columns;

  // Estilo do cabeçalho com o tema padronizado
  const headerRow = worksheet.getRow(1);
  headerRow.height = 25;
  headerRow.font = {
    bold: true,
    color: { argb: THEME_COLORS.header.text },
    size: FONT_CONFIG.headerSize,
    name: FONT_CONFIG.standard,
  };
  headerRow.fill = {
    type: "pattern",
    pattern: "solid",
    fgColor: { argb: THEME_COLORS.header.background },
  };
  headerRow.alignment = {
    horizontal: "center",
    vertical: "center",
    wrapText: true,
  };

  // Adicionar bordas ao cabeçalho
  headerRow.eachCell({ includeEmpty: true }, (cell) => {
    cell.border = {
      top: { style: "thin" },
      left: { style: "thin" },
      bottom: { style: "thin" },
      right: { style: "thin" },
    };
  });

  // Adicionar dados
  data.tickets.forEach((ticket, index) => {
    const row = worksheet.addRow({
      numero: index + 1,
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
        fgColor: { argb: THEME_COLORS.rowAlternate },
      };
    }

    // Estilo das células
    row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
      cell.border = {
        top: { style: "thin", color: { argb: THEME_COLORS.border } },
        left: { style: "thin", color: { argb: THEME_COLORS.border } },
        bottom: { style: "thin", color: { argb: THEME_COLORS.border } },
        right: { style: "thin", color: { argb: THEME_COLORS.border } },
      };

      // Alinhamento específico por coluna
      if (colNumber === 1) {
        // Coluna # - centralizado
        cell.alignment = {
          horizontal: "center",
          vertical: "center",
        };
      } else if (colNumber >= 10 && colNumber <= 12) {
        // Colunas de data - centralizado
        cell.alignment = {
          horizontal: "center",
          vertical: "center",
        };
      } else {
        // Outras colunas - alinhado à esquerda
        cell.alignment = {
          horizontal: "left",
          vertical: "center",
          wrapText: true,
        };
      }

      cell.font = {
        size: FONT_CONFIG.dataSize,
        name: FONT_CONFIG.standard,
      };

      // Colorir status
      if (colNumber === 7) {
        // Coluna Status
        const status = ticket.status?.toLowerCase();
        if (status === "concluído" || status === "resolvido") {
          cell.font = {
            ...cell.font,
            color: { argb: THEME_COLORS.success },
            bold: true,
          };
        } else if (status === "cancelado") {
          cell.font = {
            ...cell.font,
            color: { argb: THEME_COLORS.error },
          };
        }
      }

      // Colorir prioridade
      if (colNumber === 8) {
        // Coluna Prioridade
        const prioridade = ticket.prioridade?.toLowerCase();
        if (prioridade === "alta" || prioridade === "urgente") {
          cell.font = {
            ...cell.font,
            color: { argb: THEME_COLORS.error },
            bold: true,
          };
        } else if (prioridade === "média") {
          cell.font = {
            ...cell.font,
            color: { argb: THEME_COLORS.highlight },
            bold: true,
          };
        }
      }
    });

    row.height = 20;
  });

  // Congelar linha de cabeçalho
  worksheet.views = [{ state: "frozen", ySplit: 1 }];

  // Auto-filtro
  worksheet.autoFilter = {
    from: { row: 1, column: 1 },
    to: { row: data.tickets.length + 1, column: columns.length },
  };
}

// ========================================
// ABA 2: RESUMO E ANÁLISES
// ========================================
function createSummarySheet(workbook: ExcelJS.Workbook, data: ReportData) {
  const worksheet = workbook.addWorksheet("Resumo");

  // Título principal
  worksheet.mergeCells("A1:D1");
  const titleCell = worksheet.getCell("A1");
  titleCell.value = "Resumo de Chamados";
  titleCell.font = {
    bold: true,
    size: FONT_CONFIG.titleSize,
    name: FONT_CONFIG.standard,
    color: { argb: THEME_COLORS.header.background },
  };
  titleCell.alignment = { horizontal: "left", vertical: "center" };
  worksheet.getRow(1).height = 25;

  // Linha em branco
  worksheet.addRow([]);

  // Informações gerais
  let currentRow = 3;
  const addInfoRow = (label: string, value: string | number) => {
    const row = worksheet.getRow(currentRow);
    row.getCell(1).value = label;
    row.getCell(1).font = {
      bold: true,
      size: FONT_CONFIG.dataSize,
      name: FONT_CONFIG.standard,
    };
    row.getCell(2).value = value;
    row.getCell(2).font = {
      size: FONT_CONFIG.dataSize,
      name: FONT_CONFIG.standard,
    };
    currentRow++;
  };

  addInfoRow("Data do Relatório:", formatDate(data.data_relatorio));
  addInfoRow("Total de Chamados:", data.count);
  currentRow++; // Linha em branco

  // Análise por Problema
  const problemCount = countBy(data.tickets, "problema");
  if (Object.keys(problemCount).length > 0) {
    worksheet.getRow(currentRow).getCell(1).value = "Análise por Tipo de Problema";
    worksheet.getRow(currentRow).getCell(1).font = {
      bold: true,
      size: 12,
      name: FONT_CONFIG.standard,
      color: { argb: THEME_COLORS.header.background },
    };
    currentRow += 2;

    // Cabeçalho da tabela
    const headerRow = worksheet.getRow(currentRow);
    ["Tipo de Problema", "Quantidade", "Percentual"].forEach((header, idx) => {
      const cell = headerRow.getCell(idx + 1);
      cell.value = header;
      cell.fill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: THEME_COLORS.header.background },
      };
      cell.font = {
        bold: true,
        color: { argb: THEME_COLORS.header.text },
        size: FONT_CONFIG.headerSize,
        name: FONT_CONFIG.standard,
      };
      cell.alignment = { horizontal: "center", vertical: "center" };
      cell.border = {
        top: { style: "thin" },
        left: { style: "thin" },
        bottom: { style: "thin" },
        right: { style: "thin" },
      };
    });
    currentRow++;

    // Dados da tabela
    const sortedProblems = Object.entries(problemCount).sort(
      ([, a], [, b]) => b - a
    );
    const startDataRow = currentRow;
    sortedProblems.forEach(([problema, count], index) => {
      const row = worksheet.getRow(currentRow);
      row.getCell(1).value = problema;
      row.getCell(2).value = count;
      row.getCell(2).alignment = { horizontal: "center", vertical: "center" };

      // Fórmula de percentual
      row.getCell(3).value = {
        formula: `B${currentRow}/B4`,
        result: count / data.count,
      };
      row.getCell(3).numFmt = "0.0%";
      row.getCell(3).alignment = { horizontal: "center", vertical: "center" };

      // Aplicar bordas e alternância de cores
      [1, 2, 3].forEach((col) => {
        const cell = row.getCell(col);
        cell.border = {
          top: { style: "thin", color: { argb: THEME_COLORS.border } },
          left: { style: "thin", color: { argb: THEME_COLORS.border } },
          bottom: { style: "thin", color: { argb: THEME_COLORS.border } },
          right: { style: "thin", color: { argb: THEME_COLORS.border } },
        };
        cell.font = {
          size: FONT_CONFIG.dataSize,
          name: FONT_CONFIG.standard,
        };
        if (index % 2 === 0) {
          cell.fill = {
            type: "pattern",
            pattern: "solid",
            fgColor: { argb: THEME_COLORS.rowAlternate },
          };
        }
      });

      currentRow++;
    });
    currentRow += 2;
  }

  // Análise por Status
  const statusCount = countBy(data.tickets, "status");
  if (Object.keys(statusCount).length > 0) {
    worksheet.getRow(currentRow).getCell(1).value = "Análise por Status";
    worksheet.getRow(currentRow).getCell(1).font = {
      bold: true,
      size: 12,
      name: FONT_CONFIG.standard,
      color: { argb: THEME_COLORS.header.background },
    };
    currentRow += 2;

    // Cabeçalho da tabela
    const headerRow = worksheet.getRow(currentRow);
    ["Status", "Quantidade", "Percentual"].forEach((header, idx) => {
      const cell = headerRow.getCell(idx + 1);
      cell.value = header;
      cell.fill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: THEME_COLORS.header.background },
      };
      cell.font = {
        bold: true,
        color: { argb: THEME_COLORS.header.text },
        size: FONT_CONFIG.headerSize,
        name: FONT_CONFIG.standard,
      };
      cell.alignment = { horizontal: "center", vertical: "center" };
      cell.border = {
        top: { style: "thin" },
        left: { style: "thin" },
        bottom: { style: "thin" },
        right: { style: "thin" },
      };
    });
    currentRow++;

    // Dados da tabela
    const sortedStatus = Object.entries(statusCount).sort(
      ([, a], [, b]) => b - a
    );
    sortedStatus.forEach(([status, count], index) => {
      const row = worksheet.getRow(currentRow);
      row.getCell(1).value = status;
      row.getCell(2).value = count;
      row.getCell(2).alignment = { horizontal: "center", vertical: "center" };

      // Fórmula de percentual
      row.getCell(3).value = {
        formula: `B${currentRow}/B4`,
        result: count / data.count,
      };
      row.getCell(3).numFmt = "0.0%";
      row.getCell(3).alignment = { horizontal: "center", vertical: "center" };

      // Aplicar bordas e cores
      [1, 2, 3].forEach((col) => {
        const cell = row.getCell(col);
        cell.border = {
          top: { style: "thin", color: { argb: THEME_COLORS.border } },
          left: { style: "thin", color: { argb: THEME_COLORS.border } },
          bottom: { style: "thin", color: { argb: THEME_COLORS.border } },
          right: { style: "thin", color: { argb: THEME_COLORS.border } },
        };
        cell.font = {
          size: FONT_CONFIG.dataSize,
          name: FONT_CONFIG.standard,
        };
        if (index % 2 === 0) {
          cell.fill = {
            type: "pattern",
            pattern: "solid",
            fgColor: { argb: THEME_COLORS.rowAlternate },
          };
        }
      });

      currentRow++;
    });
    currentRow += 2;
  }

  // Análise por Prioridade
  const priorityCount = countBy(data.tickets, "prioridade");
  if (Object.keys(priorityCount).length > 0) {
    worksheet.getRow(currentRow).getCell(1).value = "Análise por Prioridade";
    worksheet.getRow(currentRow).getCell(1).font = {
      bold: true,
      size: 12,
      name: FONT_CONFIG.standard,
      color: { argb: THEME_COLORS.header.background },
    };
    currentRow += 2;

    // Cabeçalho da tabela
    const headerRow = worksheet.getRow(currentRow);
    ["Prioridade", "Quantidade", "Percentual"].forEach((header, idx) => {
      const cell = headerRow.getCell(idx + 1);
      cell.value = header;
      cell.fill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: THEME_COLORS.header.background },
      };
      cell.font = {
        bold: true,
        color: { argb: THEME_COLORS.header.text },
        size: FONT_CONFIG.headerSize,
        name: FONT_CONFIG.standard,
      };
      cell.alignment = { horizontal: "center", vertical: "center" };
      cell.border = {
        top: { style: "thin" },
        left: { style: "thin" },
        bottom: { style: "thin" },
        right: { style: "thin" },
      };
    });
    currentRow++;

    // Dados da tabela
    const priorityOrder = ["Urgente", "Alta", "Média", "Baixa"];
    const sortedPriority = Object.entries(priorityCount).sort((a, b) => {
      const indexA = priorityOrder.indexOf(a[0]);
      const indexB = priorityOrder.indexOf(b[0]);
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    });

    sortedPriority.forEach(([prioridade, count], index) => {
      const row = worksheet.getRow(currentRow);
      row.getCell(1).value = prioridade;
      row.getCell(2).value = count;
      row.getCell(2).alignment = { horizontal: "center", vertical: "center" };

      // Fórmula de percentual
      row.getCell(3).value = {
        formula: `B${currentRow}/B4`,
        result: count / data.count,
      };
      row.getCell(3).numFmt = "0.0%";
      row.getCell(3).alignment = { horizontal: "center", vertical: "center" };

      // Aplicar bordas e cores
      [1, 2, 3].forEach((col) => {
        const cell = row.getCell(col);
        cell.border = {
          top: { style: "thin", color: { argb: THEME_COLORS.border } },
          left: { style: "thin", color: { argb: THEME_COLORS.border } },
          bottom: { style: "thin", color: { argb: THEME_COLORS.border } },
          right: { style: "thin", color: { argb: THEME_COLORS.border } },
        };
        cell.font = {
          size: FONT_CONFIG.dataSize,
          name: FONT_CONFIG.standard,
        };
        if (index % 2 === 0) {
          cell.fill = {
            type: "pattern",
            pattern: "solid",
            fgColor: { argb: THEME_COLORS.rowAlternate },
          };
        }
      });

      currentRow++;
    });
    currentRow += 2;
  }

  // Top 5 Unidades com mais chamados
  const unidadeCount = countBy(data.tickets, "unidade");
  if (Object.keys(unidadeCount).length > 0) {
    worksheet.getRow(currentRow).getCell(1).value = "Top 5 Unidades com Mais Chamados";
    worksheet.getRow(currentRow).getCell(1).font = {
      bold: true,
      size: 12,
      name: FONT_CONFIG.standard,
      color: { argb: THEME_COLORS.header.background },
    };
    currentRow += 2;

    // Cabeçalho da tabela
    const headerRow = worksheet.getRow(currentRow);
    ["Unidade", "Quantidade", "Percentual"].forEach((header, idx) => {
      const cell = headerRow.getCell(idx + 1);
      cell.value = header;
      cell.fill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: THEME_COLORS.header.background },
      };
      cell.font = {
        bold: true,
        color: { argb: THEME_COLORS.header.text },
        size: FONT_CONFIG.headerSize,
        name: FONT_CONFIG.standard,
      };
      cell.alignment = { horizontal: "center", vertical: "center" };
      cell.border = {
        top: { style: "thin" },
        left: { style: "thin" },
        bottom: { style: "thin" },
        right: { style: "thin" },
      };
    });
    currentRow++;

    // Top 5 unidades
    const topUnidades = Object.entries(unidadeCount)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);

    topUnidades.forEach(([unidade, count], index) => {
      const row = worksheet.getRow(currentRow);
      row.getCell(1).value = unidade;
      row.getCell(2).value = count;
      row.getCell(2).alignment = { horizontal: "center", vertical: "center" };

      // Fórmula de percentual
      row.getCell(3).value = {
        formula: `B${currentRow}/B4`,
        result: count / data.count,
      };
      row.getCell(3).numFmt = "0.0%";
      row.getCell(3).alignment = { horizontal: "center", vertical: "center" };

      // Aplicar bordas e cores
      [1, 2, 3].forEach((col) => {
        const cell = row.getCell(col);
        cell.border = {
          top: { style: "thin", color: { argb: THEME_COLORS.border } },
          left: { style: "thin", color: { argb: THEME_COLORS.border } },
          bottom: { style: "thin", color: { argb: THEME_COLORS.border } },
          right: { style: "thin", color: { argb: THEME_COLORS.border } },
        };
        cell.font = {
          size: FONT_CONFIG.dataSize,
          name: FONT_CONFIG.standard,
        };
        if (index % 2 === 0) {
          cell.fill = {
            type: "pattern",
            pattern: "solid",
            fgColor: { argb: THEME_COLORS.rowAlternate },
          };
        }
      });

      currentRow++;
    });
  }

  // Ajustar largura das colunas
  worksheet.getColumn(1).width = 30;
  worksheet.getColumn(2).width = 12;
  worksheet.getColumn(3).width = 12;
  worksheet.getColumn(4).width = 15;
}

// ========================================
// FUNÇÕES AUXILIARES
// ========================================
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

function countBy(
  array: TicketData[],
  field: keyof TicketData
): Record<string, number> {
  return array.reduce((acc, item) => {
    const value = String(item[field] || "Não informado");
    acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
}
