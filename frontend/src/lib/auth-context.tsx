import {
  createContext,
  useContext,
  ReactNode,
  useEffect,
  useState,
} from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

interface User {
  id?: number;
  email: string;
  name: string;
  firstName?: string;
  lastName?: string;
  nivel_acesso?: string;
  setores?: string[];
  bi_subcategories?: string[] | null;
  loginTime: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email?: string, password?: string) => Promise<any>;
  logout: () => void;
  loginWithAuth0: () => Promise<void>;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper function: determina para onde redirecionar baseado no nível de acesso
function getAutoRedirectUrl(user: User): string | null {
  if (!user.nivel_acesso) return null;

  const accessLevel = user.nivel_acesso.toLowerCase();

  // Administradores vão para o painel administrativo
  if (accessLevel === "administrador") {
    return "/setor/ti/admin";
  }

  // Agentes vão para a página de chamados
  if (accessLevel.includes("agente")) {
    return "/setor/ti";
  }

  // Usuários comuns vão para a página inicial dos setores
  if (user.setores && user.setores.length > 0) {
    const firstSector = user.setores[0].toLowerCase();
    return `/setor/${firstSector}`;
  }

  // Fallback: página principal
  return "/";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Initialize Auth0 on mount
  useEffect(() => {
    const initAuth0 = async () => {
      try {
        // Check if returning from Auth0 callback
        const code = searchParams.get("code");
        const state = searchParams.get("state");

        if (code && state) {
          // Handle Auth0 redirect - exchange code for token
          await handleAuth0Callback(code, state);
        } else {
          // Check for existing session
          await checkExistingSession();
        }
      } catch (error) {
        console.error("Error initializing auth:", error);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth0();
  }, [searchParams]);

  const handleAuth0Callback = async (code: string, state: string) => {
    try {
      // Exchange code for token with Auth0
      const response = await fetch(
        "https://" + import.meta.env.VITE_AUTH0_DOMAIN + "/oauth/token",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            client_id: import.meta.env.VITE_AUTH0_CLIENT_ID,
            client_secret: import.meta.env.VITE_AUTH0_CLIENT_SECRET,
            code: code,
            grant_type: "authorization_code",
            redirect_uri: import.meta.env.VITE_AUTH0_REDIRECT_URI,
            state: state,
          }),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to exchange code for token");
      }

      const data = await response.json();
      const accessToken = data.access_token;

      // Store token
      localStorage.setItem("auth0_access_token", accessToken);

      // Validate token with backend e obter dados do usuário
      const userData = await validateAndSyncUser(accessToken);

      // Get redirect URL - usar a que foi armazenada ou gerar automática
      let redirectUrl = sessionStorage.getItem("auth0_redirect_after_login");
      if (!redirectUrl && userData) {
        // Se não houver redirecionamento armazenado, usar o automático baseado no nível de acesso
        redirectUrl = getAutoRedirectUrl(userData) || "/";
      }
      redirectUrl = redirectUrl || "/";

      sessionStorage.removeItem("auth0_redirect_after_login");

      navigate(redirectUrl, { replace: true });
    } catch (error) {
      console.error("Error handling Auth0 callback:", error);
      throw error;
    }
  };

  const checkExistingSession = async () => {
    try {
      const token = localStorage.getItem("auth0_access_token");
      if (!token) {
        setUser(null);
        return;
      }

      // Validate token with backend
      await validateAndSyncUser(token);
    } catch (error) {
      console.error("Error checking session:", error);
      localStorage.removeItem("auth0_access_token");
      setUser(null);
    }
  };

  const validateAndSyncUser = async (accessToken: string): Promise<User | null> => {
    try {
      // Call backend to validate token and get user data
      const response = await fetch("/api/auth/auth0-login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ token: accessToken }),
      });

      if (!response.ok) {
        if (response.status === 403) {
          console.error("User not authorized");
        } else {
          console.error("Error validating with backend:", response.status);
        }
        throw new Error("Validation failed");
      }

      const data = await response.json();
      const now = Date.now();

      const userData: User = {
        id: data.id,
        email: data.email,
        name: `${data.nome} ${data.sobrenome}`,
        firstName: data.nome,
        lastName: data.sobrenome,
        nivel_acesso: data.nivel_acesso,
        setores: Array.isArray(data.setores) ? data.setores : [],
        bi_subcategories: Array.isArray(data.bi_subcategories)
          ? data.bi_subcategories
          : null,
        loginTime: now,
      };

      setUser(userData);

      // Store in sessionStorage
      sessionStorage.setItem("evoque-fitness-auth", JSON.stringify(userData));

      // Determinar redirecionamento automático baseado no nível de acesso
      const autoRedirect = getAutoRedirectUrl(userData);
      if (autoRedirect) {
        sessionStorage.setItem("auth0_redirect_after_login", autoRedirect);
      }

      return userData;
    } catch (error) {
      console.error("Error syncing user:", error);
      throw error;
    }
  };

  // Traditional email/password login (if needed)
  const login = async (email?: string, password?: string) => {
    try {
      if (!email || !password) {
        throw new Error("Email and password are required");
      }

      const response = await fetch("/api/usuarios/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, senha: password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Authentication failed");
      }

      const data = await response.json();
      const now = Date.now();

      const userData: User = {
        id: data.id,
        email: data.email,
        name: `${data.nome} ${data.sobrenome}`,
        firstName: data.nome,
        lastName: data.sobrenome,
        nivel_acesso: data.nivel_acesso,
        setores: Array.isArray(data.setores) ? data.setores : [],
        bi_subcategories: Array.isArray(data.bi_subcategories)
          ? data.bi_subcategories
          : null,
        loginTime: now,
      };

      setUser(userData);
      sessionStorage.setItem("evoque-fitness-auth", JSON.stringify(userData));

      return {
        ...data,
        alterar_senha_primeiro_acesso:
          data.alterar_senha_primeiro_acesso || false,
      };
    } catch (error: any) {
      throw new Error(error?.message || "Authentication failed");
    }
  };

  // Login with Auth0
  const loginWithAuth0 = async () => {
    try {
      // Get redirect URL from current location
      const redirect =
        new URLSearchParams(window.location.search).get("redirect") || "/";
      sessionStorage.setItem("auth0_redirect_after_login", redirect);

      // Build Auth0 login URL
      const authorizationUrl = new URL(
        `https://${import.meta.env.VITE_AUTH0_DOMAIN}/authorize`,
      );

      const params = {
        response_type: "code",
        client_id: import.meta.env.VITE_AUTH0_CLIENT_ID,
        redirect_uri: import.meta.env.VITE_AUTH0_REDIRECT_URI,
        scope: "openid profile email offline_access",
        audience: import.meta.env.VITE_AUTH0_AUDIENCE,
        state: Math.random().toString(36).substring(7), // Simple state for demo
      };

      Object.entries(params).forEach(([key, value]) => {
        authorizationUrl.searchParams.append(key, value);
      });

      // Redirect to Auth0
      window.location.href = authorizationUrl.toString();
    } catch (error) {
      console.error("Error logging in with Auth0:", error);
      throw error;
    }
  };

  // Logout
  const logout = async () => {
    try {
      // Clear local storage
      localStorage.removeItem("auth0_access_token");
      sessionStorage.removeItem("evoque-fitness-auth");
      sessionStorage.removeItem("auth0_redirect_after_login");

      setUser(null);

      // Redirect to Auth0 logout
      const logoutUrl = new URL(
        `https://${import.meta.env.VITE_AUTH0_DOMAIN}/v2/logout`,
      );
      logoutUrl.searchParams.append(
        "returnTo",
        import.meta.env.VITE_AUTH0_LOGOUT_URI || window.location.origin,
      );
      logoutUrl.searchParams.append(
        "client_id",
        import.meta.env.VITE_AUTH0_CLIENT_ID,
      );

      window.location.href = logoutUrl.toString();
    } catch (error) {
      console.error("Error logging out:", error);
      setUser(null);
      window.location.href = "/";
    }
  };

  const getAccessToken = () => {
    return localStorage.getItem("auth0_access_token");
  };

  const contextValue: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    loginWithAuth0,
    getAccessToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}
