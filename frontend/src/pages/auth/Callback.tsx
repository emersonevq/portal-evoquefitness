import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuthContext } from "@/lib/auth-context";

export default function Callback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isLoading } = useAuthContext();

  useEffect(() => {
    // Get redirect URL from query param or default to home
    const redirect = searchParams.get("redirect") || "/";

    // Wait for auth to be ready, then redirect
    if (!isLoading) {
      const timer = setTimeout(() => {
        navigate(redirect, { replace: true });
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [isLoading, navigate, searchParams]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-muted-foreground font-medium">Autenticando...</p>
        <p className="text-xs text-muted-foreground mt-2">Aguarde enquanto redirecionamos você</p>
      </div>
    </div>
  );
}
