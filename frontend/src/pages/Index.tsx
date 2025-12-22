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
      <section className="relative overflow-hidden py-3 sm:py-4">
        <div className="container relative z-10">
          <div className="rounded-2xl brand-gradient px-4 sm:px-8 py-4 sm:py-5 shadow-xl border border-white/20 backdrop-blur-sm overflow-hidden">
            <div className="relative z-10 text-center max-w-2xl mx-auto">
              {/* Main heading */}
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-primary-foreground mb-1 drop-shadow-lg">
                Portal Evoque
              </h1>

              {/* Subtitle */}
              <p className="text-xs sm:text-sm text-primary-foreground/90 mb-3">
                Acesse seus setores
              </p>

              {/* CTA Button */}
              <div className="flex items-center justify-center">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      size="sm"
                      className="rounded-full bg-white text-primary hover:bg-white/90 shadow-md hover:shadow-lg transition-all duration-300 font-semibold px-5 h-9 text-sm"
                    >
                      Escolher portal <ChevronDown className="size-4 ml-1" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="center" className="w-40">
                    {sectors.map((s) => {
                      const allowed = canAccess(s.slug);
                      const href = user
                        ? `/setor/${s.slug}`
                        : `/auth0/login?redirect=/setor/${s.slug}`;
                      return (
                        <Link key={s.slug} to={href}>
                          <DropdownMenuItem
                            className={`cursor-pointer text-sm transition-all ${
                              !user || allowed
                                ? ""
                                : "opacity-50 pointer-events-none"
                            }`}
                          >
                            <s.icon className="w-3 h-3 mr-2" />
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
      <section id="setores" className="py-4 sm:py-5 bg-muted/30 backdrop-blur-sm">
        <div className="container">
          {/* Section Header */}
          <div className="text-center mb-4 sm:mb-5">
            <h2 className="text-lg sm:text-xl font-bold mb-1 text-foreground">
              Nossos Setores
            </h2>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {sectors.map((s, idx) => {
              const allowed = canAccess(s.slug);
              const href = user
                ? `/setor/${s.slug}`
                : `/auth0/login?redirect=/setor/${s.slug}`;
              return (
                <Link
                  to={href}
                  key={s.slug}
                  className={`group relative ${
                    user && !allowed ? "opacity-50 pointer-events-none cursor-not-allowed" : "cursor-pointer"
                  }`}
                >
                  <div
                    className={`card-surface rounded-xl p-3 sm:p-4 transition-all duration-300 border border-border/60 hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-ring overflow-hidden relative hover:shadow-md hover:-translate-y-0.5`}
                    aria-disabled={user ? String(!allowed) : undefined}
                  >
                    {/* Content */}
                    <div className="relative z-10">
                      {/* Icon Container */}
                      <div className="inline-flex items-center justify-center w-9 h-9 bg-primary/10 rounded-lg mb-2 group-hover:bg-primary/20 transition-colors duration-300">
                        <s.icon className="w-5 h-5 text-primary" />
                      </div>

                      {/* Text Content */}
                      <h3 className="font-semibold text-sm text-foreground mb-1 group-hover:text-primary transition-colors duration-300">
                        {s.title}
                      </h3>
                      <p className="text-xs text-muted-foreground leading-relaxed line-clamp-1">
                        {s.description}
                      </p>
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
