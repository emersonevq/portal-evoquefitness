import { useEffect } from "react";
import { useAuthContext } from "@/lib/auth-context";

export default function Callback() {
  const { isLoading, isAuthenticated } = useAuthContext();

  useEffect(() => {
    console.log("[CALLBACK] isLoading:", isLoading);
    console.log("[CALLBACK] isAuthenticated:", isAuthenticated);
  }, [isLoading, isAuthenticated]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-muted-foreground font-medium">
          {isLoading ? "Autenticando..." : "Redirecionando..."}
        </p>
        <p className="text-xs text-muted-foreground mt-2">
          Aguarde enquanto processamos seu login
        </p>
      </div>
    </div>
  );
}