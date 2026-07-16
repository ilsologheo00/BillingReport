import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { RequireAuth } from "./auth/RequireAuth";
import { ThemeProvider } from "./theme/ThemeContext";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { CustomerDetailPage } from "./pages/CustomerDetailPage";
import { NinjaOneMappingPage } from "./pages/NinjaOneMappingPage";
import { AcronisMappingPage } from "./pages/AcronisMappingPage";

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <RequireAuth>
                  <DashboardPage />
                </RequireAuth>
              }
            />
            <Route
              path="/customers/:id"
              element={
                <RequireAuth>
                  <CustomerDetailPage />
                </RequireAuth>
              }
            />
            <Route
              path="/ninjaone-mapping"
              element={
                <RequireAuth>
                  <NinjaOneMappingPage />
                </RequireAuth>
              }
            />
            <Route
              path="/acronis-mapping"
              element={
                <RequireAuth>
                  <AcronisMappingPage />
                </RequireAuth>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
