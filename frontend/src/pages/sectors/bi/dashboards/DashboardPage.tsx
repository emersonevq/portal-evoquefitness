import Layout from "@/components/layout/Layout";
import { useParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

const dashboards: Record<
  string,
  {
    title: string;
    iframeUrl: string;
  }
> = {
  "analise-ocs": {
    title: "Análise de OC's",
    iframeUrl:
      "https://app.powerbi.com/reportEmbed?reportId=8799e0cf-fe55-4670-8a67-ceeee9744bc4&autoAuth=true&ctid=9f45f492-87a3-4214-862d-4c0d080aa136",
  },
  "central-relacionamento": {
    title: "Central de relacionamento",
    iframeUrl:
      "https://app.powerbi.com/reportEmbed?reportId=837fb0a1-d589-4857-ad9d-44a34fb70b05&autoAuth=true&ctid=9f45f492-87a3-4214-862d-4c0d080aa136",
  },
  "central-vendas": {
    title: "Central de vendas",
    iframeUrl:
      "https://app.powerbi.com/reportEmbed?reportId=737afc5a-c604-4583-9e71-3f8e81d0f276&autoAuth=true&ctid=9f45f492-87a3-4214-862d-4c0d080aa136",
  },
  comercial: {
    title: "Comercial",
    iframeUrl:
      "https://app.powerbi.com/reportEmbed?reportId=0117fd5b-b3c0-46ff-8c1e-c35ff5d4bb8d&autoAuth=true&ctid=9f45f492-87a3-4214-862d-4c0d080aa136",
  },
  "controle-cotas": {
    title: "Controle de cotas",
    iframeUrl:
      "https://app.powerbi.com/reportEmbed?reportId=4bc4c1aa-b8c5-4a8a-b3a2-2417cdfb17c2&autoAuth=true&ctid=9f45f492-87a3-4214-862d-4c0d080aa136",
  },
  fiscal: {
    title: "Fiscal",
    iframeUrl:
      "https://app.powerbi.com/reportEmbed?reportId=34adf0c5-d4ff-49ab-bffd-26eef0df797e&autoAuth=true&ctid=9f45f492-87a3-4214-862d-4c0d080aa136",
  },
  produtos: {
    title: "Produtos",
    iframeUrl:
      "https://app.powerbi.com/reportEmbed?reportId=74dc6b4a-8b03-4837-881f-37f6b2d8e6a5&autoAuth=true&ctid=9f45f492-87a3-4214-862d-4c0d080aa136",
  },
};

export default function DashboardPage() {
  const { dashboardId } = useParams<{ dashboardId: string }>();
  const dashboard = dashboardId ? dashboards[dashboardId] : null;

  if (!dashboard) {
    return (
      <Layout>
        <section className="container py-12">
          <div className="rounded-xl border border-border/60 bg-card p-6 sm:p-8">
            <p className="text-muted-foreground">Dashboard não encontrado.</p>
            <div className="mt-4">
              <Link to="/setor/portal-bi">
                <Button variant="outline" className="rounded-full">
                  <ArrowLeft className="size-4 mr-2" /> Voltar
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </Layout>
    );
  }

  return (
    <Layout>
      <section className="w-full">
        <div className="brand-gradient">
          <div className="container py-10 sm:py-14">
            <Link to="/setor/portal-bi" className="inline-block mb-4">
              <Button variant="secondary" size="sm" className="rounded-full">
                <ArrowLeft className="size-4 mr-2" /> Voltar
              </Button>
            </Link>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-primary-foreground drop-shadow">
              {dashboard.title}
            </h1>
          </div>
        </div>
      </section>

      <section className="container py-8">
        <div className="rounded-xl border border-border/60 bg-card overflow-hidden">
          <iframe
            title={dashboard.title}
            width="100%"
            height="541"
            src={dashboard.iframeUrl}
            frameBorder="0"
            allowFullScreen
          />
        </div>
      </section>
    </Layout>
  );
}
