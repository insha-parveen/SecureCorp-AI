"use client";

// React context for the current user. Hydrated by the login flow (the
// server-side /api/auth/me is the source of truth on reload). Components
// reach for `useCurrentUser()` rather than calling /me directly so the
// TanStack Query cache is shared.

import { createContext, useContext } from "react";
import type { User } from "./types";

interface AuthContextValue {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useCurrentUser(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useCurrentUser must be used inside <AuthProvider>");
  }
  return ctx;
}
