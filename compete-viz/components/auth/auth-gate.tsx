"use client";

import { type ReactNode } from "react";
import { AuthProvider, useAuth } from "./auth-provider";
import { LoginScreen } from "./login-screen";

function Gate({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <LoginScreen />;
  return <>{children}</>;
}

export function AuthGate({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <Gate>{children}</Gate>
    </AuthProvider>
  );
}
