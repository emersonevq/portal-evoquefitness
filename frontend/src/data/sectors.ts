import {
  Landmark,
  Megaphone,
  Package,
  Server,
  ShoppingCart,
  Wrench,
  Briefcase,
  Layers3,
  BarChart3,
} from "lucide-react";
import type { ComponentType, SVGProps } from "react";

export type IconType = ComponentType<SVGProps<SVGSVGElement>>;

export interface Sector {
  slug: string;
  title: string;
  description: string;
  icon: IconType;
}

export const sectors: Sector[] = [
  {
    slug: "ti",
    title: "Setor de TI",
    description: "Gerencie chamados e otimize serviços de tecnologia.",
    icon: Server,
  },
  {
    slug: "compras",
    title: "Setor de Compras",
    description: "Registre e acompanhe solicitações de compras.",
    icon: ShoppingCart,
  },
  {
    slug: "manutencao",
    title: "Setor de Manutenção",
    description: "Gerencie solicitações e acompanhe reparos.",
    icon: Wrench,
  },
  {
    slug: "portal-bi",
    title: "Portal BI",
    description: "Acesse relatórios e dashboards de análise de dados.",
    icon: BarChart3,
  },
  {
    slug: "financeiro",
    title: "Setor Financeiro",
    description: "Controle financeiro e relatórios de pagamentos.",
    icon: Landmark,
  },
  {
    slug: "marketing",
    title: "Setor de Marketing",
    description: "Planeje campanhas e acompanhe resultados.",
    icon: Megaphone,
  },
  {
    slug: "produtos",
    title: "Setor de Produtos",
    description: "Gerencie produtos e estoques da academia.",
    icon: Package,
  },
  {
    slug: "comercial",
    title: "Setor Comercial",
    description: "Acompanhe vendas e metas comerciais.",
    icon: Briefcase,
  },
  {
    slug: "outros-servicos",
    title: "Outros Serviços",
    description: "Acesse diversos serviços complementares da academia.",
    icon: Layers3,
  },
];
