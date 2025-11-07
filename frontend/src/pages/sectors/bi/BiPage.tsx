import Layout from "@/components/layout/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart3, LineChart } from "lucide-react";

export default function BiPage() {
  return (
    <Layout>
      <div className="container py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-primary mb-2">
            Portal de BI
          </h1>
          <p className="text-muted-foreground">
            Analise dados e visualize insights em dashboards interativos
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="p-6 hover:shadow-lg transition">
            <div className="flex items-start justify-between mb-4">
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
            <h2 className="font-semibold text-lg mb-2">Dashboard Principal</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Visualize KPIs e métricas principais da empresa
            </p>
            <Button variant="outline" className="w-full">
              Acessar Dashboard
            </Button>
          </Card>

          <Card className="p-6 hover:shadow-lg transition">
            <div className="flex items-start justify-between mb-4">
              <LineChart className="w-8 h-8 text-primary" />
            </div>
            <h2 className="font-semibold text-lg mb-2">Relatórios de Desempenho</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Análise detalhada de performance por setor
            </p>
            <Button variant="outline" className="w-full">
              Ver Relatórios
            </Button>
          </Card>

          <Card className="p-6 hover:shadow-lg transition">
            <div className="flex items-start justify-between mb-4">
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
            <h2 className="font-semibold text-lg mb-2">Análise de Dados</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Explore dados e crie visualizações customizadas
            </p>
            <Button variant="outline" className="w-full">
              Explorar Dados
            </Button>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
