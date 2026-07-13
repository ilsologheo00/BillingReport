import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { login as apiLogin } from "../api/auth";

interface AuthContextValue {
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      login: async (username: string, password: string) => {
        const accessToken = await apiLogin(username, password);
        localStorage.setItem("token", accessToken);
        setToken(accessToken);
      },
      logout: () => {
        localStorage.removeItem("token");
        setToken(null);
      },
    }),
    [token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
