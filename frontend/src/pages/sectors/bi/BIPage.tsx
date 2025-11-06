import Layout from "@/components/layout/Layout";
import { sectors } from "@/data/sectors";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const sector = sectors.find((s) => s.slug === "portal-bi")!;

const dashboards = [
  {
    slug: "analise-ocs",
    title: "Análise de OC's",
    description: "Visualize análises detalhadas de ordens de compra",
  },
  {
    slug: "central-relacionamento",
    title: "Central de relacionamento",
    description: "Acompanhe as interações e relacionamento com clientes",
  },
  {
    slug: "central-vendas",
    title: "Central de vendas",
    description: "Monitore o desempenho de vendas em tempo real",
  },
  {
    slug: "comercial",
    title: "Comercial",
    description: "Análise completa de dados comerciais",
  },
  {
    slug: "controle-cotas",
    title: "Controle de cotas",
    description: "Gerencie e acompanhe as cotas estabelecidas",
  },
  {
    slug: "fiscal",
    title: "Fiscal",
    description: "Informações fiscais e de compliance",
  },
  {
    slug: "produtos",
    title: "Produtos",
    description: "Análise de produtos e inventário",
  },
];

export default function BIPage() {
  return (
    <Layout>
      <section className="w-full">
        <div className="brand-gradient">
          <div className="container py-10 sm:py-14">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-primary-foreground drop-shadow">
              {sector.title}
            </h1>
            <p className="mt-2 text-primary-foreground/90 max-w-2xl">
              {sector.description}
            </p>
          </div>
        </div>
      </section>

      <section className="container py-8 sm:py-12">
        <h2 className="text-xl sm:text-2xl font-bold mb-6">Dashboards disponíveis</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {dashboards.map((dashboard) => (
            <Link
              key={dashboard.slug}
              to={`/setor/portal-bi/${dashboard.slug}`}
              className="card-surface group rounded-xl p-6 transition hover:shadow-lg hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <h3 className="font-semibold text-base mb-2">{dashboard.title}</h3>
              <p className="text-sm text-muted-foreground">{dashboard.description}</p>
              <div className="mt-4">
                <Button size="sm" className="rounded-full">
                  Acessar
                </Button>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </Layout>
  );
}
