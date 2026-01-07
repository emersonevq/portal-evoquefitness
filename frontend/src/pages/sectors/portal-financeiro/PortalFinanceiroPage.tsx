import Layout from "@/components/layout/Layout";
import { sectors } from "@/data/sectors";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DollarSign, Plus, BarChart3, FileText } from "lucide-react";

const sector = sectors.find((s) => s.slug === "portal-financeiro")!;

export default function PortalFinanceiroPage() {
  return (
    <Layout>
      <section className="w-full">
        <div className="brand-gradient">
          <div className="container py-10 sm:py-14">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-primary-foreground drop-shadow">
              {sector?.title || "Portal Financeiro"}
            </h1>
            <p className="mt-2 text-primary-foreground/90 max-w-2xl">
              {sector?.description ||
                "Gerencie e acompanhe suas solicitações de compras e despesas."}
            </p>
          </div>
        </div>
      </section>

      <section className="container py-8 sm:py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="card-surface rounded-xl border border-border/40 overflow-hidden hover:shadow-md transition-shadow p-6">
            <div className="flex items-start justify-between mb-4">
              <DollarSign className="w-8 h-8 text-primary" />
            </div>
            <h2 className="font-semibold text-lg mb-2">
              Solicitações de Compra
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              Registre e acompanhe novas solicitações de compra
            </p>
            <Button variant="secondary" className="w-full">
              <Plus className="w-4 h-4 mr-2" />
              Nova Solicitação
            </Button>
          </Card>

          <Card className="card-surface rounded-xl border border-border/40 overflow-hidden hover:shadow-md transition-shadow p-6">
            <div className="flex items-start justify-between mb-4">
              <FileText className="w-8 h-8 text-primary" />
            </div>
            <h2 className="font-semibold text-lg mb-2">Histórico</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Consulte todas as solicitações de compra anteriores
            </p>
            <Button variant="secondary" className="w-full">
              Ver Histórico
            </Button>
          </Card>

          <Card className="card-surface rounded-xl border border-border/40 overflow-hidden hover:shadow-md transition-shadow p-6">
            <div className="flex items-start justify-between mb-4">
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
            <h2 className="font-semibold text-lg mb-2">Relatórios</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Gere relatórios de despesas e gastos com compras
            </p>
            <Button variant="secondary" className="w-full">
              Gerar Relatório
            </Button>
          </Card>
        </div>

        <div className="mt-12">
          <Card className="card-surface rounded-xl border border-border/40 p-6 sm:p-8">
            <h3 className="text-lg font-semibold mb-3">Informações</h3>
            <p className="text-muted-foreground text-sm">
              O Portal Financeiro oferece ferramentas completas para gerenciar
              solicitações de compra, acompanhar despesas e gerar relatórios
              detalhados. Funcionalidades adicionais serão adicionadas conforme
              sua orientação.
            </p>
          </Card>
        </div>
      </section>
    </Layout>
  );
}
