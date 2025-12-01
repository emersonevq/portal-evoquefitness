import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthContext } from "@/lib/auth-context";
import LoginMediaPanel from "./components/LoginMediaPanel";
import {
  Headphones,
  Shield,
  Zap,
  Clock,
  LogIn,
  AlertCircle,
} from "lucide-react";

export default function Login() {
  const navigate = useNavigate();
  const { loginWithMicrosoft } = useAuthContext();
  const [isAuth0Loading, setIsAuth0Loading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleMicrosoftLogin = async () => {
    setIsAuth0Loading(true);
    try {
      await loginWithMicrosoft();
      const redirect =
        new URLSearchParams(window.location.search).get("redirect") || "/";
      window.location.href = redirect;
    } catch (error) {
      console.error("Erro ao fazer login com Microsoft:", error);
      alert("Erro ao conectar com Microsoft. Tente novamente.");
      setIsAuth0Loading(false);
    }
  };

  return (
    <div className="relative min-h-[100svh] w-full flex items-center justify-center overflow-hidden bg-background">
      {/* Fundo com mídia */}
      <LoginMediaPanel />

      {/* Conteúdo principal */}
      <div className="relative z-10 w-full h-screen flex items-center justify-center p-6 md:p-10">
        <div
          className={`w-full max-w-[480px] transition-all duration-1000 ${
            mounted ? "opacity-100 scale-100" : "opacity-0 scale-95"
          }`}
        >
          {/* Card de Login */}
          <div className="card-surface rounded-xl p-6 sm:p-8 shadow-2xl border">
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 rounded-2xl blur-lg animate-pulse" />
                  <div className="relative">
                    <div className="absolute inset-0 bg-primary/20 rounded-2xl blur-lg animate-pulse" />
                    <div className="relative p-3.5 brand-gradient rounded-2xl shadow-lg">
                      <Headphones className="w-7 h-7 text-primary-foreground" />
                    </div>
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl font-bold tracking-tight">
                    Central de Suporte
                  </h1>
                  <p className="text-sm text-primary font-medium">
                    Sistema de Atendimento TI
                  </p>
                </div>
              </div>

              <p className="text-sm text-muted-foreground leading-relaxed">
                Acesse o portal para abrir chamados, acompanhar solicitações e
                obter suporte técnico especializado.
              </p>
            </div>

            {/* Auth0 Microsoft Login Button */}
            <Button
              onClick={handleMicrosoftLogin}
              disabled={isAuth0Loading}
              className="w-full h-11 rounded-md mb-4 bg-blue-600 hover:bg-blue-700 text-white font-medium flex items-center justify-center gap-2 group"
            >
              {isAuth0Loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Conectando...</span>
                </div>
              ) : (
                <>
                  <img
                    src="https://cdn.builder.io/api/v1/image/assets%2Faa9e931ad59b462c9cf6adb1ab6191c2%2F3403c2d4318f49d29f5d270b18089327?format=webp&width=800"
                    alt="Microsoft 365"
                    className="w-4 h-4 object-contain"
                  />
                  <span>Entrar com Microsoft Office 365</span>
                  <LogIn className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </Button>

            {/* Alerta de mudança */}
            <div className="flex gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-900 mb-1">
                  Autenticação alterada
                </p>
                <p className="text-xs text-red-800 leading-relaxed">
                  O acesso ao portal agora é realizado exclusivamente via Microsoft Office 365. Utilize seu e-mail corporativo da unidade e a senha de e-mail para fazer login.
                </p>
              </div>
            </div>

            {/* Features */}
            <div className="mt-6 pt-6 border-t">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { icon: Shield, label: "Seguro" },
                  { icon: Zap, label: "Rápido" },
                  { icon: Clock, label: "24/7" },
                ].map((item, i) => (
                  <div
                    key={i}
                    className="flex flex-col items-center gap-2 p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                  >
                    <item.icon className="w-5 h-5 text-primary" />
                    <span className="text-xs text-muted-foreground font-medium">
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="mt-6 pt-6 border-t">
              <p className="text-xs text-muted-foreground text-center">
                © {new Date().getFullYear()} Central de Suporte TI — Sistema
                interno
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
