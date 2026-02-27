"use client";

import { useState, type FormEvent } from "react";
import { useAuth } from "./auth-provider";
import { getCompanyName } from "@/lib/company";
import { ShieldAlert } from "lucide-react";

export function LoginScreen() {
  const { login } = useAuth();
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const companyName = getCompanyName();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!login(password)) {
      setError(true);
      setPassword("");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <ShieldAlert className="h-6 w-6 text-primary" />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-bold text-foreground">Competitive Intelligence</h1>
            <p className="mt-1 text-xs text-muted-foreground">{companyName} &mdash; Authorized Access Only</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="password" className="block text-xs font-medium text-muted-foreground mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoFocus
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError(false);
              }}
              className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Enter access password"
            />
            {error && (
              <p className="mt-1.5 text-xs text-destructive">Incorrect password. Try again.</p>
            )}
          </div>
          <button
            type="submit"
            className="inline-flex h-10 w-full items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Sign In
          </button>
        </form>

        <p className="text-center text-[10px] text-muted-foreground">
          This dashboard contains confidential competitive data.
        </p>
      </div>
    </div>
  );
}
