import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuthContext } from "@/lib/auth-context";
import { AlertCircle } from "lucide-react";

export default function Callback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isLoading, authError } = useAuthContext();
  const [showError, setShowError] = useState(false);

  useEffect(() => {
    // If there's an auth error, show it briefly then redirect to error page
    if (authError) {
      setShowError(true);
      const timer = setTimeout(() => {
        navigate("/auth0/error?error=" + encodeURIComponent(authError), {
          replace: true,
        });
      }, 2000);
      return () => clearTimeout(timer);
    }

    // Get redirect URL from query param or default to home
    const redirect = searchParams.get("redirect") || "/";

    // Wait for auth to be ready, then redirect
    if (!isLoading) {
      const timer = setTimeout(() => {
        navigate(redirect, { replace: true });
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [isLoading, authError, navigate, searchParams]);

  if (showError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center max-w-sm">
          <div className="bg-destructive/10 p-4 rounded-full inline-flex mb-4">
            <AlertCircle className="w-8 h-8 text-destructive" />
          </div>
          <p className="text-lg font-semibold text-foreground mb-2">
            Erro na autenticação
          </p>
          <p className="text-sm text-muted-foreground mb-4">{authError}</p>
          <p className="text-xs text-muted-foreground">
            Redirecionando para página de erro...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-muted-foreground font-medium">Autenticando...</p>
        <p className="text-xs text-muted-foreground mt-2">
          Aguarde enquanto redirecionamos você
        </p>
      </div>
    </div>
  );
}
