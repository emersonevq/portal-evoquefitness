import { useSearchParams, useNavigate } from "react-router-dom";
import { AlertCircle } from "lucide-react";

export default function Auth0Error() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const error = searchParams.get("error");
  const reason = searchParams.get("reason");

  const getErrorMessage = () => {
    if (error === "token_exchange_failed") {
      return {
        title: "Erro ao processar autenticação",
        message:
          "Houve um problema ao processar seu código de autenticação do Auth0. Tente fazer login novamente.",
        details:
          "Se o problema persistir, verifique se você está usando a URL correta e tente novamente em alguns momentos.",
      };
    }

    if (error?.includes("não encontrado")) {
      return {
        title: "Usuário não encontrado",
        message:
          "O email que você utilizou para fazer login não existe no banco de dados.",
        details:
          "Por favor, entre em contato com o administrador do sistema para criar sua conta.",
      };
    }

    if (reason || error) {
      return {
        title: "Erro de autenticação",
        message:
          decodeURIComponent(error || reason || "Erro desconhecido") ||
          "Houve um erro ao processar seu login.",
        details:
          "Se o problema persistir, entre em contato com o suporte técnico.",
      };
    }

    return {
      title: "Erro desconhecido",
      message: "Houve um erro ao processar sua autenticação.",
      details: "Entre em contato com o suporte técnico para assistência.",
    };
  };

  const errorInfo = getErrorMessage();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-card rounded-lg border border-border shadow-lg p-8">
          <div className="flex justify-center mb-6">
            <div className="bg-destructive/10 p-4 rounded-full">
              <AlertCircle className="w-8 h-8 text-destructive" />
            </div>
          </div>

          <h1 className="text-2xl font-bold text-center mb-4 text-card-foreground">
            {errorInfo.title}
          </h1>

          <p className="text-center text-card-foreground/90 mb-4">
            {errorInfo.message}
          </p>

          <p className="text-center text-muted-foreground text-sm mb-8">
            {errorInfo.details}
          </p>

          {error && (
            <div className="bg-muted/50 rounded p-4 mb-8 border border-border">
              <p className="text-xs text-muted-foreground font-mono break-words">
                <span className="font-semibold">Código de erro:</span>{" "}
                {error.substring(0, 100)}
                {error.length > 100 ? "..." : ""}
              </p>
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={() => navigate("/auth0/login", { replace: true })}
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90 py-2 px-4 rounded-md font-medium transition-colors"
            >
              Tentar fazer login novamente
            </button>

            <button
              onClick={() => navigate("/", { replace: true })}
              className="w-full bg-secondary text-secondary-foreground hover:bg-secondary/90 py-2 px-4 rounded-md font-medium transition-colors"
            >
              Voltar para página inicial
            </button>
          </div>

          <p className="text-center text-xs text-muted-foreground mt-6">
            Precisa de ajuda? Entre em contato com o suporte técnico.
          </p>
        </div>
      </div>
    </div>
  );
}
