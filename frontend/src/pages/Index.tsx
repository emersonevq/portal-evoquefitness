import Layout from "@/components/layout/Layout";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { sectors } from "@/data/sectors";
import { ChevronDown } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuthContext } from "@/lib/auth-context";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";

export default function Index() {
  const { user } = useAuthContext();
  const [, setTick] = useState(0);
  const [showPermissionUpdate, setShowPermissionUpdate] = useState(false);

  useEffect(() => {
    const handler = () => {
      console.debug("[INDEX] Permission update detected (auth:refresh)");
      setTick((t) => t + 1);
      // Show a brief notification when permissions are updated
      setShowPermissionUpdate(true);
      setTimeout(() => setShowPermissionUpdate(false), 3000);
    };

    const userDataHandler = () => {
      console.debug("[INDEX] Permission update detected (user:data-updated)");
      setTick((t) => t + 1);
      setShowPermissionUpdate(true);
      setTimeout(() => setShowPermissionUpdate(false), 3000);
    };

    window.addEventListener("auth:refresh", handler as EventListener);
    window.addEventListener(
      "user:data-updated",
      userDataHandler as EventListener,
    );
    window.addEventListener("users:changed", handler as EventListener);

    return () => {
      window.removeEventListener("auth:refresh", handler as EventListener);
      window.removeEventListener(
        "user:data-updated",
        userDataHandler as EventListener,
      );
      window.removeEventListener("users:changed", handler as EventListener);
    };
  }, []);

  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await apiFetch("/alerts");
        if (res.ok) {
          const data = await res.json();
          if (mounted && Array.isArray(data)) setAlerts(data);
        }
      } catch (e) {
        // ignore
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const dismissed =
    typeof window !== "undefined"
      ? (JSON.parse(
          sessionStorage.getItem("dismissedAlerts") || "[]",
        ) as number[])
      : [];
  const dismiss = (id: number) => {
    try {
      const arr = JSON.parse(
        sessionStorage.getItem("dismissedAlerts") || "[]",
      ) as number[];
      if (!Array.isArray(arr)) {
        sessionStorage.setItem("dismissedAlerts", JSON.stringify([id]));
      } else {
        if (!arr.includes(id)) arr.push(id);
        sessionStorage.setItem("dismissedAlerts", JSON.stringify(arr));
      }
    } catch {
      sessionStorage.setItem("dismissedAlerts", JSON.stringify([id]));
    }
    setAlerts((cur) => cur.filter((a) => a.id !== id));
  };

  const normalize = (s: any) =>
    typeof s === "string"
      ? s
          .normalize("NFKD")
          .replace(/\p{Diacritic}/gu, "")
          .toLowerCase()
      : s;
  const slugToKey: Record<string, string> = {
    ti: "TI",
    compras: "Compras",
    manutencao: "Manutencao",
    bi: "BI",
  };
  const canAccess = (slug: string) => {
    if (!user) return false;
    if (user.nivel_acesso === "Administrador") return true;
    const required = slugToKey[slug];
    if (!required) return false;
    const req = normalize(required);
    const arr = Array.isArray(user.setores) ? user.setores.map(normalize) : [];
    return arr.some(
      (s) => s && (s === req || s.includes(req) || req.includes(s)),
    );
  };

  return (
    <Layout>
      {/* Permission update indicator */}
      {showPermissionUpdate && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-green-50 border border-green-300 rounded-lg px-4 py-3 text-sm text-green-800 shadow-md animate-in fade-in slide-in-from-top-2 duration-300">
          ✓ Suas permissões foram atualizadas!
        </div>
      )}

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-6 sm:pt-8 pb-8 sm:pb-12">
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <div className="container relative z-10">
          <div className="rounded-3xl brand-gradient px-6 sm:px-12 py-8 sm:py-12 shadow-2xl border border-white/20 backdrop-blur-sm overflow-hidden">
            {/* Decorative grid pattern */}
            <div
              className="absolute inset-0 opacity-5"
              style={{
                backgroundImage: `linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px),
                                 linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px)`,
                backgroundSize: "64px 64px",
              }}
            />

            <div className="relative z-10 text-center max-w-2xl mx-auto">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/10 backdrop-blur-md border border-white/20 rounded-full mb-3 sm:mb-4 animate-in fade-in slide-in-from-top-4 duration-500">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                <span className="text-xs sm:text-sm font-medium text-white">
                  Bem-vindo ao Portal Evoque
                </span>
              </div>

              {/* Main heading */}
              <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-primary-foreground mb-2 sm:mb-3 animate-in fade-in slide-in-from-top-6 duration-700 drop-shadow-lg">
                Portal Evoque
              </h1>

              {/* Subtitle */}
              <p className="text-sm sm:text-base text-primary-foreground/95 leading-relaxed mb-6 sm:mb-7 animate-in fade-in slide-in-from-top-8 duration-900">
                Acesse seus setores e gerencie operações em um único lugar.
              </p>

              {/* CTA Button */}
              <div className="flex items-center justify-center animate-in fade-in slide-in-from-bottom-4 duration-700">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      size="lg"
                      className="rounded-full bg-white text-primary hover:bg-white/90 shadow-lg hover:shadow-xl transition-all duration-300 font-semibold px-8 h-12"
                    >
                      Escolher portal <ChevronDown className="size-5 ml-1" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="center" className="w-48">
                    {sectors.map((s) => {
                      const allowed = canAccess(s.slug);
                      const href = user
                        ? `/setor/${s.slug}`
                        : `/auth0/login?redirect=/setor/${s.slug}`;
                      return (
                        <Link key={s.slug} to={href}>
                          <DropdownMenuItem
                            className={`cursor-pointer transition-all ${
                              !user || allowed
                                ? ""
                                : "opacity-50 pointer-events-none"
                            }`}
                          >
                            <s.icon className="w-4 h-4 mr-2" />
                            {s.title}
                          </DropdownMenuItem>
                        </Link>
                      );
                    })}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Sectors Grid Section */}
      <section id="setores" className="py-16 sm:py-24 bg-muted/30 backdrop-blur-sm">
        <div className="container">
          {/* Section Header */}
          <div className="text-center mb-12 sm:mb-16 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <h2 className="text-3xl sm:text-4xl font-bold mb-3 text-foreground">
              Nossos Setores
            </h2>
            <p className="text-muted-foreground text-base sm:text-lg max-w-2xl mx-auto">
              Explore os módulos disponíveis e gerencie todas as operações em um único lugar
            </p>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6">
            {sectors.map((s, idx) => {
              const allowed = canAccess(s.slug);
              const href = user
                ? `/setor/${s.slug}`
                : `/auth0/login?redirect=/setor/${s.slug}`;
              return (
                <Link
                  to={href}
                  key={s.slug}
                  className={`group relative animate-in fade-in slide-in-from-bottom-6 duration-700 ${
                    idx % 4 === 0 ? "delay-0" : idx % 4 === 1 ? "delay-75" : idx % 4 === 2 ? "delay-150" : "delay-200"
                  }`}
                  style={{
                    animationFillMode: "both",
                  }}
                >
                  <div
                    className={`card-surface rounded-2xl p-6 sm:p-7 transition-all duration-300 border border-border/60 hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-ring overflow-hidden relative
                    ${user && !allowed ? "opacity-50 pointer-events-none cursor-not-allowed" : "hover:shadow-lg hover:-translate-y-1 cursor-pointer"}
                    `}
                    aria-disabled={user ? String(!allowed) : undefined}
                  >
                    {/* Gradient overlay on hover */}
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                    {/* Content */}
                    <div className="relative z-10">
                      {/* Icon Container */}
                      <div className="inline-flex items-center justify-center w-12 h-12 bg-primary/10 rounded-xl mb-4 group-hover:bg-primary/20 transition-colors duration-300">
                        <s.icon className="w-6 h-6 text-primary group-hover:scale-110 transition-transform duration-300" />
                      </div>

                      {/* Text Content */}
                      <h3 className="font-bold text-lg text-foreground mb-2 group-hover:text-primary transition-colors duration-300">
                        {s.title}
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">
                        {s.description}
                      </p>

                      {/* Hover Arrow */}
                      <div className="mt-4 flex items-center text-primary opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:translate-x-1">
                        <span className="text-xs font-semibold">Acessar</span>
                        <ChevronDown className="w-4 h-4 ml-1 transform rotate-270 group-hover:translate-x-0.5 transition-transform" />
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>
    </Layout>
  );
}
