import type { ReactNode } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useMe } from "./features/auth/useAuth";
import SignupPage from "./pages/SignupPage";
import LoginPage from "./pages/LoginPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import Verify2FAPage from "./pages/Verify2FAPage";
import WorkspacesPage from "./pages/WorkspacesPage";
import BoardPage from "./pages/BoardPage";

function RequireAuth({ children }: { children: ReactNode }) {
  const { data: me, isLoading } = useMe();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading...</div>
    );
  }
  if (!me) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/verify-2fa" element={<Verify2FAPage />} />

      <Route
        path="/workspaces"
        element={
          <RequireAuth>
            <WorkspacesPage />
          </RequireAuth>
        }
      />
      <Route
        path="/boards/:boardId"
        element={
          <RequireAuth>
            <BoardPage />
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to="/workspaces" replace />} />
    </Routes>
  );
}
